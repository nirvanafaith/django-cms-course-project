#!/usr/bin/env python
"""Django 命令行入口。

``sys.argv`` 保存用户输入的命令，例如 ``migrate``、``test`` 或 ``runserver``；
``execute_from_command_line`` 再把它交给 Django 的命令分发系统。
"""

import os
import sys


def main():
    """设置项目配置模块并执行用户指定的 Django 管理命令。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
