"""Точка входа: разбор аргументов, сборка частей, диалог с пользователем."""

import argparse
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import jinja2

from pdf_checker.domain import Invoice
from pdf_checker.loaders import DataFileError, discover, load_invoices
from pdf_checker.menu import ask_index, choose, format_menu
from pdf_checker.opener import open_file
from pdf_checker.render import money, pdf_path, render_html, write_pdf

DATA_SUFFIXES = {".csv", ".json"}
TEMPLATE_SUFFIXES = {".html", ".htm"}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-checker", description="PDF-чек из CSV/JSON по HTML-шаблону"
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--templates-dir", type=Path, default=Path("templates"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--no-open", action="store_true", help="не открывать PDF после создания")
    return parser.parse_args(argv)


def load_all(paths: list[Path]) -> tuple[list[tuple[Path, list[Invoice]]], list[tuple[Path, str]]]:
    loaded, broken = [], []
    for path in paths:
        try:
            invoices = load_invoices(path)
        except (DataFileError, OSError, UnicodeDecodeError) as e:
            broken.append((path, str(e)))
            continue
        if invoices:
            loaded.append((path, invoices))
        else:
            broken.append((path, "нет ни одного чека"))
    return loaded, broken


def invoice_line(invoice: Invoice) -> str:
    return f"{invoice.invoice_id}  {invoice.date}  {invoice.customer}  {money(invoice.total)} ₽"


def run(
    args: argparse.Namespace,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> int:
    loaded, broken = load_all(discover(args.data_dir, DATA_SUFFIXES))
    templates = discover(args.templates_dir, TEMPLATE_SUFFIXES)

    if loaded:
        print_fn(
            format_menu(
                f"Файлы с данными ({args.data_dir})",
                [f"{path.name}  — чеков: {len(invoices)}" for path, invoices in loaded],
            )
        )
    else:
        print_fn(f"В {args.data_dir.resolve()} нет пригодных файлов CSV или JSON.")
    for path, reason in broken:
        print_fn(f"  пропущен {path.name}: {reason}")
    print_fn("")
    if templates:
        print_fn(format_menu(f"HTML-шаблоны ({args.templates_dir})", [p.name for p in templates]))
    else:
        print_fn(f"В {args.templates_dir.resolve()} нет HTML-шаблонов.")
    if not loaded or not templates:
        return 1

    print_fn("")
    data_path, invoices = loaded[ask_index(len(loaded), "Файл с данными", input_fn, print_fn)]
    template = templates[ask_index(len(templates), "Шаблон", input_fn, print_fn)]
    invoice = invoices[
        choose(f"Чеки в {data_path.name}", [invoice_line(i) for i in invoices], input_fn, print_fn)
    ]

    try:
        html = render_html(
            template, invoice, generated_at=datetime.now().strftime("%d.%m.%Y %H:%M")
        )
    except jinja2.TemplateError as e:
        print_fn(f"Ошибка в шаблоне {template.name}: {e}")
        return 1
    out = pdf_path(args.output_dir, invoice.invoice_id, template.stem)
    try:
        write_pdf(html, out, base_url=template.parent)
    except OSError as e:
        # Так WeasyPrint сообщает, что не нашёл системные библиотеки Pango.
        print_fn(f"Не удалось создать PDF: {e}\nПроверьте установку Pango — см. README.")
        return 1
    print_fn(f"\nPDF сохранён: {out.resolve()}")

    if not args.no_open:
        try:
            open_file(out.resolve())
        except (OSError, subprocess.CalledProcessError) as e:
            print_fn(f"Открыть автоматически не получилось ({e}); файл на месте.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(args)
    except (KeyboardInterrupt, EOFError):
        print("\nОтменено.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
