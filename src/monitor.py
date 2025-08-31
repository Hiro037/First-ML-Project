import asyncio
from collections import deque
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ResidualMonitor:
    """Класс для мониторинга собственной доходности ETH в реальном времени."""

    def __init__(self, beta: float, threshold: float = 0.01, window_minutes: int = 60):
        """
        Args:
            beta: Коэффициент beta из модели
            threshold: Порог для оповещения (1% = 0.01)
            window_minutes: Размер окна в минутах (60)
        """
        self.beta = beta
        self.threshold = threshold
        self.window_size = window_minutes

        # Храним последние цены и временные метки
        self.last_prices: Dict[str, Optional[float]] = {
            'BTCUSDT': None,
            'ETHUSDT': None
        }
        self.previous_prices: Dict[str, Optional[float]] = {
            'BTCUSDT': None,
            'ETHUSDT': None
        }

        # Deque для хранения собственной доходности за 60 минут
        self.epsilon_window = deque(maxlen=window_minutes)
        self.current_sum = 0.0  # Текущая сумма за окно

        # Временные метки
        self.current_minute: Optional[int] = None

    def update_price(self, symbol: str, price: float, timestamp: datetime) -> Optional[float]:
        """
        Обновляет цену и вычисляет доходность при наличии данных по обеим парам.

        Returns:
            Текущая накопленная собственная доходность за 60 минут
        """
        # Сохраняем предыдущую цену
        self.previous_prices[symbol] = self.last_prices[symbol]
        self.last_prices[symbol] = price

        # Проверяем, есть ли данные для обеих пар
        if (self.previous_prices['BTCUSDT'] is not None and
                self.previous_prices['ETHUSDT'] is not None and
                self.last_prices['BTCUSDT'] is not None and
                self.last_prices['ETHUSDT'] is not None):
            return self._calculate_epsilon(timestamp)

        return None

    def _calculate_epsilon(self, timestamp: datetime) -> float:
        """
        Вычисляет собственную доходность ETH (epsilon).
        """
        # Вычисляем доходности
        btc_return = np.log(self.last_prices['BTCUSDT'] / self.previous_prices['BTCUSDT'])
        eth_return = np.log(self.last_prices['ETHUSDT'] / self.previous_prices['ETHUSDT'])

        # Собственная доходность: epsilon = eth_return - beta * btc_return
        epsilon = eth_return - (self.beta * btc_return)

        # Обновляем скользящее окно
        self._update_window(epsilon, timestamp)

        return self.current_sum

    def _update_window(self, epsilon: float, timestamp: datetime):
        """
        Обновляет скользящее окно и сумму.
        """
        current_minute = timestamp.minute

        if self.current_minute is None:
            self.current_minute = current_minute

        if current_minute != self.current_minute:
            # Новая минута - добавляем новое значение
            if len(self.epsilon_window) == self.window_size:
                # Удаляем самый старый элемент из суммы
                self.current_sum -= self.epsilon_window[0]

            self.epsilon_window.append(epsilon)
            self.current_sum += epsilon
            self.current_minute = current_minute
        else:
            # Та же минута - обновляем последнее значение
            if self.epsilon_window:
                self.current_sum -= self.epsilon_window[-1]
                self.epsilon_window[-1] = epsilon
                self.current_sum += epsilon
            else:
                self.epsilon_window.append(epsilon)
                self.current_sum += epsilon

    def check_alert(self) -> bool:
        """
        Проверяет, превысила ли собственная доходность порог.

        Returns:
            True если |current_sum| >= threshold
        """
        return abs(self.current_sum) >= self.threshold

    def get_current_state(self) -> Dict:
        """Возвращает текущее состояние монитора."""
        return {
            'current_sum': self.current_sum,
            'window_size': len(self.epsilon_window),
            'window_values': list(self.epsilon_window),
            'threshold': self.threshold,
            'beta': self.beta
        }