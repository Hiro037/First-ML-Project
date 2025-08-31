import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable, Optional
import logging
import json

logger = logging.getLogger(__name__)


class BinanceWebSocketClient:
    """Класс для работы с WebSocket Binance в реальном времени."""

    BASE_WS_URL = "wss://stream.binance.com:9443/ws"

    def __init__(self):
        self.session = None
        self.websocket = None
        self.callback = None
        self.running = False

    async def connect(self, symbols: List[str], callback: Callable):
        """
        Подключается к WebSocket и начинает получать данные.

        Args:
            symbols: Список символов для подписки (например, ['btcusdt', 'ethusdt'])
            callback: Функция обратного вызова для обработки сообщений
        """
        self.callback = callback
        self.running = True

        # Формируем stream names
        streams = [f"{symbol}@trade" for symbol in symbols]
        stream_url = f"{self.BASE_WS_URL}/{'/'.join(streams)}"

        logger.info(f"Connecting to WebSocket: {stream_url}")

        try:
            self.session = aiohttp.ClientSession()
            self.websocket = await self.session.ws_connect(stream_url)
            await self._listen()

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
        finally:
            if self.session:
                await self.session.close()

    async def _listen(self):
        """Слушает сообщения от WebSocket."""
        async for msg in self.websocket:
            if not self.running:
                break

            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    await self.callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {msg.data}")
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                logger.info("WebSocket connection closed")
                break

    async def disconnect(self):
        """Отключается от WebSocket."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()

    @staticmethod
    def parse_trade_message(message: Dict) -> Optional[Dict]:
        """
        Парсит trade сообщение от Binance.

        Returns:
            Dict с полями: symbol, price, timestamp, quantity
        """
        if message.get('e') != 'trade':
            return None

        return {
            'symbol': message.get('s'),
            'price': float(message.get('p', 0)),
            'timestamp': message.get('E'),  # Event time
            'quantity': float(message.get('q', 0)),
            'is_buyer_maker': message.get('m', False)
        }


# Добавляем WebSocket функционал в основной класс
class BinanceDataFetcher(BinanceWebSocketClient):
    """Комбинированный класс для REST и WebSocket API."""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self):
        super().__init__()
        self.rest_session = None  # Отдельная сессия для REST запросов

    async def __aenter__(self):
        self.rest_session = aiohttp.ClientSession()  # Инициализируем REST сессию
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        if self.rest_session:
            await self.rest_session.close()

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
            async with self.rest_session.get(url, params=params) as response:
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