"""Предметная модель чека. Без ввода-вывода: только данные и арифметика."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LineItem:
    name: str
    quantity: Decimal
    price: Decimal

    @property
    def total(self) -> Decimal:
        return self.quantity * self.price


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    date: str
    customer: str
    items: tuple[LineItem, ...]

    @property
    def total(self) -> Decimal:
        return sum((item.total for item in self.items), Decimal("0"))
