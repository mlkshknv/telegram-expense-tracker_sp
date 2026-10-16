
# Telegram Expense Tracker Bot

Telegram-бот для учета личных расходов студентов в Казахстане.

## Возможности

- Добавление расходов в тенге.
- Категоризация расходов.
- Просмотр последних расходов.
- Месячная статистика.
- Хранение данных в SQLite.
- Автоматические тесты через pytest.
- CI через GitHub Actions.

## Технологии

- Python 3.11+
- python-telegram-bot
- SQLite
- pytest
- Git и GitHub
- GitHub Actions

## Команды бота

- `/start` — запуск и инструкция.
- `/add 2500 Еда` — добавление расхода.
- `/list` — последние расходы.
- `/stats` — статистика за месяц.
- `/help` — помощь.

## Установка на Windows

1. Установить Python.
2. Создать виртуальное окружение:
   `python -m venv .venv`
3. Активировать:
   `.\.venv\Scripts\Activate.ps1`
4. Установить библиотеки (с pytest для тестов):
   `python -m pip install -r requirements-dev.txt`
5. Установить переменную окружения BOT_TOKEN.
6. Запустить:
   `python bot.py`

## Тестирование

Запустить:

`python -m pytest -v`

## CI/CD

- **GitHub Actions** запускает тесты при push и pull request (`.github/workflows/ci.yml`).
- **Jenkins** (`Jenkinsfile`): тесты в Docker → сборка образа → smoke-тест →
  (опционально) push в Docker Hub → (бонус) деплой в Minikube.
- **Docker**: многоэтапный `Dockerfile` (этапы `test` и `runtime`).
- Инструкция по запуску Jenkins: [`docs/JENKINS_SETUP.md`](docs/JENKINS_SETUP.md).

### Запуск в Docker

```bash
docker build --target runtime -t telegram-expense-tracker .
docker run --rm -e BOT_TOKEN=<токен> -v expense-data:/app/data telegram-expense-tracker
```

## Хранение данных

Расходы хранятся локально в SQLite.
Токен бота и база данных не должны публиковаться в репозитории.

## Ограничения

Бот работает, пока запущена программа на компьютере.
Для постоянной доступности требуется размещение на сервере.