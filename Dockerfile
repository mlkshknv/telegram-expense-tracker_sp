# syntax=docker/dockerfile:1
# Многоэтапная сборка:
#   base    — Python + зависимости бота + исходный код
#   test    — дополнительно pytest; при сборке запускает unit-тесты
#   runtime — итоговый образ для запуска бота (без тестов и pytest)

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .

# ---------- этап тестирования ----------
FROM base AS test
COPY requirements-dev.txt test_bot.py ./
RUN pip install -r requirements-dev.txt
# Если хотя бы один тест упадёт, сборка образа (и стадия Jenkins) завершится ошибкой
RUN mkdir -p /reports && python -m pytest -v --junitxml=/reports/junit.xml

# ---------- рабочий образ ----------
FROM base AS runtime
LABEL org.opencontainers.image.title="telegram-expense-tracker" \
      org.opencontainers.image.description="Telegram-бот для учёта личных расходов студентов" \
      org.opencontainers.image.source="https://github.com/mlkshknv/telegram-expense-tracker_sp"
RUN useradd --create-home --uid 10001 botuser \
    && mkdir -p /app/data \
    && chown botuser:botuser /app/data
ENV DB_PATH=/app/data/expenses.db
USER botuser
VOLUME ["/app/data"]
# BOT_TOKEN передаётся при запуске: docker run -e BOT_TOKEN=... 
CMD ["python", "bot.py"]
