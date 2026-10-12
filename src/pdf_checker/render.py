"""HTML по шаблону Jinja2 и PDF через WeasyPrint.

Шрифт подключается здесь, а не в шаблонах: шаблону достаточно написать
font-family: "DejaVu Sans", и кириллица не зависит от шрифтов системы.
"""

import re
from decimal import Decimal
from pathlib import Path

import jinja2

from pdf_checker.domain import Invoice

FONTS_DIR = Path(__file__).parent / "fonts"
# Запрещено в именах файлов Windows; на macOS разрешено, но имя должно работать везде.
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def money(value: Decimal) -> str:
    # 1234567.5 -> "1 234 567,50" с неразрывными пробелами: сумма не переносится.
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def quantity(value: Decimal) -> str:
    # format(..., "f") после normalize: 100 не превращается в 1E+2.
    return format(value.normalize(), "f").replace(".", ",")


def render_html(template_path: Path, invoice: Invoice, generated_at: str) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path.parent),
        autoescape=True,
        # Опечатка в шаблоне — ошибка, а не пустое место в чеке.
        undefined=jinja2.StrictUndefined,
    )
    env.filters["money"] = money
    env.filters["quantity"] = quantity
    template = env.get_template(template_path.name)
    return template.render(invoice=invoice, generated_at=generated_at)


def font_css() -> str:
    regular = (FONTS_DIR / "DejaVuSans.ttf").as_uri()
    bold = (FONTS_DIR / "DejaVuSans-Bold.ttf").as_uri()
    return f"""
@font-face {{ font-family: "DejaVu Sans"; src: url("{regular}"); font-weight: normal; }}
@font-face {{ font-family: "DejaVu Sans"; src: url("{bold}"); font-weight: bold; }}
"""


def write_pdf(html: str, out_path: Path, base_url: Path) -> None:
    # Импорт здесь: WeasyPrint при импорте ищет системные Pango/GObject, и без них
    # остальная программа (меню, разбор данных) всё равно должна загружаться.
    from weasyprint import CSS, HTML
    from weasyprint.text.fonts import FontConfiguration

    font_config = FontConfiguration()
    fonts = CSS(string=font_css(), font_config=font_config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(base_url)).write_pdf(
        out_path, stylesheets=[fonts], font_config=font_config
    )


def pdf_path(output_dir: Path, invoice_id: str, template_name: str) -> Path:
    safe_id = _FORBIDDEN.sub("_", invoice_id).strip(" .") or "invoice"
    return output_dir / f"{safe_id}_{template_name}.pdf"
