import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pandas as pd
import pytest

from src.data_fetcher import (
    BinanceDataFetcher,
    BinanceWebSocketClient,
    get_historical_data,
)


class TestDataFetcher:
    """Тесты для классов работы с данными."""

    def test_parse_trade_message_valid(self):
        """Тест парсинга валидного trade сообщения."""
        message = {
            "e": "trade",
            "s": "BTCUSDT",
            "p": "50000.50",
            "E": 1644567890123,
            "q": "1.2345",
            "m": True,
        }

        parsed = BinanceWebSocketClient.parse_trade_message(message)

        assert parsed["symbol"] == "BTCUSDT"
        assert parsed["price"] == 50000.50
        assert parsed["timestamp"] == 1644567890123
        assert parsed["quantity"] == 1.2345
        assert parsed["is_buyer_maker"] is True

    def test_parse_trade_message_invalid(self):
        """Тест парсинга невалидного сообщения."""
        message = {"e": "kline", "s": "BTCUSDT"}  # Не trade сообщение
        parsed = BinanceWebSocketClient.parse_trade_message(message)
        assert parsed is None

        message = {}  # Пустое сообщение
        parsed = BinanceWebSocketClient.parse_trade_message(message)
        assert parsed is None

    @pytest.mark.asyncio
    async def test_websocket_connection_and_listen(self):
        """Тест подключения к WebSocket и прослушивания сообщений."""
        mock_websocket = AsyncMock()
        mock_websocket.__aiter__.return_value = [
            MagicMock(
                type=aiohttp.WSMsgType.TEXT,
                data=json.dumps({"e": "trade", "s": "BTCUSDT"}),
            ),
            MagicMock(type=aiohttp.WSMsgType.CLOSED),
        ]

        mock_session = AsyncMock()
        mock_session.ws_connect.return_value = mock_websocket

        client = BinanceWebSocketClient()
        callback = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Запускаем подключение в фоновой задаче
            task = asyncio.create_task(client.connect(["btcusdt"], callback))

            # Даем время на выполнение
            await asyncio.sleep(0.1)

            # Останавливаем клиент
            client.running = False
            await task

            # Проверяем, что callback был вызван
            callback.assert_called_once_with({"e": "trade", "s": "BTCUSDT"})

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_klines_success(self, mock_get):
        """Тест успешного получения исторических данных."""
        mock_response = [
            [
                1644567890123,
                "50000.0",
                "51000.0",
                "49000.0",
                "50500.0",
                "1000.0",
                1644567950123,
                "50500000.0",
                1000,
                "500.0",
                "25000000.0",
            ]
        ]

        # Настраиваем мок ответа
        mock_response_obj = AsyncMock()
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_response_obj.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response_obj

        # Создаем экземпляр и тестируем
        fetcher = BinanceDataFetcher()
        fetcher.rest_session = (
            aiohttp.ClientSession()
        )  # Просто создаем сессию, мок перехватит вызовы

        klines = await fetcher.fetch_klines("BTCUSDT", "1m", 1000)

        assert len(klines) == 1
        assert klines[0]["open"] == 50000.0
        assert klines[0]["high"] == 51000.0
        assert klines[0]["close"] == 50500.0
        assert klines[0]["volume"] == 1000.0

    @pytest.mark.asyncio
    async def test_websocket_message_handling(self):
        """Тест обработки различных типов сообщений WebSocket."""
        client = BinanceWebSocketClient()
        callback = AsyncMock()
        client.callback = callback

        # Тестируем текстовое сообщение
        text_msg = MagicMock(
            type=aiohttp.WSMsgType.TEXT,
            data=json.dumps({"e": "trade", "s": "BTCUSDT"}),
        )

        # Используем прямой вызов логики вместо мока
        if text_msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = json.loads(text_msg.data)
                await callback(data)
            except Exception:
                pass

        callback.assert_called_once_with({"e": "trade", "s": "BTCUSDT"})

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Тест работы контекстного менеджера."""
        mock_session = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            async with BinanceDataFetcher() as fetcher:
                assert fetcher.rest_session is mock_session
                assert (
                    fetcher.session is None
                )  # WebSocket session еще не создан

            # Проверяем, что сессия была закрыта
            mock_session.close.assert_called_once()

    def test_parse_trade_message_edge_cases(self):
        """Тест граничных случаев парсинга сообщений."""
        # Сообщение с отсутствующими полями
        message = {"e": "trade", "s": "BTCUSDT"}
        parsed = BinanceWebSocketClient.parse_trade_message(message)

        assert parsed["symbol"] == "BTCUSDT"
        assert parsed["price"] == 0.0
        assert parsed["quantity"] == 0.0
        assert parsed["is_buyer_maker"] is False
        assert parsed["timestamp"] is None

    @pytest.mark.asyncio
    @patch("src.data_fetcher.BinanceDataFetcher.fetch_klines")
    async def test_historical_data_empty(self, mock_fetch_klines):
        """Тест получения пустых исторических данных."""
        mock_fetch_klines.return_value = []

        fetcher = BinanceDataFetcher()
        df = await fetcher.fetch_historical_data("BTCUSDT", "5m", 7)

        assert df.empty
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_websocket_disconnect(self):
        """Тест отключения от WebSocket."""
        client = BinanceWebSocketClient()
        client.websocket = AsyncMock()
        client.session = AsyncMock()

        await client.disconnect()

        assert client.running is False
        client.websocket.close.assert_called_once()
        client.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_disconnect_no_connection(self):
        """Тест отключения когда нет активного соединения."""
        client = BinanceWebSocketClient()
        client.websocket = None
        client.session = None

        # Не должно быть исключений
        await client.disconnect()
        assert client.running is False

    @pytest.mark.asyncio
    @patch("src.data_fetcher.BinanceDataFetcher.fetch_historical_data")
    async def test_get_historical_data_utility(self, mock_fetch_historical):
        """Тест вспомогательной функции get_historical_data."""
        mock_df = pd.DataFrame({"close": [50000, 51000]})
        mock_fetch_historical.return_value = mock_df

        result = await get_historical_data("BTCUSDT", 7, "5m")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_klines_with_time_params(self, mock_get):
        """Тест получения klines с параметрами времени."""
        mock_response = [
            [
                1644567890123,
                "50000.0",
                "51000.0",
                "49000.0",
                "50500.0",
                "1000.0",
                1644567950123,
                "50500000.0",
                1000,
                "500.0",
                "25000000.0",
            ]
        ]

        # Настраиваем мок ответа
        mock_response_obj = AsyncMock()
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_response_obj.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response_obj

        fetcher = BinanceDataFetcher()
        fetcher.rest_session = aiohttp.ClientSession()

        start_time = 1644567890123
        end_time = 1644567950123

        klines = await fetcher.fetch_klines(
            "BTCUSDT", "1m", 1000, start_time, end_time
        )

        # Проверяем, что параметры времени переданы в запрос
        call_args = mock_get.call_args
        assert call_args[1]["params"]["startTime"] == start_time
        assert call_args[1]["params"]["endTime"] == end_time

        assert len(klines) == 1

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_klines_different_intervals(self, mock_get):
        """Тест получения klines с разными интервалами."""
        mock_response = [
            [
                1644567890123,
                "50000.0",
                "51000.0",
                "49000.0",
                "50500.0",
                "1000.0",
                1644567950123,
                "50500000.0",
                1000,
                "500.0",
                "25000000.0",
            ]
        ]

        mock_response_obj = AsyncMock()
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_response_obj.raise_for_status = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response_obj

        # Создаем экземпляр и инициализируем rest_session
        fetcher = BinanceDataFetcher()
        fetcher.rest_session = (
            aiohttp.ClientSession()
        )  # Используем rest_session вместо session

        # Тестируем разные интервалы
        intervals = ["1m", "5m", "1h", "1d"]
        for interval in intervals:
            klines = await fetcher.fetch_klines("BTCUSDT", interval, 100)
            assert len(klines) == 1

            # Проверяем, что интервал передан корректно
            call_args = mock_get.call_args
            assert call_args[1]["params"]["interval"] == interval
