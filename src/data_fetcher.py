import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BinanceDataFetcher:
    """Класс для загрузки исторических данных с Binance REST API."""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер для инициализации сессии."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер для закрытия сессии."""
        if self.session:
            await self.session.close()

    async def fetch_klines(
            self,
            symbol: str,
            interval: str = "1d",
            limit: int = 1000,
            start_time: int = None,
            end_time: int = None
    ) -> List[Dict[str, Any]]:
        """
        Загружает исторические данные свечей (klines) с Binance.

        Args:
            symbol: Тикер пары (например, 'BTCUSDT')
            interval: Интервал свечей ('1m', '5m', '1h', '1d', etc.)
            limit: Количество свечей для загрузки (макс. 1000)
            start_time: Начальное время в миллисекундах
            end_time: Конечное время в миллисекундах

        Returns:
            Список словарей с данными свечей
        """
        url = f"{self.BASE_URL}/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # Преобразуем данные в более удобный формат
                klines = []
                for kline in data:
                    klines.append({
                        "timestamp": kline[0],
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5]),
                        "close_time": kline[6],
                        "quote_asset_volume": float(kline[7]),
                        "number_of_trades": kline[8],
                        "taker_buy_base_volume": float(kline[9]),
                        "taker_buy_quote_volume": float(kline[10]),
                    })

                logger.info(f"Fetched {len(klines)} klines for {symbol}")
                return klines

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def fetch_historical_data(
            self,
            symbol: str,
            interval: str = "5m",
            days: int = 60
    ) -> pd.DataFrame:
        """
        Загружает исторические данные за указанное количество дней.

        Args:
            symbol: Тикер пары
            interval: Интервал свечей
            days: Количество дней истории

        Returns:
            DataFrame с историческими данными
        """
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        all_klines = []
        current_start = start_time

        # Binance ограничивает 1000 свечей за запрос, поэтому несколько запросов
        while current_start < end_time:
            klines = await self.fetch_klines(
                symbol=symbol,
                interval=interval,
                limit=1000,
                start_time=current_start,
                end_time=end_time
            )

            if not klines:
                break

            all_klines.extend(klines)
            current_start = klines[-1]["timestamp"] + 1  # Следующая миллисекунда после последней свечи

            # Небольшая задержка чтобы не превысить лимиты API
            await asyncio.sleep(0.1)

        # Преобразуем в DataFrame
        df = pd.DataFrame(all_klines)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("datetime", inplace=True)

        return df


# Утилитарная функция для удобства
async def get_historical_data(symbol: str, days: int = 60, interval: str = "5m") -> pd.DataFrame:
    """Вспомогательная функция для быстрой загрузки данных."""
    async with BinanceDataFetcher() as fetcher:
        return await fetcher.fetch_historical_data(symbol, interval, days)