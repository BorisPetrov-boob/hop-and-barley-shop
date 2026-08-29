#!/usr/bin/env python
"""Точка входа для административных команд Django."""
from __future__ import annotations

import os
import sys


def main() -> None:
    """Запустить задачу управления Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что он установлен и "
            "доступен в PYTHONPATH, а виртуальное окружение активировано."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
