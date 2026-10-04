import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models


def walk_forward_backtest(price_history, split_ratio=0.7, risk_free_rate=0.02):
    """
    Splits price history into an in-sample (training) window and an
    out-of-sample (testing) window.

    - Optimizes portfolio weights using ONLY the training window.
    - Applies those exact weights to the testing window the optimizer
      never saw, and measures how they actually performed.

    This is the standard way to check whether an optimizer is finding
    a genuinely good allocation, or just fitting noise in the historical
    data it was given (overfitting).
    """
    split_index = int(len(price_history) * split_ratio)
    train_prices = price_history.iloc[:split_index]
    test_prices = price_history.iloc[split_index:]

    # ---- Step 1: optimize using ONLY the training window ----
    mu_train = expected_returns.mean_historical_return(train_prices)
    S_train = risk_models.sample_cov(train_prices)

    ef = EfficientFrontier(mu_train, S_train)
    try:
        ef.max_sharpe(risk_free_rate=risk_free_rate)
    except ValueError:
        ef.min_volatility()  # fallback if max_sharpe isn't feasible in-sample
    weights = np.array(list(ef.clean_weights().values()))

    # ---- Step 2: apply those SAME weights to the unseen test window ----
    test_returns = test_prices.pct_change().dropna()
    portfolio_test_returns = test_returns @ weights

    cumulative = (1 + portfolio_test_returns).cumprod()
    total_return = cumulative.iloc[-1] - 1
    annualized_return = (1 + total_return) ** (252 / len(portfolio_test_returns)) - 1
    annualized_vol = portfolio_test_returns.std() * np.sqrt(252)
    sharpe = (annualized_return - risk_free_rate) / annualized_vol if annualized_vol > 0 else np.nan

    running_max = cumulative.cummax()
    max_drawdown = ((cumulative / running_max) - 1).min()

    return {
        'weights': dict(zip(price_history.columns, weights.round(3))),
        'train_period': (train_prices.index[0], train_prices.index[-1]),
        'test_period': (test_prices.index[0], test_prices.index[-1]),
        'test_total_return': total_return,
        'test_annualized_return': annualized_return,
        'test_annualized_volatility': annualized_vol,
        'test_sharpe': sharpe,
        'test_max_drawdown': max_drawdown,
        'cumulative_growth': cumulative  # for plotting
    }


if __name__ == "__main__":
    from data_loader import fetch_market_data

    tickers = ['AAPL', 'BND', 'GLD']
    prices = fetch_market_data(tickers, '2020-01-01', '2024-09-08')

    result = walk_forward_backtest(prices, split_ratio=0.7)

    print(f"Trained on: {result['train_period'][0].date()} to {result['train_period'][1].date()}")
    print(f"Tested on:  {result['test_period'][0].date()} to {result['test_period'][1].date()}")
    print(f"\nWeights chosen using training data only: {result['weights']}")
    print(f"\n--- Performance on UNSEEN test data ---")
    print(f"Total return: {result['test_total_return']*100:.2f}%")
    print(f"Annualized return: {result['test_annualized_return']*100:.2f}%")
    print(f"Annualized volatility: {result['test_annualized_volatility']*100:.2f}%")
    print(f"Sharpe ratio: {result['test_sharpe']:.2f}")
    print(f"Max drawdown: {result['test_max_drawdown']*100:.2f}%")
    