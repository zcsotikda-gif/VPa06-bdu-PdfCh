from decimal import Decimal

from pdf_checker.domain import Invoice, LineItem


def test_line_total_is_exact():
    item = LineItem(name="Кофе", quantity=Decimal("3"), price=Decimal("0.1"))
    assert item.total == Decimal("0.3")


def test_invoice_total_sums_lines():
    invoice = Invoice(
        invoice_id="A-1",
        date="2026-10-12",
        customer="Иванов",
        items=(
            LineItem("Чай", Decimal("2"), Decimal("150.00")),
            LineItem("Сахар", Decimal("1"), Decimal("89.90")),
        ),
    )
    assert invoice.total == Decimal("389.90")
