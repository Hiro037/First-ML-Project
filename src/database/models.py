from sqlalchemy import MetaData, Table, Column, BigInteger, String, Numeric, DateTime, func, Index

# Рекомендуется явно объявить naming convention для правильной работы с индексами и constraints.
# Это best practice для SQLAlchemy Core.
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

# Определяем таблицу prices
prices = Table(
    "prices",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("symbol", String(20), nullable=False),
    Column("price", Numeric(20, 8), nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    # Индекс для быстрого поиска исторических данных по паре и времени
    Index("ix_prices_symbol_timestamp", "symbol", "timestamp"),
)

# Определяем таблицу betas
betas = Table(
    "betas",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("beta", Numeric(10, 6), nullable=False),  # ЗАМЕНИЛИ Decimal на Numeric
    Column("calculated_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)
