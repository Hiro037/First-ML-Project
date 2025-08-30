# 1. Используем официальный образ Python с нужной версией (3.11 по ТЗ)
FROM python:3.11-slim

# 2. Настройки Python для контейнеров
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Указываем Poetry не создавать виртуальное окружение внутри контейнера
    POETRY_VIRTUALENVS_CREATE=false \
    # Устанавливаем путь для кеша pip
    PIP_CACHE_DIR=/tmp/pip_cache

# 3. Устанавливаем системные зависимости ТОЛЬКО для компиляции Python-пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Обязательно для сборки любых Python-пакетов с C-кодом
    build-essential \
    # Обязательно для psycopg2 (а значит и для asyncpg/SQLAlchemy)
    libpq-dev \
    # Чистим кеш apt, чтобы уменьшить размер образа
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Устанавливаем самую новую стабильную версию Poetry
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==1.8.2

# 5. Рабочая директория
WORKDIR /app

# 6. Копируем ТОЛЬКО файлы зависимостей в первую очередь
COPY pyproject.toml poetry.lock ./

# 7. Устанавливаем зависимости проекта через Poetry
RUN poetry install --no-interaction --no-ansi --only main

# 8. Копируем весь исходный код в контейнер
COPY ./src ./src
COPY ./tests ./tests

# 9. Запускаем проект
# CMD ["python", "-m", "src.main"]