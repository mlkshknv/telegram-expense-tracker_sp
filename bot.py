
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Путь к базе можно переопределить переменной окружения DB_PATH
# (в Docker-контейнере база хранится в томе /app/data).
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).with_name("expenses.db")))

CATEGORIES = {
    "еда",
    "транспорт",
    "учёба",
    "развлечения",
    "здоровье",
    "другое",
}


def connect_db():
    """Open the database and create the expenses table if needed."""
    connection = sqlite3.connect(DB_PATH)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    connection.commit()
    return connection


def add_expense(user_id, amount, category):
    """Validate and save an expense."""
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError("Сумма должна быть положительным целым числом.")

    category = category.strip().capitalize()

    if category.lower() not in CATEGORIES:
        raise ValueError(
            "Неизвестная категория. Используй: "
            "Еда, Транспорт, Учёба, Развлечения, "
            "Здоровье или Другое."
        )

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with connect_db() as connection:
        connection.execute(
            """
            INSERT INTO expenses
            (user_id, amount, category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, amount, category, created_at),
        )


def get_recent_expenses(user_id, limit=10):
    """Return the user's latest expenses."""
    with connect_db() as connection:
        return connection.execute(
            """
            SELECT amount, category, created_at
            FROM expenses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def get_monthly_stats(user_id):
    """Calculate the user's current-month statistics."""
    month = datetime.now().strftime("%Y-%m")

    with connect_db() as connection:
        total, count = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0), COUNT(*)
            FROM expenses
            WHERE user_id = ?
              AND substr(created_at, 1, 7) = ?
            """,
            (user_id, month),
        ).fetchone()

        categories = connection.execute(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id = ?
              AND substr(created_at, 1, 7) = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (user_id, month),
        ).fetchall()

    return total, count, categories


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для учёта личных расходов.\n\n"
        "Все суммы указываются в тенге.\n\n"
        "Команды:\n"
        "/add 2500 Еда — добавить расход\n"
        "/list — последние расходы\n"
        "/stats — статистика за месяц\n"
        "/help — помощь\n\n"
        "Категории: Еда, Транспорт, Учёба, "
        "Развлечения, Здоровье, Другое."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await start(update, context)


async def add_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Формат: /add СУММА КАТЕГОРИЯ\n"
            "Пример: /add 2500 Еда"
        )
        return

    try:
        amount = int(context.args[0])
        category = " ".join(context.args[1:])

        add_expense(
            update.effective_user.id,
            amount,
            category,
        )

        await update.message.reply_text(
            f"Расход добавлен: {amount} ₸, категория — "
            f"{category.capitalize()}."
        )

    except ValueError as error:
        await update.message.reply_text(str(error))


async def list_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    expenses = get_recent_expenses(update.effective_user.id)

    if not expenses:
        await update.message.reply_text(
            "Расходов пока нет. Добавь первый: /add 2500 Еда"
        )
        return

    lines = ["Последние расходы:"]

    for amount, category, created_at in expenses:
        lines.append(
            f"• {created_at} — {category}: {amount} ₸"
        )

    await update.message.reply_text("\n".join(lines))


async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    total, count, categories = get_monthly_stats(
        update.effective_user.id
    )

    lines = [
        "Статистика за текущий месяц:",
        f"Всего потрачено: {total} ₸",
        f"Количество расходов: {count}",
        "",
        "По категориям:",
    ]

    if categories:
        for category, amount in categories:
            lines.append(f"• {category}: {amount} ₸")
    else:
        lines.append("Пока нет расходов за этот месяц.")

    await update.message.reply_text("\n".join(lines))


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "Не задан BOT_TOKEN. Установи токен в переменной окружения."
        )

    connect_db()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("stats", stats_command))

    print("Бот запущен. Для остановки нажми Ctrl+C.")
    app.run_polling()


if __name__ == "__main__":
    main()