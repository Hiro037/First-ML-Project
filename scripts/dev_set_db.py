import asyncio
from sqlalchemy import create_engine
from src.database.models import metadata  # Импортируем metadata
from src.config import settings  # Предполагается, что у вас будет файл config.py с настройками

# Формируем sync URL для создания таблиц (синхронный вызов)
SYNC_DATABASE_URL = settings.database_url

async def async_main():
    # 1. Создаем синхронный движок и создаем все таблицы
    sync_engine = create_engine(SYNC_DATABASE_URL)
    print("Dropping and creating tables...")
    metadata.drop_all(sync_engine)  # Удаляем старые таблицы (для чистоты теста)
    metadata.create_all(sync_engine)  # Создаем новые таблицы
    sync_engine.dispose()
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(async_main())