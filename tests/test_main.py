from pathlib import Path

from pdf_checker.__main__ import parse_args, run

ROOT = Path(__file__).parent.parent


def run_with(argv, answers):
    replies = iter(answers)
    printed = []
    code = run(parse_args(argv), input_fn=lambda _: next(replies), print_fn=printed.append)
    return code, "\n".join(printed)


def test_full_dialog_creates_pdf(tmp_path):
    code, out = run_with(
        [
            "--data-dir",
            str(ROOT / "data"),
            "--templates-dir",
            str(ROOT / "templates"),
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ],
        ["1", "2", "2"],  # invoices.csv, receipt.html, второй чек
    )
    assert code == 0
    assert "Файлы с данными" in out and "HTML-шаблоны" in out
    pdf = tmp_path / "INV-1002_receipt.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")


def test_broken_file_is_listed_and_not_offered(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "broken.json").write_text("[{", encoding="utf-8")
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "t.html").write_text("x", encoding="utf-8")

    code, out = run_with(["--data-dir", str(data), "--templates-dir", str(templates)], [])
    assert code == 1
    assert "пропущен broken.json" in out
    assert "нет пригодных файлов" in out
