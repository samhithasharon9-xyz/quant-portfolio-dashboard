import numpy as np
from scipy.stats import norm


class PortfolioAnalyzer:
    """
    Takes a set of portfolio weights + market stats, and computes
    the standard risk/return metrics for that specific portfolio.
    """

    def __init__(self, weights, mean_returns, volatilities, correlation):
        self.weights = np.array(weights)
        self.mean_returns = mean_returns
        self.volatilities = volatilities
        self.correlation = correlation

        # Covariance matrix: combines correlation + volatility into one
        # matrix the math needs. You don't have to derive this - just
        # know it's "how much two assets move together, in absolute terms."
        self.cov_matrix = correlation * np.outer(volatilities, volatilities)

    def portfolio_return(self):
        """Weighted average of expected returns."""
        return self.weights @ self.mean_returns

    def portfolio_volatility(self):
        """Portfolio-level risk, accounting for how assets move together."""
        return np.sqrt(self.weights @ self.cov_matrix @ self.weights)

    def sharpe_ratio(self, risk_free_rate=0.02):
        """Return earned per unit of risk taken. Higher is better."""
        return (self.portfolio_return() - risk_free_rate) / self.portfolio_volatility()

    def portfolio_beta(self, market_volatility=0.18):
        """
        Simplified beta: how much more/less volatile this portfolio is
        vs. a 'typical market' volatility assumption (~18%/year).
        """
        return self.portfolio_volatility() / market_volatility

    def value_at_risk(self, confidence=0.95):
        """
        95% VaR: the return level you shouldn't do worse than,
        95% of the time. (5% of the time, it could be worse than this.)
        """
        z_score = norm.ppf(1 - confidence)
        return self.portfolio_return() + z_score * self.portfolio_volatility()

    def max_drawdown(self, returns):
        """
        Worst peak-to-trough decline in the actual historical returns.
        `returns` = the portfolio's historical daily return series.
        """
        portfolio_returns = returns @ self.weights
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative / running_max) - 1
        return drawdown.min()

    def correlation_matrix(self):
        return self.correlation


if __name__ == "__main__":
    # Quick manual test using the same data as Phase 2
    from data_loader import fetch_market_data, calculate_statistics

    tickers = ['AAPL', 'BND', 'GLD']
    prices = fetch_market_data(tickers, '2023-01-01', '2024-09-08')
    stats = calculate_statistics(prices)

    weights = np.array([0.4, 0.4, 0.2])  # 40% AAPL, 40% BND, 20% GLD

    analyzer = PortfolioAnalyzer(
        weights,
        stats['mean_returns'],
        stats['volatilities'],
        stats['correlation']
    )

    print(f"Portfolio Return: {analyzer.portfolio_return()*100:.2f}%")
    print(f"Portfolio Volatility: {analyzer.portfolio_volatility()*100:.2f}%")
    print(f"Sharpe Ratio: {analyzer.sharpe_ratio():.2f}")
    print(f"Portfolio Beta: {analyzer.portfolio_beta():.2f}")
    print(f"Value at Risk (95%): {analyzer.value_at_risk()*100:.2f}%")
    print(f"Max Drawdown: {analyzer.max_drawdown(stats['returns'])*100:.2f}%")