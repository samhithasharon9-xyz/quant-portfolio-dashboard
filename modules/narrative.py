import streamlit as st
import google.generativeai as genai


def _configure():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True


def generate_portfolio_narrative(tickers, stats, max_sharpe_weights, min_vol_weights,
                                  rp_weights, currency_label):
    """
    Builds a short plain-English summary of the portfolio analysis by
    feeding the ALREADY-COMPUTED numbers to Gemini and asking it to
    explain them in a few sentences. Gemini isn't doing any math here -
    it's just turning numbers we calculated into a readable narrative.
    """
    if not _configure():
        return (
            "AI narrative unavailable — no GEMINI_API_KEY found in "
            ".streamlit/secrets.toml."
        )

    # Build a compact, factual data summary for the model to describe
    top_asset = stats['mean_returns'].idxmax()
    top_return = stats['mean_returns'].max() * 100
    most_volatile = stats['volatilities'].idxmax()
    most_vol_value = stats['volatilities'].max() * 100

    if max_sharpe_weights is None:
        max_sharpe_str = "not available (no asset beat the risk-free rate over this period)"
    else:
        max_sharpe_str = ", ".join(
            f"{t}: {w*100:.0f}%" for t, w in zip(tickers, max_sharpe_weights)
        )
    min_vol_str = ", ".join(
        f"{t}: {w*100:.0f}%" for t, w in zip(tickers, min_vol_weights)
    )
    rp_str = ", ".join(
        f"{t}: {w*100:.0f}%" for t, w in zip(tickers, rp_weights)
    )

    prompt = f"""You are a financial analyst assistant. Based ONLY on the data below,
write a short, plain-English summary (4-6 sentences, no headers, no bullet points)
of this portfolio analysis for someone who is not a finance expert. Be factual and
avoid giving personalized investment advice or telling the reader what they should do.

Assets analyzed: {', '.join(tickers)} (currency: {currency_label})
Highest expected return: {top_asset} ({top_return:.1f}% annualized)
Most volatile asset: {most_volatile} ({most_vol_value:.1f}% annualized volatility)

Max Sharpe portfolio weights: {max_sharpe_str}
Min Volatility portfolio weights: {min_vol_str}
Risk Parity portfolio weights: {rp_str}

Explain what these allocations suggest about the trade-off between risk and
return in this specific set of assets."""

    model = genai.GenerativeModel("gemini-3.6-flash")
    response = model.generate_content(prompt)
    return response.text