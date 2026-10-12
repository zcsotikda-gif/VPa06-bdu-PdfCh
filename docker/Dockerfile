# Безэкранная часть и pytest на Linux. Открытие PDF системной программой здесь
# не проверяется — в контейнере её нет; тесты запускают сценарий с --no-open.
FROM python:3.12-slim

# Системные библиотеки WeasyPrint для Debian — по официальной инструкции установки.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
# Не editable: тесты идут против установленного пакета, в том числе шрифтов внутри него.
RUN pip install --no-cache-dir ".[dev]"
COPY tests ./tests
COPY data ./data
COPY templates ./templates

CMD ["pytest", "-q"]
