from decimal import Decimal
from pathlib import Path

import jinja2
import pytest
from pypdf import PdfReader

from pdf_checker.domain import Invoice, LineItem
from pdf_checker.render import money, pdf_path, quantity, render_html, write_pdf

PROJECT_TEMPLATES = Path(__file__).parent.parent / "templates"

INVOICE = Invoice(
    invoice_id="Ч-001",
    date="2026-10-12",
    customer="ООО «Ромашка» <script>",
    items=(
        LineItem("Подшипник шариковый", Decimal("2"), Decimal("1250.50")),
        LineItem("Смазка, кг", Decimal("0.5"), Decimal("480")),
    ),
)


def test_money_groups_thousands_with_comma_decimal():
    assert money(Decimal("1234567.5")) == "1 234 567,50"


def test_quantity_drops_trailing_zeros_without_exponent():
    assert quantity(Decimal("2.000")) == "2"
    assert quantity(Decimal("100")) == "100"
    assert quantity(Decimal("0.50")) == "0,5"


def test_render_escapes_data(tmp_path):
    template = tmp_path / "t.html"
    template.write_text("<p>{{ invoice.customer }}</p>", encoding="utf-8")
    html = render_html(template, INVOICE, generated_at="12.10.2026 20:30")
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_render_typo_in_template_fails(tmp_path):
    template = tmp_path / "t.html"
    template.write_text("{{ invoice.custmer }}", encoding="utf-8")
    with pytest.raises(jinja2.UndefinedError):
        render_html(template, INVOICE, generated_at="")


def test_pdf_path_replaces_characters_forbidden_on_windows(tmp_path):
    path = pdf_path(tmp_path, 'A/B:C*?"<>|', "receipt")
    assert path == tmp_path / "A_B_C_______receipt.pdf"


@pytest.mark.parametrize("template", sorted(PROJECT_TEMPLATES.glob("*.html")), ids=lambda p: p.name)
def test_project_templates_produce_pdf_with_cyrillic_and_dejavu(template, tmp_path):
    html = render_html(template, INVOICE, generated_at="12.10.2026 20:30")
    out = tmp_path / "out.pdf"
    write_pdf(html, out, base_url=template.parent)

    assert out.read_bytes().startswith(b"%PDF")
    reader = PdfReader(out)
    text = "".join(page.extract_text() for page in reader.pages)
    assert "Подшипник шариковый" in text
    assert "Ромашка" in text

    fonts = set()
    for page in reader.pages:
        for font in page["/Resources"]["/Font"].values():
            fonts.add(str(font.get_object()["/BaseFont"]))
    assert fonts, "в PDF нет шрифтов"
    # Любой другой шрифт — подстановка системой: где-то текст вышел не DejaVu Sans.
    assert all("DejaVu-Sans" in name for name in fonts), fonts


def test_project_has_templates():
    assert len(list(PROJECT_TEMPLATES.glob("*.html"))) >= 2
