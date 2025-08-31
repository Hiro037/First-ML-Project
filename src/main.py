import asyncio
from datetime import datetime, timedelta
from typing import Dict
import logging
from .data_fetcher import BinanceDataFetcher
from .monitor import ResidualMonitor
from .database.crud import DatabaseManager
from .config import settings
from databases import Database
from .initialize import initialize_model
logger = logging.getLogger(__name__)


class CryptoMonitor:
    """Основной класс приложения для мониторинга в реальном времени."""

    def __init__(self):
        self.data_fetcher = BinanceDataFetcher()
        self.monitor = None
        self.db_manager = None
        self.database = None
        self.beta_recalculation_task = None
        self.latest_beta = None

    async def initialize(self):
        """Инициализирует все компоненты системы."""
        # Подключаемся к БД
        self.database = Database(str(settings.database_url))
        await self.database.connect()
        self.db_manager = DatabaseManager(self.database)

        # Загружаем и устанавливаем beta
        await self._load_and_set_beta()

        logger.info(f"Monitor initialized with beta={self.latest_beta:.6f}")
        print(f"Monitoring started with beta={self.latest_beta:.6f}, threshold={settings.price_change_threshold}%")

    async def _load_and_set_beta(self):
        """Загружает beta из БД и обновляет монитор."""
        self.latest_beta = await self.db_manager.get_latest_beta()
        if self.latest_beta is None:
            raise ValueError("No beta coefficient found in database. Run initialization first.")

        if self.monitor:
            # Обновляем существующий монитор
            self.monitor.beta = self.latest_beta
        else:
            # Создаем новый монитор
            self.monitor = ResidualMonitor(
                beta=self.latest_beta,
                threshold=settings.price_change_threshold,
                window_minutes=settings.lookback_window_minutes
            )

    async def trade_callback(self, message: Dict):
        """
        Callback-функция для обработки сообщений от WebSocket.
        """
        try:
            # Парсим сообщение
            parsed = BinanceDataFetcher.parse_trade_message(message)
            if not parsed:
                return

            symbol = parsed['symbol']
            price = parsed['price']
            timestamp = datetime.fromtimestamp(parsed['timestamp'] / 1000)

            # Обновляем цену в мониторе
            cumulative_epsilon = self.monitor.update_price(symbol, price, timestamp)

            if cumulative_epsilon is not None:
                # Проверяем условие оповещения
                if self.monitor.check_alert():
                    await self._trigger_alert(cumulative_epsilon, timestamp)

                # Логируем для отладки (редко, чтобы не засорять консоль)
                if abs(cumulative_epsilon) > 0.002:
                    logger.info(
                        f"{timestamp.time()} - Cumulative epsilon: {cumulative_epsilon:.6f}"
                    )

        except Exception as e:
            logger.error(f"Error in trade callback: {e}")

    async def _trigger_alert(self, cumulative_epsilon: float, timestamp: datetime):
        """
        Обрабатывает срабатывание оповещения.
        """
        alert_message = (
            f"\n{'=' * 80}\n"
            f"🚨 ALERT: ETH independent movement detected!\n"
            f"Time: {timestamp.isoformat()}\n"
            f"Cumulative epsilon: {cumulative_epsilon:.6f} ({cumulative_epsilon * 100:.2f}%)\n"
            f"Threshold: {self.monitor.threshold * 100:.2f}%\n"
            f"Beta: {self.monitor.beta:.6f}\n"
            f"{'=' * 80}"
        )

        # Выводим в консоль
        print(alert_message)

        # Логируем
        logger.warning(f"Alert triggered: {cumulative_epsilon:.6f}")

    async def _recalculate_beta_periodically(self):
        """Периодически пересчитывает коэффициент beta."""
        while True:
            try:
                # Ждем 24 часа (или из конфига)
                await asyncio.sleep(settings.beta_recalculation_interval)

                logger.info("Starting periodic beta recalculation...")

                # Пересчитываем beta
                new_beta = await initialize_model()

                # Обновляем монитор
                await self._load_and_set_beta()

                logger.info(f"Beta recalculation completed: {new_beta:.6f}")
                print(f"🔄 Beta updated to: {new_beta:.6f}")

            except Exception as e:
                logger.error(f"Beta recalculation failed: {e}")
                # Продолжаем работу даже при ошибке пересчета
                await asyncio.sleep(3600)  # Ждем час перед повторной попыткой

    async def start_monitoring(self):
        """Запускает мониторинг в реальном времени."""
        try:
            await self.initialize()

            # Запускаем фоновую задачу для пересчета beta
            self.beta_recalculation_task = asyncio.create_task(
                self._recalculate_beta_periodically()
            )

            logger.info("Starting real-time monitoring...")
            print("Real-time monitoring active. Press Ctrl+C to stop.")
            print("Waiting for price data...")

            # Подключаемся к WebSocket
            await self.data_fetcher.connect(
                symbols=['btcusdt', 'ethusdt'],
                callback=self.trade_callback
            )

        except asyncio.CancelledError:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Очищает ресурсы."""
        # Отменяем фоновую задачу
        if self.beta_recalculation_task:
            self.beta_recalculation_task.cancel()
            try:
                await self.beta_recalculation_task
            except asyncio.CancelledError:
                pass

        # Закрываем соединения
        if self.data_fetcher:
            await self.data_fetcher.disconnect()
        if self.database:
            await self.database.disconnect()


async def main():
    """Основная функция приложения."""
    monitor = CryptoMonitor()
    await monitor.start_monitoring()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e:
        print(f"Application error: {e}")
        raise