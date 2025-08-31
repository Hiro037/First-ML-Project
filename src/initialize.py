# src/initialize.py
import asyncio
import pandas as pd
from datetime import datetime
from .data_fetcher import BinanceDataFetcher
from .model import calculate_beta, prepare_data_for_regression
from .database.crud import DatabaseManager
from .config import settings
from databases import Database


async def initialize_model() -> float:
    """
    Инициализирует модель: загружает данные, рассчитывает и сохраняет beta.
    Возвращает рассчитанное значение beta.
    """
    print("Initializing model: loading historical data and calculating beta...")

    database_url_str = str(settings.database_url)
    database = Database(database_url_str)
    await database.connect()
    db_manager = DatabaseManager(database)

    try:
        # Загружаем исторические данные
        async with BinanceDataFetcher() as fetcher:
            btc_data = await fetcher.fetch_historical_data("BTCUSDT", days=60, interval="5m")
            eth_data = await fetcher.fetch_historical_data("ETHUSDT", days=60, interval="5m")

        print(f"Loaded {len(btc_data)} BTC and {len(eth_data)} ETH records")

        # Рассчитываем beta
        eth_prices, btc_prices = prepare_data_for_regression(eth_data, btc_data)
        beta_value, _, _ = calculate_beta(eth_prices, btc_prices)

        # Сохраняем beta в БД
        await db_manager.insert_beta(beta_value, datetime.utcnow())

        print(f"Model initialized successfully. Beta: {beta_value:.6f}")
        return beta_value

    finally:
        await database.disconnect()