# pdf-checker

Консольная программа: берёт чеки из CSV или JSON, подставляет один из них в
HTML-шаблон и сохраняет PDF (WeasyPrint), затем открывает его системной программой.

## Как работает

1. При запуске выводит пронумерованные списки файлов данных из `data/` и
   шаблонов из `templates/`. Файл, который не удалось разобрать, показывается
   с причиной и к выбору не предлагается.
2. Спрашивает номер файла данных и номер шаблона.
3. Выводит чеки выбранного файла (invoice id, дата, покупатель, сумма) и
   спрашивает номер чека.
4. Сохраняет `output/<invoice_id>_<шаблон>.pdf` и открывает его.

Каталоги берутся от текущего каталога; другие пути задаются ключами
`--data-dir`, `--templates-dir`, `--output-dir`. `--no-open` — не открывать PDF.

## Форматы данных

**CSV** (UTF-8, можно с BOM из Excel) — одна строка на позицию чека; строки
одного чека связаны `invoice_id`:

```
invoice_id,date,customer,item,quantity,price
INV-1001,2026-10-01,Иванов Пётр,Хлеб бородинский,1,54.90
INV-1001,2026-10-01,Иванов Пётр,Молоко 1 л,2,"89,90"
```

Дробная часть — через точку или запятую (запятую взять в кавычки).

**JSON** — список чеков:

```json
[{"invoice_id": "J-2001", "date": "2026-10-07", "customer": "Кузнецов Алексей",
  "items": [{"name": "Наушники", "quantity": 1, "price": 5990.00}]}]
```

## Шаблоны

Шаблоны — Jinja2. Доступны `invoice` (поля `invoice_id`, `date`, `customer`,
`items`, `total`; у позиции `name`, `quantity`, `price`, `total`) и
`generated_at`. Фильтры: `money` (`1 234,50`) и `quantity` (`0,5`).
Значения экранируются; опечатка в имени поля — ошибка, а не пустое место.

Кириллицу обеспечивает шрифт DejaVu Sans внутри пакета: в шаблоне достаточно
`html { font-family: "DejaVu Sans", sans-serif; }`. Именно на `html`, а не
`body`: колонтитулы страницы (`@page { @bottom-right {...} }`) наследуют шрифт
от корня и иначе выйдут шрифтом по умолчанию.

## Установка

Нужен Python 3.12+ и системная библиотека Pango (её использует WeasyPrint).

**macOS**

```
brew install pango
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

**Windows**

1. Поставить MSYS2 (https://www.msys2.org) и в его консоли выполнить
   `pacman -S mingw-w64-x86_64-pango`.
2. Добавить `C:\msys64\mingw64\bin` в `PATH` или задать переменную
   `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin`.
3. `py -3.12 -m venv .venv` и `.venv\Scripts\pip install -e ".[dev]"`.

Подробности — в инструкции WeasyPrint:
https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

## Запуск

```
.venv/bin/python -m pdf_checker          # macOS
.venv\Scripts\python -m pdf_checker      # Windows
```

## Проверки

```
.venv/bin/pytest
.venv/bin/ruff check .
docker compose -f docker/compose.yaml up --build --abort-on-container-exit
```

Последняя команда сама собирает образ `pdf-checker-tests` из `docker/Dockerfile`
(`--build`), поэтому хранить его между прогонами не нужно. Убрать образ и
контейнер после проверки:

```
docker compose -f docker/compose.yaml down --rmi local
```

Контейнер прогоняет тесты на Linux с Pango из Debian. Ветка открытия файла в
Windows (`os.startfile`) покрыта тестом с подменой, но вживую не проверялась.
