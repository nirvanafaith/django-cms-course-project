"""只读 Admin 系统日志视图测试。"""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core.tests.test_log_reader import write_events


class SystemLogViewTests(TestCase):
    """验证超级用户权限、过滤与分页。"""

    def setUp(self) -> None:
        self.admin = User.objects.create_superuser("log-admin", password="password")
        self.normal = User.objects.create_user("reader", password="password")

    def test_normal_user_cannot_open_system_logs(self) -> None:
        """普通用户被 Admin 权限边界拒绝。"""
        self.client.force_login(self.normal)

        response = self.client.get(reverse("admin_system_logs"))

        self.assertEqual(response.status_code, 302)

    def test_superuser_can_filter_every_supported_field(self) -> None:
        """日期、级别、事件、状态和请求 ID 均参与过滤。"""
        with TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            write_events(
                log_dir / "cms.jsonl",
                [
                    {
                        "timestamp": "2026-08-14T10:00:00+00:00",
                        "level": "ERROR",
                        "event": "request.failed",
                        "status": 500,
                        "request_id": "target-request",
                    },
                    {
                        "timestamp": "2026-08-13T10:00:00+00:00",
                        "level": "INFO",
                        "event": "request.complete",
                        "status": 200,
                        "request_id": "other-request",
                    },
                ],
            )
            self.client.force_login(self.admin)

            with override_settings(LOG_DIR=log_dir):
                response = self.client.get(
                    reverse("admin_system_logs"),
                    {
                        "date": "2026-08-14",
                        "level": "ERROR",
                        "event": "request.failed",
                        "status": "500",
                        "request_id": "target-request",
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "target-request")
        self.assertNotContains(response, "other-request")

    def test_paginates_fifty_events_and_preserves_filters(self) -> None:
        """第二页显示余下记录且翻页链接保留过滤条件。"""
        with TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            write_events(
                log_dir / "cms.jsonl",
                [
                    {
                        "timestamp": f"2026-08-14T10:{index:02}:00+00:00",
                        "level": "INFO",
                        "request_id": f"request-{index:02}",
                    }
                    for index in range(55)
                ],
            )
            self.client.force_login(self.admin)

            with override_settings(LOG_DIR=log_dir):
                response = self.client.get(
                    reverse("admin_system_logs"), {"level": "INFO", "page": "2"}
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["events"]), 5)
        self.assertContains(response, "level=INFO")

    def test_missing_log_file_renders_empty_state_and_admin_link(self) -> None:
        """无日志时显示空状态，Admin 导航保留系统日志入口。"""
        with TemporaryDirectory() as temporary:
            self.client.force_login(self.admin)

            with override_settings(LOG_DIR=Path(temporary)):
                response = self.client.get(reverse("admin_system_logs"))
            index_response = self.client.get(reverse("admin:index"))

        self.assertContains(response, "暂无符合条件的日志")
        self.assertContains(response, 'class="module system-log-table-scroll"')
        self.assertContains(index_response, "系统日志")
