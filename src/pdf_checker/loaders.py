"""Чтение чеков из CSV и JSON.

CSV — одна строка на позицию, строки одного чека связаны колонкой invoice_id.
JSON — список чеков, у каждого список позиций items.
Любое расхождение с форматом — DataFileError с понятной причиной.
"""

import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pdf_checker.domain import Invoice, LineItem

CSV_COLUMNS = ("invoice_id", "date", "customer", "item", "quantity", "price")
INVOICE_KEYS = ("invoice_id", "date", "customer", "items")
ITEM_KEYS = ("name", "quantity", "price")


class DataFileError(Exception):
    """Файл данных не соответствует ожидаемому формату."""


def discover(directory: Path, suffixes: set[str]) -> list[Path]:
    if not directory.is_dir():
        return []
    found = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in suffixes]
    return sorted(found, key=lambda p: p.name.lower())


def load_invoices(path: Path) -> list[Invoice]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    raise DataFileError(f"неизвестный формат: {path.suffix}")


def _decimal(value: object, where: str) -> Decimal:
    # Запятая как разделитель дробной части — обычное дело в русских таблицах.
    text = str(value).strip().replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        raise DataFileError(f"{where}: не число: {value!r}") from None


def load_csv(path: Path) -> list[Invoice]:
    # utf-8-sig снимает BOM, который ставит Excel при сохранении в CSV UTF-8.
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise DataFileError(f"нет колонок: {', '.join(missing)}")

        headers: dict[str, tuple[str, str]] = {}
        items: dict[str, list[LineItem]] = {}
        for row in reader:
            where = f"строка {reader.line_num}"
            invoice_id = row["invoice_id"].strip()
            if not invoice_id:
                raise DataFileError(f"{where}: пустой invoice_id")
            header = (row["date"].strip(), row["customer"].strip())
            known = headers.setdefault(invoice_id, header)
            if known != header:
                raise DataFileError(
                    f"{where}: у чека {invoice_id} разные дата или покупатель в разных строках"
                )
            items.setdefault(invoice_id, []).append(
                LineItem(
                    name=row["item"].strip(),
                    quantity=_decimal(row["quantity"], where),
                    price=_decimal(row["price"], where),
                )
            )
    return [
        Invoice(invoice_id, date, customer, tuple(items[invoice_id]))
        for invoice_id, (date, customer) in headers.items()
    ]


def load_json(path: Path) -> list[Invoice]:
    try:
        # parse_float=Decimal: 0.1 из файла остаётся точным 0.1, а не двоичным приближением.
        data = json.loads(path.read_text(encoding="utf-8-sig"), parse_float=Decimal)
    except json.JSONDecodeError as e:
        raise DataFileError(f"битый JSON: {e}") from None
    if not isinstance(data, list):
        raise DataFileError("ожидается список чеков на верхнем уровне")

    invoices: list[Invoice] = []
    seen: set[str] = set()
    for n, raw in enumerate(data, start=1):
        where = f"чек №{n}"
        if not isinstance(raw, dict):
            raise DataFileError(f"{where}: ожидается объект")
        missing = [k for k in INVOICE_KEYS if k not in raw]
        if missing:
            raise DataFileError(f"{where}: нет полей: {', '.join(missing)}")
        invoice_id = str(raw["invoice_id"]).strip()
        if invoice_id in seen:
            raise DataFileError(f"{where}: повтор invoice_id {invoice_id}")
        seen.add(invoice_id)
        if not isinstance(raw["items"], list):
            raise DataFileError(f"{where}: items должен быть списком")

        items = []
        for m, item in enumerate(raw["items"], start=1):
            item_where = f"{where}, позиция {m}"
            if not isinstance(item, dict):
                raise DataFileError(f"{item_where}: ожидается объект")
            missing = [k for k in ITEM_KEYS if k not in item]
            if missing:
                raise DataFileError(f"{item_where}: нет полей: {', '.join(missing)}")
            items.append(
                LineItem(
                    name=str(item["name"]),
                    quantity=_decimal(item["quantity"], item_where),
                    price=_decimal(item["price"], item_where),
                )
            )
        invoices.append(Invoice(invoice_id, str(raw["date"]), str(raw["customer"]), tuple(items)))
    return invoices
