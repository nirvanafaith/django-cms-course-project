"""有界读取当前与轮转 JSONL 日志。"""

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Final

type LogValue = str | int | float | bool | None
type LogEvent = dict[str, LogValue]

ALLOWED_FIELDS: Final = frozenset(
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
    }
)
ROTATED_LOG_NAME: Final = re.compile(r"cms\.jsonl\.\d{4}-\d{2}-\d{2}")
READ_BLOCK_SIZE: Final = 8192


def _newest_lines(path: Path) -> Iterator[str]:
    """从文件末尾按行读取，避免为上限较小的页面加载整个文件。"""
    with path.open("rb") as stream:
        stream.seek(0, 2)
        position = stream.tell()
        pending = b""
        while position > 0:
            block_size = min(READ_BLOCK_SIZE, position)
            position -= block_size
            stream.seek(position)
            pending = stream.read(block_size) + pending
            lines = pending.split(b"\n")
            pending = lines[0]
            for line in reversed(lines[1:]):
                if line:
                    try:
                        yield line.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
        if pending:
            try:
                yield pending.decode("utf-8")
            except UnicodeDecodeError:
                return


def _parse_event(line: str) -> LogEvent | None:
    """把一行不可信 JSON 解析为字段和值均受限的事件。"""
    try:
        decoded = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(decoded, dict):
        return None
    event: LogEvent = {}
    for key in ALLOWED_FIELDS:
        value = decoded.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            event[key] = value
    return event


def read_log_events(log_dir: Path, *, limit: int = 5000) -> list[LogEvent]:
    """返回当前与合法轮转文件中的最新事件，最多读取 ``limit`` 条。"""
    if not log_dir.is_dir() or limit <= 0:
        return []
    current = log_dir / "cms.jsonl"
    rotated = sorted(
        (
            path
            for path in log_dir.iterdir()
            if path.is_file() and ROTATED_LOG_NAME.fullmatch(path.name)
        ),
        reverse=True,
    )
    paths = ([current] if current.is_file() else []) + rotated
    events: list[LogEvent] = []
    for path in paths:
        for line in _newest_lines(path):
            event = _parse_event(line)
            if event is not None:
                events.append(event)
                if len(events) == limit:
                    return events
    return events
