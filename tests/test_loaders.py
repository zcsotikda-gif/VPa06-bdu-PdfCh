import json
from decimal import Decimal

import pytest

from pdf_checker.loaders import DataFileError, discover, load_invoices

CSV_HEADER = "invoice_id,date,customer,item,quantity,price\n"


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_csv_groups_rows_by_invoice_id_in_file_order(tmp_path):
    path = write(
        tmp_path / "a.csv",
        CSV_HEADER
        + "B-2,2026-10-01,Петров,Хлеб,1,45.50\n"
        + "A-1,2026-10-02,Иванов,Чай,2,150\n"
        + 'B-2,2026-10-01,Петров,Молоко,2,"89,90"\n',
    )
    invoices = load_invoices(path)
    assert [i.invoice_id for i in invoices] == ["B-2", "A-1"]
    b2 = invoices[0]
    assert [item.name for item in b2.items] == ["Хлеб", "Молоко"]
    assert b2.items[1].price == Decimal("89.90")
    assert b2.total == Decimal("225.30")


def test_csv_with_excel_bom_is_read(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_text(CSV_HEADER + "A-1,2026-10-02,Иванов,Чай,1,10\n", encoding="utf-8-sig")
    assert load_invoices(path)[0].invoice_id == "A-1"


def test_csv_missing_column_names_it(tmp_path):
    path = write(tmp_path / "bad.csv", "invoice_id,date,item,quantity,price\nA,1,x,1,1\n")
    with pytest.raises(DataFileError, match="customer"):
        load_invoices(path)


def test_csv_bad_number_reports_line(tmp_path):
    path = write(tmp_path / "bad.csv", CSV_HEADER + "A,2026-10-02,Иванов,Чай,два,10\n")
    with pytest.raises(DataFileError, match="строка 2"):
        load_invoices(path)


def test_csv_conflicting_header_fields_for_same_id(tmp_path):
    path = write(
        tmp_path / "bad.csv",
        CSV_HEADER + "A,2026-10-02,Иванов,Чай,1,10\nA,2026-10-02,Петров,Хлеб,1,10\n",
    )
    with pytest.raises(DataFileError, match="A"):
        load_invoices(path)


def test_json_invoices(tmp_path):
    data = [
        {
            "invoice_id": "J-1",
            "date": "2026-10-03",
            "customer": "Сидорова",
            "items": [{"name": "Сыр", "quantity": 0.5, "price": 0.1}],
        }
    ]
    path = write(tmp_path / "a.json", json.dumps(data, ensure_ascii=False))
    [invoice] = load_invoices(path)
    assert invoice.customer == "Сидорова"
    assert invoice.items[0].total == Decimal("0.05")


def test_json_duplicate_id_rejected(tmp_path):
    one = {"invoice_id": "J", "date": "d", "customer": "c", "items": []}
    path = write(tmp_path / "a.json", json.dumps([one, one]))
    with pytest.raises(DataFileError, match="J"):
        load_invoices(path)


def test_json_missing_key_rejected(tmp_path):
    path = write(tmp_path / "a.json", json.dumps([{"invoice_id": "J", "items": []}]))
    with pytest.raises(DataFileError, match="date"):
        load_invoices(path)


def test_json_not_a_list_rejected(tmp_path):
    path = write(tmp_path / "a.json", "{}")
    with pytest.raises(DataFileError):
        load_invoices(path)


def test_broken_json_rejected(tmp_path):
    path = write(tmp_path / "a.json", "[{")
    with pytest.raises(DataFileError):
        load_invoices(path)


def test_discover_filters_and_sorts(tmp_path):
    for name in ["b.json", "a.csv", "notes.txt", "C.CSV"]:
        write(tmp_path / name, "")
    (tmp_path / "sub.csv").mkdir()
    found = discover(tmp_path, {".csv", ".json"})
    assert [p.name for p in found] == ["a.csv", "b.json", "C.CSV"]


def test_discover_missing_dir_is_empty(tmp_path):
    assert discover(tmp_path / "nope", {".csv"}) == []
