from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import insert, select, desc
from databases import Database
from .models import prices, betas

class DatabaseManager:
    def __init__(self, database: Database):
        self.database = database

    async def insert_price(self, price_data: dict) -> int:
        """Асинхронно вставляет запись о цене в таблицу prices.
        Args:
            price_data (dict): Данные для вставки. Должны содержать ключи:
                'symbol', 'price', 'timestamp'
        Returns:
            int: ID вставленной записи.
        """
        query = insert(prices).values(price_data)
        return await self.database.execute(query)

    async def insert_beta(self, beta_value: float, calculated_at) -> int:
        """Асинхронно вставляет запись о рассчитанном коэффициенте beta.
        Args:
            beta_value (float): Значение коэффициента beta.
            calculated_at (datetime): Время расчета.
        Returns:
            int: ID вставленной записи.
        """
        query = insert(betas).values(beta=beta_value, calculated_at=calculated_at)
        return await self.database.execute(query)

    async def get_latest_beta(self) -> float:
        """Получает последнее рассчитанное значение beta из БД."""
        query = select(betas.c.beta).order_by(desc(betas.c.calculated_at)).limit(1)
        result = await self.database.fetch_one(query)
        return float(result['beta']) if result else None

    async def get_latest_beta_and_timestamp(self) -> Optional[Tuple[float, datetime]]:
        """
        Получает последнее рассчитанное значение beta и время его расчёта из БД.

        Returns:
            Кортеж (beta_value, calculated_at) или None, если запись отсутствует.
        """
        query = select(betas.c.beta, betas.c.calculated_at).order_by(desc(betas.c.calculated_at)).limit(1)
        result = await self.database.fetch_one(query)
        return (float(result['beta']), result['calculated_at']) if result else None
