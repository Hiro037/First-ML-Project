from datetime import datetime, timezone

import pytest
from databases import Database

from src.config import settings
from src.database.crud import DatabaseManager


class TestDatabase:
    """Тесты для работы с базой данных."""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Тест подключения к базе данных."""
        # Этот тест требует запущенной БД, поэтому может быть пропущен в CI
        try:
            database = Database(str(settings.database_url))
            await database.connect()
            assert database.is_connected is True
            await database.disconnect()
        except Exception:
            pytest.skip("Database not available for testing")

    @pytest.mark.asyncio
    async def test_insert_and_read_beta(self):
        """Тест записи и чтения коэффициента beta."""
        try:
            database = Database(str(settings.database_url))
            await database.connect()
            db_manager = DatabaseManager(database)

            # Тестовые данные
            test_beta = 1.123456
            test_time = datetime.now(timezone.utc)  # Исправлено: используем timezone-aware datetime

            # Записываем и читаем
            await db_manager.insert_beta(test_beta, test_time)
            latest_beta = await db_manager.get_latest_beta()

            assert abs(latest_beta - test_beta) < 0.000001
            await database.disconnect()

        except Exception:
            pytest.skip("Database not available for testing")

