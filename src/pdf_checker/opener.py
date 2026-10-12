"""Открытие файла программой, назначенной в системе."""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# os.startfile существует только в Windows.
_STARTFILE: Callable[[str], None] | None = getattr(os, "startfile", None)


def open_file(
    path: Path,
    platform: str = sys.platform,
    run: Callable[..., object] = subprocess.run,
    startfile: Callable[[str], None] | None = _STARTFILE,
) -> None:
    if platform == "win32":
        if startfile is None:
            raise OSError("os.startfile недоступен")
        startfile(str(path))
    elif platform == "darwin":
        run(["open", str(path)], check=True)
    else:
        run(["xdg-open", str(path)], check=True)
