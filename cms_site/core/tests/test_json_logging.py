"""结构化日志、脱敏与请求边界测试。"""

import json
import logging
from unittest.mock import MagicMock

from django.conf import settings
from django.contrib.auth.models import User
from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.utils.functional import SimpleLazyObject

from core.json_logging import JsonFormatter, mask_ip
from core.middleware import AdminLoginThrottleMiddleware, RequestContextMiddleware
from core.throttling import RateLimitResult


class IpMaskingTests(SimpleTestCase):
    """验证日志只保留排障所需的网络前缀。"""

    def test_masks_ipv4_host_part(self) -> None:
        """IPv4 最后一段归零。"""
        self.assertEqual(mask_ip("203.0.113.42"), "203.0.113.0")

    def test_masks_ipv6_after_four_hextets(self) -> None:
        """IPv6 只保留前 64 位。"""
        self.assertEqual(
            mask_ip("2001:db8:abcd:1234:5678:9abc:def0:1234"),
            "2001:db8:abcd:1234::",
        )

    def test_replaces_invalid_address(self) -> None:
        """无效地址不会原样进入日志。"""
        self.assertEqual(mask_ip("not-an-address"), "unknown")


class JsonFormatterTests(SimpleTestCase):
    """验证 JSONL 仅输出固定白名单字段。"""

    def test_serializes_allowlisted_fields_only(self) -> None:
        """查询、Cookie、口令和认证头即使存在于记录中也被丢弃。"""
        record = logging.makeLogRecord(
            {
                "name": "cms.request",
                "levelno": logging.INFO,
                "levelname": "INFO",
                "msg": "request.complete",
                "request_id": "request-123",
                "method": "GET",
                "path": "/list/",
                "status": 200,
                "duration_ms": 12.5,
                "user_id": 7,
                "masked_ip": "203.0.113.0",
                "query_string": "password=secret",
                "cookies": "sessionid=secret",
                "password": "secret",
                "authorization": "Bearer secret",
            }
        )

        payload = json.loads(JsonFormatter().format(record))

        self.assertEqual(
            set(payload),
            {
                "timestamp",
                "level",
                "logger",
                "event",
                "request_id",
                "method",
                "path",
                "status",
                "duration_ms",
                "user_id",
                "masked_ip",
            },
        )
        self.assertEqual(payload["event"], "request.complete")
        self.assertNotIn("secret", json.dumps(payload, ensure_ascii=False))


class RequestLoggingTests(SimpleTestCase):
    """验证一次完成请求产生可关联且脱敏的事件。"""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_completed_request_has_required_context(self) -> None:
        """请求事件包含状态、耗时、请求 ID、用户和脱敏地址。"""
        request = self.factory.get(
            "/list/?password=secret",
            REMOTE_ADDR="203.0.113.42",
            HTTP_AUTHORIZATION="Bearer secret",
            HTTP_COOKIE="sessionid=secret",
        )
        request.user = User(pk=42, username="reader")
        middleware = RequestContextMiddleware(lambda _request: HttpResponse("ok"))

        with self.assertLogs("cms.request", level="INFO") as captured:
            response = middleware(request)

        record = captured.records[0]
        self.assertEqual(record.getMessage(), "request.complete")
        self.assertEqual(record.__dict__["method"], "GET")
        self.assertEqual(record.__dict__["path"], "/list/")
        self.assertEqual(record.__dict__["status"], 200)
        self.assertGreaterEqual(record.__dict__["duration_ms"], 0)
        self.assertEqual(record.__dict__["user_id"], 42)
        self.assertEqual(record.__dict__["masked_ip"], "203.0.113.0")
        self.assertEqual(record.__dict__["request_id"], response["X-Request-ID"])
        self.assertFalse(hasattr(record, "query_string"))

    def test_error_response_avoids_resolving_unavailable_session_user(self) -> None:
        """Given 503 响应，When 会话数据库不可用，Then 日志中间件保留该响应。"""
        request = self.factory.get("/health/ready/", REMOTE_ADDR="203.0.113.42")
        request.__dict__["user"] = SimpleLazyObject(
            MagicMock(side_effect=OperationalError("db unavailable"))
        )
        middleware = RequestContextMiddleware(
            lambda _request: HttpResponse("unavailable", status=503)
        )

        with self.assertLogs("cms.request", level="INFO") as captured:
            response = middleware(request)

        self.assertEqual(response.status_code, 503)
        self.assertIsNone(captured.records[0].__dict__["user_id"])


class LoginSecurityLoggingTests(SimpleTestCase):
    """验证两个登录入口共享限流与安全事件。"""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_public_login_failure_is_recorded(self) -> None:
        """公开登录失败进入同一限流器并产生脱敏事件。"""
        request = self.factory.post(
            "/accounts/login/",
            {"username": "reader", "password": "secret"},
            REMOTE_ADDR="203.0.113.42",
        )
        middleware = AdminLoginThrottleMiddleware(lambda _request: HttpResponse("invalid"))
        middleware.throttle = MagicMock()
        middleware.throttle.check.return_value = RateLimitResult(True, 0)

        with self.assertLogs("cms.security", level="WARNING") as captured:
            response = middleware(request)

        self.assertEqual(response.status_code, 200)
        middleware.throttle.record_failure.assert_called_once_with("reader", "203.0.113.42")
        record = captured.records[0]
        self.assertEqual(record.getMessage(), "login.failed")
        self.assertEqual(record.__dict__["path"], "/accounts/login/")
        self.assertEqual(record.__dict__["masked_ip"], "203.0.113.0")

    def test_admin_login_block_is_recorded(self) -> None:
        """Admin 登录封禁返回 429 并产生安全事件。"""
        request = self.factory.post(
            "/admin/login/",
            {"username": "admin", "password": "secret"},
            REMOTE_ADDR="2001:db8:abcd:1234::9",
        )
        middleware = AdminLoginThrottleMiddleware(lambda _request: HttpResponse("unused"))
        middleware.throttle = MagicMock()
        middleware.throttle.check.return_value = RateLimitResult(False, 60)

        with self.assertLogs("cms.security", level="WARNING") as captured:
            response = middleware(request)

        self.assertEqual(response.status_code, 429)
        record = captured.records[0]
        self.assertEqual(record.getMessage(), "login.blocked")
        self.assertEqual(record.__dict__["masked_ip"], "2001:db8:abcd:1234::")


class LoggingSettingsTests(SimpleTestCase):
    """验证文件输出与保留周期配置。"""

    def test_uses_utf8_daily_rotation_with_fourteen_backups(self) -> None:
        """日志文件按本地午夜轮转并保留十四份。"""
        handler = settings.LOGGING["handlers"]["json_file"]

        self.assertEqual(handler["class"], "logging.handlers.TimedRotatingFileHandler")
        self.assertEqual(handler["filename"], settings.LOG_FILE)
        self.assertEqual(handler["when"], "midnight")
        self.assertEqual(handler["backupCount"], 14)
        self.assertEqual(handler["encoding"], "utf-8")
        self.assertFalse(handler["utc"])
        self.assertTrue(handler["delay"])
