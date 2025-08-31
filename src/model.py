import logging
from typing import Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def calculate_returns(price_series: pd.Series) -> pd.Series:
    """
    Вычисляет логарифмические доходности из ценового ряда.

    Args:
        price_series: Series с ценами закрытия

    Returns:
        Series с логарифмическими доходностями

    Raises:
        ValueError: Если данных недостаточно для расчета
    """
    # Проверяем, что данных достаточно
    if len(price_series) < 2:
        raise ValueError(
            f"Not enough data for returns calculation."
            f" Got {len(price_series)} values, need at least 2."
        )

    # Логарифмические доходности: log(P_t / P_{t-1})
    returns = np.log(price_series / price_series.shift(1))
    # Удаляем первую NaN-запись
    return returns.dropna()


def calculate_beta(
    eth_prices: pd.Series, btc_prices: pd.Series
) -> Tuple[float, pd.Series, pd.Series]:
    """
    Вычисляет коэффициент beta для ETH
    относительно BTC через линейную регрессию.

    Args:
        eth_prices: Series с ценами закрытия ETHUSDT
        btc_prices: Series с ценами закрытия BTCUSDT

    Returns:
        Tuple: (beta_value, eth_returns, btc_returns)
    """
    try:
        # Вычисляем доходности
        eth_returns = calculate_returns(eth_prices)
        btc_returns = calculate_returns(btc_prices)

        # Выравниваем индексы (на случай расхождений во времени)
        aligned_returns = pd.concat(
            [eth_returns, btc_returns], axis=1
        ).dropna()
        eth_aligned = aligned_returns.iloc[:, 0]
        btc_aligned = aligned_returns.iloc[:, 1]

        # Проверяем, что данных достаточно для регрессии
        if len(eth_aligned) < 2:
            raise ValueError("Not enough data for regression")

        # Линейная регрессия:
        # ETH_returns = alpha + beta * BTC_returns + epsilon
        # Используем scipy.stats.linregress для простоты и скорости
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            btc_aligned.values, eth_aligned.values
        )

        # slope - это наш коэффициент beta
        beta_value = slope

        logger.info(
            f"Beta calculation complete: "
            f"beta={beta_value:.6f}, "
            f"R²={r_value ** 2:.4f}, "
            f"p-value={p_value:.2e}, "
            f"n={len(eth_aligned)}"
        )

        return beta_value, eth_aligned, btc_aligned

    except Exception as e:
        logger.error(f"Error calculating beta: {e}")
        raise


def prepare_data_for_regression(
    eth_data: pd.DataFrame, btc_data: pd.DataFrame
) -> Tuple[pd.Series, pd.Series]:
    """
    Подготавливает данные для регрессии, выравнивая временные ряды.

    Args:
        eth_data: DataFrame с данными ETHUSDT
        btc_data: DataFrame с данными BTCUSDT

    Returns:
        Tuple: (eth_prices, btc_prices) с выровненными индексами
    """
    # Берем цены закрытия
    eth_prices = eth_data["close"]
    btc_prices = btc_data["close"]

    # Выравниваем индексы (объединяем и удаляем пропуски)
    aligned_prices = pd.concat(
        [eth_prices, btc_prices], axis=1, keys=["eth", "btc"]
    ).dropna()

    return aligned_prices["eth"], aligned_prices["btc"]
