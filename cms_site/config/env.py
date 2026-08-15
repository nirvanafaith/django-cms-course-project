"""集中解析运行环境变量。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Final

MODE_LOCAL: Final = "local"
MODE_PUBLIC: Final = "public"
VALID_MODES: Final = frozenset({MODE_LOCAL, MODE_PUBLIC})


class ConfigError(RuntimeError):
    """运行配置缺失或非法。"""


@dataclass(frozen=True, slots=True)
class IntegerSetting:
    """一个整数环境变量允许的默认值与闭区间。"""

    default: int
    minimum: int
    maximum: int


def get_mode() -> str:
    """读取并校验 Django 运行模式。"""
    mode = os.environ.get("DJANGO_MODE", MODE_LOCAL)
    if mode not in VALID_MODES:
        raise ConfigError(f"DJANGO_MODE 仅支持 local 或 public，当前值为 {mode!r}")
    return mode


def is_test_mode() -> bool:
    """判断当前进程是否显式运行测试。"""
    return "test" in sys.argv or os.environ.get("DJANGO_TEST") == "1"


def parse_bool(value: str | None, *, default: bool = False) -> bool:
    """把常见环境变量布尔文本解析为布尔值。"""
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_int(name: str, value: str | None, setting: IntegerSetting) -> int:
    """把环境变量解析为指定闭区间内的整数。"""
    raw = str(setting.default) if value is None else value
    try:
        parsed = int(raw)
    except ValueError as error:
        raise ConfigError(f"{name} 必须是整数") from error
    if not setting.minimum <= parsed <= setting.maximum:
        raise ConfigError(f"{name} 必须介于 {setting.minimum} 和 {setting.maximum} 之间")
    return parsed


def split_csv(value: str | None) -> list[str]:
    """解析逗号分隔配置并丢弃空项。"""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def require_env(name: str) -> str:
    """读取必填变量，错误信息只包含变量名。"""
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"缺少必需的配置变量：{name}")
    return value
