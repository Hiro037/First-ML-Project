import asyncio
import json
from datetime import datetime, timezone
from src.data_fetcher import BinanceDataFetcher


async def trade_callback(message):
    """Пример функции обработки trade сообщений."""
    parsed = BinanceDataFetcher.parse_trade_message(message)
    if parsed:
        print(f"{datetime.now(timezone.utc).isoformat()} - {parsed['symbol']}: "
              f"${parsed['price']:.2f} (Qty: {parsed['quantity']:.4f})")


async def test_websocket():
    """Тестирует WebSocket подключение."""
    print("Testing Binance WebSocket connection...")
    print("Press Ctrl+C to stop")

    fetcher = BinanceDataFetcher()

    try:
        # Подключаемся к WebSocket для BTC и ETH
        await fetcher.connect(
            symbols=['btcusdt', 'ethusdt'],
            callback=trade_callback
        )

    except asyncio.CancelledError:
        print("\nWebSocket test stopped")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await fetcher.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")