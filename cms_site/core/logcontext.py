"""请求日志关联标识的线程本地上下文。"""

from __future__ import annotations

import logging
import threading

_local = threading.local()


def set_request_id(request_id: str) -> None:
    """设置当前线程请求标识。"""
    _local.request_id = request_id


def get_request_id() -> str:
    """读取当前线程请求标识。"""
    return getattr(_local, "request_id", "-")


def clear_request_id() -> None:
    """清除当前线程请求标识。"""
    _local.request_id = "-"


class RequestIdFilter(logging.Filter):
    """向日志记录注入请求标识。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
