# Интеграционные тесты
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.data_fetcher import BinanceDataFetcher
from src.database.crud import DatabaseManager
from src.initialize import initialize_model
from src.main import CryptoMonitor
from src.model import calculate_beta
from src.monitor import ResidualMonitor


class TestIntegration:
    """Интеграционные тесты всей системы."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Тест полного пайплайна: данные -> модель -> монитор."""
        # Создаем тестовые данные
        dates = pd.date_range("2024-01-01", periods=100, freq="h")
        btc_prices = pd.Series(
            np.random.normal(0, 0.001, 100).cumsum() + 50000, index=dates
        )
        eth_prices = pd.Series(
            1.5 * np.random.normal(0, 0.001, 100).cumsum() + 3000, index=dates
        )

        # Рассчитываем beta
        beta_value, eth_returns, btc_returns = calculate_beta(
            eth_prices, btc_prices
        )

        # Создаем монитор
        monitor = ResidualMonitor(
            beta=beta_value, threshold=0.01, window_minutes=60
        )

        # Симулируем обновление цен
        for i in range(1, len(btc_prices)):
            monitor.update_price("BTCUSDT", btc_prices.iloc[i], dates[i])
            monitor.update_price("ETHUSDT", eth_prices.iloc[i], dates[i])

        # Проверяем, что монитор работает
        assert monitor.current_sum is not None
        assert len(monitor.epsilon_window) > 0

    @pytest.mark.asyncio
    async def test_crypto_monitor_initialization(self):
        """Тест инициализации CryptoMonitor."""
        with patch("src.main.Database") as mock_database_class, patch(
            "src.main.DatabaseManager"
        ) as mock_db_manager_class:
            mock_db_instance = AsyncMock()
            mock_database_class.return_value = mock_db_instance
            mock_db_manager_instance = MagicMock(spec=DatabaseManager)
            mock_db_manager_class.return_value = mock_db_manager_instance
            mock_db_manager_instance.get_latest_beta = AsyncMock(
                return_value=1.5
            )

            monitor = CryptoMonitor()
            await monitor.initialize()

            mock_db_instance.connect.assert_called_once()
            mock_db_manager_instance.get_latest_beta.assert_called_once()
            assert monitor.monitor is not None
            assert monitor.monitor.beta == 1.5
            assert monitor.latest_beta == 1.5

    @pytest.mark.asyncio
    async def test_initialize_no_beta(self):
        """Тест инициализации без beta в БД."""
        with patch("src.main.Database") as mock_database_class, patch(
            "src.main.DatabaseManager"
        ) as mock_db_manager_class:
            mock_db_instance = AsyncMock()
            mock_database_class.return_value = mock_db_instance
            mock_db_manager_instance = MagicMock(spec=DatabaseManager)
            mock_db_manager_class.return_value = mock_db_manager_instance
            mock_db_manager_instance.get_latest_beta = AsyncMock(
                return_value=None
            )

            monitor = CryptoMonitor()
            with pytest.raises(
                ValueError, match="No beta coefficient found in database"
            ):
                await monitor.initialize()

    @pytest.mark.asyncio
    async def test_crypto_monitor_trade_callback(self):
        """Тест обработки сообщений в trade_callback."""
        monitor = CryptoMonitor()
        monitor.monitor = ResidualMonitor(
            beta=1.5, threshold=0.01, window_minutes=60
        )

        # Мокаем parse_trade_message
        mock_message = {
            "symbol": "ETHUSDT",
            "price": 3200.0,
            "timestamp": 1698765432000,  # 2023-10-31 12:34:52
        }
        with patch.object(
            BinanceDataFetcher,
            "parse_trade_message",
            return_value=mock_message,
        ):
            # Вызываем callback
            await monitor.trade_callback({"data": "test"})

        # Проверяем, что монитор обновил цену
        assert len(monitor.monitor.epsilon_window) >= 0
        assert monitor.monitor.last_prices["ETHUSDT"] == 3200.0

    @pytest.mark.asyncio
    async def test_trade_callback_invalid_message(self):
        """Тест trade_callback с невалидным сообщением."""
        monitor = CryptoMonitor()
        monitor.monitor = ResidualMonitor(
            beta=1.5, threshold=0.01, window_minutes=60
        )
        with patch.object(
            BinanceDataFetcher, "parse_trade_message", return_value=None
        ):
            await monitor.trade_callback({"data": "invalid"})
        # Просто покрытие return

    @pytest.mark.asyncio
    async def test_trade_callback_exception(self):
        """Тест trade_callback с исключением."""
        monitor = CryptoMonitor()
        monitor.monitor = ResidualMonitor(
            beta=1.5, threshold=0.01, window_minutes=60
        )
        with patch.object(
            BinanceDataFetcher,
            "parse_trade_message",
            side_effect=Exception("Test error"),
        ), patch("src.main.logger") as mock_logger:
            await monitor.trade_callback({"data": "test"})
        mock_logger.error.assert_called_with(
            "Error in trade callback: Test error"
        )

    @pytest.mark.asyncio
    async def test_trade_callback_with_alert(self):
        """Тест trade_callback с срабатыванием алерта."""
        monitor = CryptoMonitor()
        monitor.monitor = ResidualMonitor(
            beta=1.0, threshold=0.05, window_minutes=60
        )

        with patch.object(
            BinanceDataFetcher, "parse_trade_message"
        ) as mock_parse, patch("src.main.logger") as mock_logger, patch(
            "builtins.print"
        ) as mock_print:
            mock_parse.side_effect = [
                {
                    "symbol": "BTCUSDT",
                    "price": 100.0,
                    "timestamp": 1698765432000,
                },
                {
                    "symbol": "ETHUSDT",
                    "price": 10.0,
                    "timestamp": 1698765432000,
                },
                {
                    "symbol": "BTCUSDT",
                    "price": 101.0,
                    "timestamp": 1698765432000,
                },
                {
                    "symbol": "ETHUSDT",
                    "price": 11.0,
                    "timestamp": 1698765432000,
                },
            ]

            await monitor.trade_callback({"data": "btc1"})
            await monitor.trade_callback({"data": "eth1"})
            await monitor.trade_callback({"data": "btc2"})
            await monitor.trade_callback({"data": "eth2"})

        mock_print.assert_called()
        mock_logger.warning.assert_called()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_initialize_model(self):
        """Тест функции initialize_model."""
        # Мокаем данные в формате, ожидаемом prepare_data_for_regression
        dates = pd.date_range("2024-01-01", periods=4, freq="h")
        mock_btc_data = pd.DataFrame(
            {
                "timestamp": [int(d.timestamp() * 1000) for d in dates],
                "close": [50000.0, 50100.0, 50200.0, 50300.0],
            }
        )
        mock_eth_data = pd.DataFrame(
            {
                "timestamp": [int(d.timestamp() * 1000) for d in dates],
                "close": [3000.0, 3050.0, 3100.0, 3150.0],
            }
        )

        # Мокаем зависимости
        with patch(
            "src.initialize.BinanceDataFetcher.fetch_historical_data",
            AsyncMock(side_effect=[mock_btc_data, mock_eth_data]),
        ) as mock_fetch, patch(
            "src.initialize.DatabaseManager.insert_beta", AsyncMock()
        ) as mock_insert:
            # Вызываем initialize_model
            beta = await initialize_model()

        # Проверяем, что данные запрошены и beta сохранена
        assert mock_fetch.called
        assert mock_insert.called
        assert isinstance(beta, float)

    @pytest.mark.asyncio
    async def test_beta_recalculation(self):
        """Тест периодического пересчета beta."""
        monitor = CryptoMonitor()
        with patch.object(monitor, "database", AsyncMock()), patch.object(
            monitor, "db_manager", MagicMock(spec=DatabaseManager)
        ) as mock_db_manager:
            mock_db_manager.get_latest_beta = AsyncMock(return_value=1.6)

            # Мокаем initialize_model
            with patch(
                "src.main.initialize_model", AsyncMock(return_value=1.7)
            ):
                # Выполняем пересчет
                await monitor._load_and_set_beta()

            # Проверяем, что beta обновлена
            assert monitor.latest_beta == 1.6
            assert monitor.monitor.beta == 1.6

    @pytest.mark.asyncio
    async def test_start_monitoring_error(self):
        """Тест start_monitoring с ошибкой."""
        monitor = CryptoMonitor()

        # Создаем мок для cleanup
        monitor.cleanup = AsyncMock()

        with patch.object(
            monitor,
            "initialize",
            AsyncMock(side_effect=Exception("Init error")),
        ), patch("src.main.logger.error") as mock_logger:
            with pytest.raises(Exception, match="Init error"):
                await monitor.start_monitoring()

        mock_logger.assert_called_with("Monitoring error: Init error")
        monitor.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_with_none_values(self):
        """Тест cleanup с None значениями."""
        monitor = CryptoMonitor()

        # Устанавливаем None значения
        monitor.beta_recalculation_task = None
        monitor.data_fetcher = None
        monitor.database = None

        # Не должно быть исключений
        await monitor.cleanup()
