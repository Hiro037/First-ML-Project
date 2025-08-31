from datetime import datetime

from src.monitor import ResidualMonitor


class TestMonitor:
    """Тесты для класса ResidualMonitor."""

    def test_monitor_initialization(self):
        """Тест инициализации монитора."""
        monitor = ResidualMonitor(beta=1.5, threshold=0.01, window_minutes=60)

        assert monitor.beta == 1.5
        assert monitor.threshold == 0.01
        assert monitor.window_size == 60
        assert monitor.current_sum == 0.0
        assert len(monitor.epsilon_window) == 0

    def test_monitor_update_prices_initial(self):
        """Тест обновления цен при инициализации."""
        monitor = ResidualMonitor(beta=1.5, threshold=0.01, window_minutes=60)

        # Первое обновление - должно вернуть None (недостаточно данных)
        result = monitor.update_price(
            "BTCUSDT", 100.0, datetime(2024, 1, 1, 10, 0)
        )
        assert result is None

        result = monitor.update_price(
            "ETHUSDT", 50.0, datetime(2024, 1, 1, 10, 0)
        )
        assert result is None

    def test_monitor_calculate_epsilon(self):
        """Тест расчета собственной доходности."""
        monitor = ResidualMonitor(beta=1.5, threshold=0.01, window_minutes=60)

        # Устанавливаем начальные цены
        monitor.last_prices = {"BTCUSDT": 100.0, "ETHUSDT": 50.0}
        monitor.previous_prices = {"BTCUSDT": 100.0, "ETHUSDT": 50.0}

        # Обновляем цены (BTC +1%, ETH +2%)
        result = monitor.update_price(
            "BTCUSDT", 101.0, datetime(2024, 1, 1, 10, 1)
        )
        result = monitor.update_price(
            "ETHUSDT", 51.0, datetime(2024, 1, 1, 10, 1)
        )

        # Должен вернуться cumulative epsilon
        assert result is not None

    def test_monitor_alert_condition(self):
        """Тест условия срабатывания оповещения."""
        monitor = ResidualMonitor(beta=1.5, threshold=0.01, window_minutes=3)

        # Симулируем накопление >1%
        monitor.current_sum = 0.015
        assert monitor.check_alert() is True

        # Отрицательное движение >1%
        monitor.current_sum = -0.015
        assert monitor.check_alert() is True

        # Движение <1%
        monitor.current_sum = 0.005
        assert monitor.check_alert() is False

    def test_monitor_window_management(self):
        """Тест управления скользящим окном."""
        monitor = ResidualMonitor(beta=1.5, threshold=0.01, window_minutes=3)

        # Добавляем значения в окно
        test_epsilons = [0.001, 0.002, 0.003]
        for i, epsilon in enumerate(test_epsilons):
            monitor.epsilon_window.append(epsilon)
            monitor.current_sum += epsilon

        assert len(monitor.epsilon_window) == 3
        assert (
            abs(monitor.current_sum - 0.006) < 1e-10
        )  # Исправлено: используем приблизительное сравнение

        # Добавляем четвертое значение - первое должно удалиться
        monitor.epsilon_window.append(0.004)
        monitor.current_sum += 0.004 - test_epsilons[0]

        assert len(monitor.epsilon_window) == 3
        assert (
            abs(monitor.current_sum - 0.009) < 1e-10
        )  # Исправлено: используем приблизительное сравнение
