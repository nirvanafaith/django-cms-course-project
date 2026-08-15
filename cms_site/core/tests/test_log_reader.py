"""有界 JSONL 日志读取器测试。"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core.log_reader import read_log_events


def write_events(path: Path, events: list[dict[str, str | int]]) -> None:
    """写入测试使用的 UTF-8 JSONL。"""
    path.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )


class LogReaderTests(SimpleTestCase):
    """验证读取范围、顺序、容错和上限。"""

    def test_reads_current_and_rotated_files_newest_first(self) -> None:
        """当前文件优先，单个文件内从最新事件开始读取。"""
        with TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            write_events(
                log_dir / "cms.jsonl.2026-08-13",
                [
                    {"timestamp": "2026-08-13T09:00:00+00:00", "request_id": "1"},
                    {"timestamp": "2026-08-13T10:00:00+00:00", "request_id": "2"},
                ],
            )
            (log_dir / "cms.jsonl.2026-08-14").write_text("malformed\n", encoding="utf-8")
            write_events(
                log_dir / "cms.jsonl",
                [
                    {"timestamp": "2026-08-14T09:00:00+00:00", "request_id": "3"},
                    {"timestamp": "2026-08-14T10:00:00+00:00", "request_id": "4"},
                ],
            )

            events = read_log_events(log_dir)

        self.assertEqual([event["request_id"] for event in events], ["4", "3", "2", "1"])

    def test_caps_results_at_five_thousand(self) -> None:
        """超大日志最多返回最近五千条。"""
        with TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            write_events(
                log_dir / "cms.jsonl",
                [
                    {
                        "timestamp": (f"2026-08-14T10:{index // 60:02}:{index % 60:02}+00:00"),
                        "status": index,
                    }
                    for index in range(5002)
                ],
            )

            events = read_log_events(log_dir)

        self.assertEqual(len(events), 5000)
        self.assertEqual(events[0]["status"], 5001)

    def test_missing_directory_returns_empty_list(self) -> None:
        """日志目录不存在时显示空状态而不报错。"""
        with TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"

            events = read_log_events(missing)

        self.assertEqual(events, [])
