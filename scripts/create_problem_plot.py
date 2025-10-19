import asyncio
import matplotlib.pyplot as plt
import pandas as pd
from src.data_fetcher import BinanceDataFetcher


async def main():
    # Загружаем данные за последние 3 дня с 5-минутным интервалом
    async with BinanceDataFetcher() as fetcher:
        eth_data = await fetcher.fetch_historical_data('ETHUSDT', interval='5m', days=3)
        btc_data = await fetcher.fetch_historical_data('BTCUSDT', interval='5m', days=3)

    # Создаем график
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Верхний график - цены
    ax1.plot(eth_data.index, eth_data['close'], label='ETHUSDT', color='blue', linewidth=1)
    ax1.set_ylabel('Цена ETHUSDT (USDT)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Создаем вторую ось Y для BTC
    ax1_btc = ax1.twinx()
    ax1_btc.plot(btc_data.index, btc_data['close'], label='BTCUSDT', color='orange', linewidth=1, alpha=0.7)
    ax1_btc.set_ylabel('Цена BTCUSDT (USDT)', color='orange')
    ax1_btc.tick_params(axis='y', labelcolor='orange')
    ax1_btc.legend(loc='upper right')

    # Нижний график - процентные изменения
    eth_returns = (eth_data['close'].pct_change() * 100).dropna()
    btc_returns = (btc_data['close'].pct_change() * 100).dropna()

    # Выравниваем индексы
    aligned_returns = pd.concat([eth_returns, btc_returns], axis=1).dropna()
    aligned_returns.columns = ['ETH', 'BTC']

    ax2.plot(aligned_returns.index, aligned_returns['ETH'], label='Изменение ETH (%)', color='blue', linewidth=1)
    ax2.plot(aligned_returns.index, aligned_returns['BTC'], label='Изменение BTC (%)', color='orange', linewidth=1,
             alpha=0.7)
    ax2.set_ylabel('Процентное изменение (%)')
    ax2.set_xlabel('Время')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.title('Синхронное движение цен ETHUSDT и BTCUSDT\n(данные за 3 дня, 5-минутный интервал)')
    plt.tight_layout()
    plt.savefig('problem_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()

    print("График сохранен как 'problem_visualization.png'")


if __name__ == "__main__":
    asyncio.run(main())