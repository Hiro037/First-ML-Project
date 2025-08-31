from src.initialize import initialize_model


async def main():
    # Инициализируем модель при запуске
    beta = await initialize_model()
    # Дальше запускаем основной цикл с WebSocket
    # ...