import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import inspect
from src.database.models import metadata
from src.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Инициализирует базу данных: проверяет таблицы, создаёт при необходимости."""
    database_url = str(settings.database_url)
    logger.info(f"Using DATABASE_URL: {database_url}")
    logger.info("Checking database tables...")

    try:
        engine = create_async_engine(database_url, echo=True)

        async with engine.begin() as conn:  # type: AsyncConnection
            # Получаем список существующих таблиц через sync-инспектор
            def get_existing_tables(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()

            existing_tables = await conn.run_sync(get_existing_tables)
            all_tables = metadata.tables.keys()

            missing_tables = [t for t in all_tables if t not in existing_tables]

            if not missing_tables:
                for t in all_tables:
                    logger.info(f"Таблица '{t}' уже существует.")
            else:
                logger.info(f"Найдены отсутствующие таблицы: {missing_tables}. Создаю...")
                await conn.run_sync(metadata.create_all)

        await engine.dispose()
        logger.info("Проверка и создание таблиц завершены")

    except Exception as e:
        logger.error(f"Failed to check/create tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
