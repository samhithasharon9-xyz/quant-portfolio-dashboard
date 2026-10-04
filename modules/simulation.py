import numpy as np
from scipy.optimize import minimize


def risk_parity_weights(volatilities, correlation):
    """
    Risk Parity: instead of maximizing return, spread risk EQUALLY
    across assets. Each asset contributes the same amount of risk
    to the total portfolio, regardless of its expected return.

    This is a genuinely different philosophy from Mean-Variance -
    worth explaining in an interview as "return-agnostic risk balancing."
    """
    n = len(volatilities)
    cov_matrix = correlation * np.outer(volatilities, volatilities)

    def risk_contribution(weights):
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / portfolio_vol
        return risk_contrib

    def objective(weights):
        # Minimize the variance BETWEEN each asset's risk contribution -
        # i.e. push them all toward being equal.
        contribs = risk_contribution(weights)
        target = contribs.mean()
        return np.sum((contribs - target) ** 2)

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0.001, 1) for _ in range(n)]  # small floor avoids divide-by-zero
    initial_guess = np.array([1 / n] * n)

    result = minimize(
        objective, initial_guess,
        method='SLSQP', bounds=bounds, constraints=constraints
    )

    return result.x


def monte_carlo_simulation(mean_returns, cov_matrix, weights,
                            initial_value=10000, days=252, n_simulations=1000):
    """
    Simulate many possible future paths for the portfolio, using random
    daily returns drawn from the historical mean/covariance. This shows
    a RANGE of outcomes rather than one single prediction.
    """
    n_assets = len(weights)
    daily_mean = mean_returns / 252
    daily_cov = cov_matrix / 252

    simulation_results = np.zeros((n_simulations, days))

    for sim in range(n_simulations):
        # Draw correlated random daily returns for all assets at once
        daily_returns = np.random.multivariate_normal(daily_mean, daily_cov, days)
        portfolio_daily_returns = daily_returns @ weights
        cumulative_growth = np.cumprod(1 + portfolio_daily_returns)
        simulation_results[sim] = initial_value * cumulative_growth

    final_values = simulation_results[:, -1]

    summary = {
        'simulations': simulation_results,       # every path, for plotting
        'median_final_value': np.median(final_values),
        'percentile_5': np.percentile(final_values, 5),   # pessimistic case
        'percentile_95': np.percentile(final_values, 95),  # optimistic case
        'probability_of_loss': np.mean(final_values < initial_value)
    }

    return summary


if __name__ == "__main__":
    from data_loader import fetch_market_data, calculate_statistics

    tickers = ['AAPL', 'BND', 'GLD']
    prices = fetch_market_data(tickers, '2023-01-01', '2024-09-08')
    stats = calculate_statistics(prices)

    rp_weights = risk_parity_weights(stats['volatilities'], stats['correlation'])
    print("Risk Parity weights:")
    print(dict(zip(tickers, rp_weights.round(3))))

    cov_matrix = stats['correlation'] * np.outer(stats['volatilities'], stats['volatilities'])
    mc_results = monte_carlo_simulation(
        stats['mean_returns'].values, cov_matrix.values, rp_weights
    )

    print(f"\nMonte Carlo (1 year, $10,000 start):")
    print(f"Median final value: ${mc_results['median_final_value']:,.2f}")
    print(f"5th percentile (bad case): ${mc_results['percentile_5']:,.2f}")
    print(f"95th percentile (good case): ${mc_results['percentile_95']:,.2f}")
    print(f"Probability of loss: {mc_results['probability_of_loss']*100:.1f}%")