import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.model import calculate_returns, calculate_beta, prepare_data_for_regression


class TestModel:
    """Тесты для функций расчета модели."""

    def test_calculate_returns_basic(self):
        """Тест расчета доходностей на простых данных."""
        # Создаем простой ценовой ряд
        prices = pd.Series([100, 101, 102.5, 100.8])

        # Рассчитываем доходности
        returns = calculate_returns(prices)

        # Ожидаемые результаты вручную
        expected_values = [
            np.log(101 / 100),  # log(101/100)
            np.log(102.5 / 101),  # log(102.5/101)
            np.log(100.8 / 102.5)  # log(100.8/102.5)
        ]

        # Проверяем значения, а не индексы
        np.testing.assert_array_almost_equal(returns.values, expected_values)
        assert len(returns) == 3

    def test_calculate_returns_empty(self):
        """Тест с пустыми данными."""
        with pytest.raises(ValueError):
            calculate_returns(pd.Series([]))

    def test_calculate_returns_single_value(self):
        """Тест с одним значением."""
        with pytest.raises(ValueError):
            calculate_returns(pd.Series([100]))

    def test_prepare_data_for_regression(self):
        """Тест подготовки данных для регрессии."""
        # Создаем тестовые данные с разными индексами
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        eth_prices = pd.Series([100, 101, 102, 103, 104], index=dates)
        btc_prices = pd.Series([200, 201, 202, 203, 204], index=dates)

        # Вызываем функцию
        eth_prepared, btc_prepared = prepare_data_for_regression(
            pd.DataFrame({'close': eth_prices}),
            pd.DataFrame({'close': btc_prices})
        )

        # Проверяем результаты
        assert len(eth_prepared) == 5
        assert len(btc_prepared) == 5
        assert eth_prepared.index.equals(btc_prepared.index)
        assert eth_prepared.iloc[0] == 100
        assert btc_prepared.iloc[0] == 200

    def test_prepare_data_mismatched_indexes(self):
        """Тест с несовпадающими индексами."""
        dates1 = pd.date_range('2024-01-01', periods=3, freq='D')
        dates2 = pd.date_range('2024-01-02', periods=3, freq='D')  # Сдвинутые даты

        eth_prices = pd.Series([100, 101, 102], index=dates1)
        btc_prices = pd.Series([200, 201, 202], index=dates2)

        eth_prepared, btc_prepared = prepare_data_for_regression(
            pd.DataFrame({'close': eth_prices}),
            pd.DataFrame({'close': btc_prices})
        )

        # Должны остаться только совпадающие даты
        assert len(eth_prepared) == 2
        assert len(btc_prepared) == 2

    def test_calculate_beta_perfect_correlation(self):
        """Тест расчета beta при perfect correlation."""
        # Создаем идеально коррелированные данные
        np.random.seed(42)  # Для воспроизводимости
        btc_returns = pd.Series(np.random.normal(0, 0.01, 1000))
        eth_returns = 1.5 * btc_returns  # Идеальная корреляция с beta=1.5

        # Создаем фиктивные ценовые ряды
        eth_prices = pd.Series(np.exp(eth_returns.cumsum()))
        btc_prices = pd.Series(np.exp(btc_returns.cumsum()))

        # Рассчитываем beta
        beta_value, eth_calc, btc_calc = calculate_beta(eth_prices, btc_prices)

        # Проверяем результаты
        assert abs(beta_value - 1.5) < 0.001  # Должно быть очень близко к 1.5
        assert len(eth_calc) == len(btc_calc) == 999  # Из-за расчета доходностей

    def test_calculate_beta_no_correlation(self):
        """Тест расчета beta при отсутствии корреляции."""
        # Создаем некоррелированные данные
        np.random.seed(42)
        btc_returns = pd.Series(np.random.normal(0, 0.01, 1000))
        eth_returns = pd.Series(np.random.normal(0, 0.01, 1000))  # Независимые данные

        eth_prices = pd.Series(np.exp(eth_returns.cumsum()))
        btc_prices = pd.Series(np.exp(btc_returns.cumsum()))

        beta_value, _, _ = calculate_beta(eth_prices, btc_prices)

        # Beta должна быть близка к 0 при отсутствии корреляции
        assert abs(beta_value) < 0.1

    def test_calculate_beta_negative_correlation(self):
        """Тест расчета beta при отрицательной корреляции."""
        np.random.seed(42)
        btc_returns = pd.Series(np.random.normal(0, 0.01, 1000))
        eth_returns = -0.8 * btc_returns  # Отрицательная корреляция

        eth_prices = pd.Series(np.exp(eth_returns.cumsum()))
        btc_prices = pd.Series(np.exp(btc_returns.cumsum()))

        beta_value, _, _ = calculate_beta(eth_prices, btc_prices)

        assert abs(beta_value + 0.8) < 0.01

    def test_calculate_beta_insufficient_data(self):
        """Тест с недостаточным количеством данных."""
        with pytest.raises(ValueError):
            calculate_beta(pd.Series([100, 101]), pd.Series([200, 201]))