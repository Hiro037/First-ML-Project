from datetime import datetime

from src.monitor import ResidualMonitor


def test_monitor_basic():
    """Тест базовой функциональности монитора."""
    print("Testing ResidualMonitor basic functionality...")

    # Создаем монитор с тестовым beta
    monitor = ResidualMonitor(beta=1.5, threshold=0.02, window_minutes=3)

    # Симулируем поток данных (цена, время)
    test_data = [
        ("BTCUSDT", 100.0, datetime(2024, 1, 1, 10, 0, 0)),
        ("ETHUSDT", 50.0, datetime(2024, 1, 1, 10, 0, 0)),
        ("BTCUSDT", 101.0, datetime(2024, 1, 1, 10, 0, 30)),  # +1% BTC
        (
            "ETHUSDT",
            53.0,
            datetime(2024, 1, 1, 10, 0, 30),
        ),  # +6% ETH (сильное движение)
    ]

    for symbol, price, timestamp in test_data:
        result = monitor.update_price(symbol, price, timestamp)
        state = monitor.get_current_state()

        print(f"{timestamp.time()} - {symbol}: ${price:.2f}")
        if result is not None:
            print(f"  Cumulative epsilon: {result:.6f}")
            print(
                f"  Window: {state['window_size']}/3, "
                f"Values: {[f'{x:.6f}' for x in state['window_values']]}"
            )

            if monitor.check_alert():
                print("🚨 ALERT TRIGGERED! >2% movement")
        print()


if __name__ == "__main__":
    test_monitor_basic()
