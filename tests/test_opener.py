from pathlib import Path

import pytest

from pdf_checker.opener import open_file

PDF = Path("/tmp/x.pdf")


def test_macos_uses_open():
    calls = []
    open_file(PDF, platform="darwin", run=lambda cmd, check: calls.append(cmd))
    assert calls == [["open", str(PDF)]]


def test_linux_uses_xdg_open():
    calls = []
    open_file(PDF, platform="linux", run=lambda cmd, check: calls.append(cmd))
    assert calls == [["xdg-open", str(PDF)]]


def test_windows_uses_startfile():
    calls = []
    open_file(PDF, platform="win32", startfile=calls.append)
    assert calls == [str(PDF)]


def test_windows_without_startfile_fails_loudly():
    with pytest.raises(OSError):
        open_file(PDF, platform="win32", startfile=None)
