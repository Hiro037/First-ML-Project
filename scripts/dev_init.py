import asyncio

from src.initialize import initialize_model


async def main():
    """Скрипт для ручной инициализации в development."""
    beta = await initialize_model()
    print(f"Development initialization complete. Beta: {beta}")


if __name__ == "__main__":
    asyncio.run(main())
