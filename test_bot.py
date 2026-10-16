
import sqlite3

import pytest

import bot


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    database_path = tmp_path / "test_expenses.db"
    monkeypatch.setattr(bot, "DB_PATH", database_path)
    bot.connect_db()
    return database_path


def test_add_expense_and_monthly_stats(temporary_database):
    bot.add_expense(123, 2500, "Еда")
    bot.add_expense(123, 1000, "Транспорт")
    bot.add_expense(456, 9000, "Еда")

    total, count, categories = bot.get_monthly_stats(123)

    assert total == 3500
    assert count == 2
    assert dict(categories) == {
        "Еда": 2500,
        "Транспорт": 1000,
    }


def test_invalid_amount_is_rejected(temporary_database):
    with pytest.raises(ValueError):
        bot.add_expense(123, -100, "Еда")


def test_invalid_category_is_rejected(temporary_database):
    with pytest.raises(ValueError):
        bot.add_expense(123, 500, "Космос")


def test_user_sees_only_own_expenses(temporary_database):
    bot.add_expense(123, 2500, "Еда")
    bot.add_expense(456, 7000, "Учёба")

    expenses = bot.get_recent_expenses(123)

    assert len(expenses) == 1
    assert expenses[0][0] == 2500


def test_database_stores_expense(temporary_database):
    bot.add_expense(123, 1500, "Здоровье")

    with sqlite3.connect(temporary_database) as connection:
        row = connection.execute(
            "SELECT user_id, amount, category FROM expenses"
        ).fetchone()

    assert row == (123, 1500, "Здоровье")