import numpy as np
from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns


class MeanVarianceOptimizer:
    """
    Wraps PyPortfolioOpt to find optimal portfolio weights.
    Same concept as hand-rolled scipy optimization - minimize risk
    for a given return target - but PyPortfolioOpt handles the
    constrained-optimization math for us.
    """

    def __init__(self, price_history):
        # PyPortfolioOpt works directly from price history, and computes
        # expected returns / covariance internally using the same
        # annualized-mean / annualized-cov logic we already used manually.
        self.price_history = price_history
        # compounding=False -> simple annualized average, the same measure
        # data_loader.calculate_statistics uses, so every tab agrees.
        self.mu = expected_returns.mean_historical_return(price_history, compounding=False)
        self.S = risk_models.sample_cov(price_history)

    def optimize_min_vol_for_return(self, target_return):
        """Find weights that minimize volatility for a target return."""
        ef = EfficientFrontier(self.mu, self.S)
        ef.efficient_return(target_return)
        weights = ef.clean_weights()
        return np.array(list(weights.values()))

    def max_sharpe_weights(self, risk_free_rate=0.02):
        """Find the single portfolio with the best risk-adjusted return."""
        ef = EfficientFrontier(self.mu, self.S)
        ef.max_sharpe(risk_free_rate=risk_free_rate)
        weights = ef.clean_weights()
        return np.array(list(weights.values()))

    def min_volatility_weights(self):
        """Find the lowest-risk portfolio possible, regardless of return."""
        ef = EfficientFrontier(self.mu, self.S)
        ef.min_volatility()
        weights = ef.clean_weights()
        return np.array(list(weights.values()))

    def efficient_frontier(self, n_points=50):
        """
        Calculate the efficient frontier: for a spread of target returns,
        find the minimum-risk weights at each one.
        """
        min_ret = self.mu.min()
        max_ret = self.mu.max()
        target_returns = np.linspace(min_ret, max_ret, n_points)

        frontier = {'returns': [], 'volatilities': [], 'weights': []}

        for target in target_returns:
            try:
                ef = EfficientFrontier(self.mu, self.S)
                ef.efficient_return(target)
                weights = np.array(list(ef.clean_weights().values()))
                ret, vol, _ = ef.portfolio_performance()

                frontier['returns'].append(ret)
                frontier['volatilities'].append(vol)
                frontier['weights'].append(weights)
            except Exception:
                # Some target returns near the extremes can be infeasible -
                # just skip those points rather than crashing.
                continue

        return frontier


if __name__ == "__main__":
    from data_loader import fetch_market_data

    tickers = ['AAPL', 'BND', 'GLD']
    prices = fetch_market_data(tickers, '2023-01-01', '2024-09-08')

    optimizer = MeanVarianceOptimizer(prices)

    print("Max Sharpe weights:")
    print(dict(zip(tickers, optimizer.max_sharpe_weights().round(3))))

    print("\nMin volatility weights:")
    print(dict(zip(tickers, optimizer.min_volatility_weights().round(3))))

    frontier = optimizer.efficient_frontier(n_points=10)
    print(f"\nEfficient frontier calculated: {len(frontier['returns'])} points")