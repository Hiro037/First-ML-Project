import asyncio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.data_fetcher import BinanceDataFetcher
from src.model import calculate_beta, calculate_returns


async def main():
    # Загружаем данные за последние 7 дней с 5-минутным интервалом
    async with BinanceDataFetcher() as fetcher:
        eth_data = await fetcher.fetch_historical_data('ETHUSDT', interval='5m', days=7)
        btc_data = await fetcher.fetch_historical_data('BTCUSDT', interval='5m', days=7)

    # Вычисляем beta на первых 60 днях (имитация инициализации)
    eth_prices, btc_prices = eth_data['close'], btc_data['close']
    beta_value, eth_returns, btc_returns = calculate_beta(eth_prices, btc_prices)

    print(f"Рассчитанный beta коэффициент: {beta_value:.6f}")

    # Вычисляем epsilon для всего периода
    epsilon_series = eth_returns - (beta_value * btc_returns)

    # Вычисляем накопленную epsilon за 60 минут (12 пятиминуток)
    window_size = 12  # 5min * 12 = 60min
    cumulative_epsilon = epsilon_series.rolling(window=window_size).sum()

    # Создаем график
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Верхний график - цена ETH
    ax1.plot(eth_data.index, eth_data['close'], label='Цена ETHUSDT', color='blue', linewidth=2)
    ax1.set_ylabel('Цена (USDT)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Цена ETHUSDT и независимые движения', fontsize=14, fontweight='bold')

    # Нижний график - накопленная epsilon
    ax2.plot(cumulative_epsilon.index, cumulative_epsilon,
             label='Накопленная Epsilon (60 мин)', color='purple', linewidth=2)

    # Добавляем пороговые линии
    ax2.axhline(y=0.01, color='green', linestyle='--', alpha=0.8, label='Порог +1%')
    ax2.axhline(y=-0.01, color='red', linestyle='--', alpha=0.8, label='Порог -1%')

    # Закрашиваем зоны превышения порогов
    ax2.fill_between(cumulative_epsilon.index, cumulative_epsilon, 0.01,
                     where=(cumulative_epsilon >= 0.01), color='green', alpha=0.3)
    ax2.fill_between(cumulative_epsilon.index, cumulative_epsilon, -0.01,
                     where=(cumulative_epsilon <= -0.01), color='red', alpha=0.3)

    ax2.set_ylabel('Накопленная Epsilon', fontsize=12)
    ax2.set_xlabel('Время', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    #
    # # Добавляем аннотации для значительных движений
    # significant_moves = cumulative_epsilon[np.abs(cumulative_epsilon) >= 0.008]
    # for timestamp, value in significant_moves.items():
    #     color = 'green' if value > 0 else 'red'
    #     ax2.annotate(f'{value:.3f}', xy=(timestamp, value),
    #                  xytext=(10, 30 if value > 0 else -30), textcoords='offset points',
    #                  arrowprops=dict(arrowstyle='->', color=color, alpha=0.7),
    #                  color=color, fontweight='bold')

    plt.tight_layout()
    plt.savefig('algorithm_demo.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Статистика для защиты
    alerts_positive = len(cumulative_epsilon[cumulative_epsilon >= 0.01])
    alerts_negative = len(cumulative_epsilon[cumulative_epsilon <= -0.01])
    total_alerts = alerts_positive + alerts_negative

    print(f"\nСТАТИСТИКА ДЛЯ ЗАЩИТЫ:")
    print(f"Всего сигналов (>1%): {total_alerts}")
    print(f"Положительных сигналов: {alerts_positive}")
    print(f"Отрицательных сигналов: {alerts_negative}")
    print(f"Максимальное движение вверх: {cumulative_epsilon.max():.4f}")
    print(f"Максимальное движение вниз: {cumulative_epsilon.min():.4f}")
    print(f"Средняя абсолютная величина движений: {np.abs(cumulative_epsilon).mean():.4f}")


if __name__ == "__main__":
    asyncio.run(main())