"""结构化日志格式与网络地址脱敏。"""

import ipaddress
import json
import logging
from datetime import UTC, datetime
from typing import Final

EVENT_FIELDS: Final = (
    "request_id",
    "method",
    "path",
    "status",
    "duration_ms",
    "user_id",
    "masked_ip",
)


def mask_ip(address: str) -> str:
    """保留网络前缀并移除可识别主机信息。"""
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return "unknown"
    if parsed.version == 4:
        return str(ipaddress.ip_network(f"{parsed}/24", strict=False).network_address)
    return str(ipaddress.ip_network(f"{parsed}/64", strict=False).network_address)


class JsonFormatter(logging.Formatter):
    """将固定白名单 LogRecord 字段序列化为单行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, str | int | float | None] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for field in EVENT_FIELDS:
            if field in record.__dict__:
                payload[field] = record.__dict__[field]
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
