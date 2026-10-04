import yfinance as yf
import pandas as pd
import numpy as np


def fetch_market_data(tickers, start_date, end_date):
    """
    Fetch historical closing prices for a list of tickers.
    Returns a DataFrame: rows = dates, columns = tickers.
    """
    data = yf.download(tickers, start=start_date, end=end_date, auto_adjust=True)

    # yfinance sometimes nests columns (multi-ticker) or not (single ticker) -
    # this handles both cases cleanly.
    if isinstance(data.columns, pd.MultiIndex):
        prices = data['Close']
    else:
        prices = data[['Close']]
        prices.columns = tickers

    prices = prices.dropna(how='all')       # drop dates with no data at all
    prices = prices.dropna(axis=1, how='all')  # drop tickers that never returned data
    return prices


def calculate_statistics(price_history):
    """
    Turn raw prices into the stats every other module needs:
    - daily % returns
    - annualized mean return per asset
    - annualized volatility per asset
    - correlation matrix between assets
    """
    returns = price_history.pct_change().dropna()

    stats = {
        'mean_returns': returns.mean() * 252,       # annualized
        'volatilities': returns.std() * np.sqrt(252),  # annualized
        'correlation': returns.corr(),
        'returns': returns
    }

    return stats


if __name__ == "__main__":
    # Quick manual test - run this file directly to sanity check it works
    tickers = ['AAPL', 'BND', 'GLD']
    prices = fetch_market_data(tickers, '2023-01-01', '2024-09-08')
    stats = calculate_statistics(prices)

    print("Annualized volatilities:")
    print(stats['volatilities'])
    print("\nAnnualized mean returns:")
    print(stats['mean_returns'])
    print("\nCorrelation matrix:")
    print(stats['correlation'])