import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.data_loader import fetch_market_data, calculate_statistics
from modules.portfolio_analyzer import PortfolioAnalyzer
from modules.optimizer import MeanVarianceOptimizer
from modules.simulation import risk_parity_weights, monte_carlo_simulation
from modules.backtester import walk_forward_backtest
from modules.narrative import generate_portfolio_narrative
from modules import ui

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")

st.set_page_config(
    page_title="Quant Portfolio Intelligence",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "📈",
    layout="wide",
)
ui.apply_theme()
ui.render_header(
    "Quant Portfolio Intelligence",
    "Build, stress-test and validate a portfolio of US or Indian assets.",
)

# ---------------- Asset universe for the picker ----------------
US_ASSETS = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "NVDA": "NVIDIA", "JPM": "JPMorgan Chase", "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq-100 ETF", "BND": "Total Bond ETF", "TLT": "Long Treasury ETF",
    "GLD": "Gold ETF",
}
INDIA_ASSETS = {
    "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank", "INFY.NS": "Infosys", "ICICIBANK.NS": "ICICI Bank",
    "ITC.NS": "ITC", "NIFTYBEES.NS": "Nifty 50 ETF", "GOLDBEES.NS": "Gold ETF (India)",
}
ALL_NAMES = {**US_ASSETS, **INDIA_ASSETS}
DEFAULTS = {"US": ["AAPL", "BND", "GLD"], "India": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]}


def asset_label(ticker):
    name = ALL_NAMES.get(ticker)
    return f"{name} ({ticker})" if name else ticker


def detect_currency(ticker_list):
    """NSE tickers end in .NS and trade in INR; everything else defaults to USD."""
    return {"INR" if t.endswith(".NS") else "USD" for t in ticker_list}


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### Portfolio setup")

    market = st.segmented_control("Market", ["US", "India"], default="US") or "US"
    universe = US_ASSETS if market == "US" else INDIA_ASSETS

    selected = st.multiselect(
        "Assets",
        options=list(universe.keys()),
        default=DEFAULTS[market],
        format_func=asset_label,
        accept_new_options=True,
        max_selections=10,
        placeholder="Add an asset or type a ticker",
        help="Pick from the list or type any Yahoo Finance ticker. "
             "Indian stocks end in .NS, e.g. TATAMOTORS.NS",
    )
    tickers = list(dict.fromkeys(t.strip().upper() for t in selected if t.strip()))

    currencies_used = detect_currency(tickers)
    currency_symbol = "₹" if currencies_used == {"INR"} else "$"

    years_back = st.slider("Years of history", 1, 10, 3)
    start_date = (datetime.now() - timedelta(days=years_back * 365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    default_rf = 7.0 if currency_symbol == "₹" else 2.0
    with st.expander("Advanced settings", icon=":material/tune:"):
        risk_free_pct = st.number_input(
            "Risk-free rate (%)", value=default_rf, step=0.25,
            help="About 7% for India (10-year G-Sec), 2-4% for the US (Treasury bills).",
        )
    risk_free_rate = risk_free_pct / 100

    run_button = st.button("Run analysis", type="primary", icon=":material/play_arrow:", width="stretch")

    st.divider()
    st.caption("Built with Python, Streamlit, PyPortfolioOpt, Plotly and Google Gemini.")

if run_button:
    st.session_state.analysis_run = True

if not st.session_state.get("analysis_run"):
    st.info("Choose your assets in the sidebar, then select **Run analysis**.")
    st.stop()

if len(tickers) < 2:
    st.warning("Select at least two assets to build a portfolio.")
    st.stop()


# ---------------- DATA ----------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(tickers, start_date, end_date):
    prices = fetch_market_data(list(tickers), start_date, end_date)
    stats = calculate_statistics(prices)
    return prices, stats


with st.spinner("Downloading market data..."):
    try:
        prices, stats = load_data(tuple(tickers), start_date, end_date)
    except Exception as e:
        st.error(f"Couldn't download prices for {', '.join(tickers)}. Check the tickers and try again. ({e})")
        st.stop()

if prices.empty:
    st.error("No price data came back for these tickers. Check the symbols and try again.")
    st.stop()

missing_tickers = [t for t in tickers if t not in prices.columns]
if missing_tickers:
    st.warning(f"No usable data for {', '.join(missing_tickers)}. Left out of this analysis.")
tickers = list(prices.columns)

if len(tickers) < 2:
    st.error("At least two assets need price data to build a portfolio.")
    st.stop()

if len(currencies_used) > 1:
    st.warning(
        "You've mixed US and Indian assets. Returns, risk and optimization are still valid "
        "because they're based on percentage moves, but money values in Scenarios use one currency label."
    )


# ---------------- ANALYTICS (computed once, used by every tab) ----------------
returns = stats["returns"]
mean_returns = stats["mean_returns"].reindex(tickers)
volatilities = stats["volatilities"].reindex(tickers)
cov_matrix = stats["correlation"] * np.outer(stats["volatilities"], stats["volatilities"])


def analyze(weights):
    return PortfolioAnalyzer(weights, stats["mean_returns"], stats["volatilities"], stats["correlation"])


def pct(x):
    return f"{x * 100:.2f}%"


def money(x):
    return f"{currency_symbol}{x:,.0f}"


def portfolio_metrics(analyzer):
    c = st.columns(3)
    c[0].metric("Expected return", pct(analyzer.portfolio_return()))
    c[1].metric("Volatility", pct(analyzer.portfolio_volatility()))
    c[2].metric("Sharpe ratio", f"{analyzer.sharpe_ratio(risk_free_rate=risk_free_rate):.2f}")


optimizer = MeanVarianceOptimizer(prices)
sharpe_message = None
try:
    max_sharpe_w = optimizer.max_sharpe_weights(risk_free_rate=risk_free_rate)
except Exception as e:
    max_sharpe_w = None
    if "risk-free" in str(e):
        sharpe_message = (
            f"No asset beat the {risk_free_pct:.2f}% risk-free rate over this period, so a maximum "
            "Sharpe portfolio doesn't exist. Try a longer history or a lower rate in Advanced settings."
        )
    else:
        sharpe_message = f"The maximum Sharpe optimization didn't converge for these assets. ({e})"

min_vol_w = optimizer.min_volatility_weights()
rp_weights = risk_parity_weights(stats["volatilities"], stats["correlation"])

ms = analyze(max_sharpe_w) if max_sharpe_w is not None else None
mv = analyze(min_vol_w)
rp = analyze(rp_weights)


# ---------------- TABS ----------------
tab_overview, tab_opt, tab_rp, tab_sim, tab_bt, tab_brief = st.tabs(
    ["Overview", "Optimization", "Risk parity", "Scenarios", "Backtest", "Analyst brief"]
)

# ===== OVERVIEW =====
with tab_overview:
    st.subheader("Performance", anchor=False)
    st.caption("Growth of 100 invested in each asset at the start of the period, so assets with very different prices compare directly.")

    rebased = prices / prices.bfill().iloc[0] * 100
    perf = go.Figure()
    for i, t in enumerate(rebased.columns):
        perf.add_trace(go.Scatter(
            x=rebased.index, y=rebased[t], name=t, mode="lines", connectgaps=True,
            line=dict(width=2.2, color=ui.SERIES_COLORS[i % len(ui.SERIES_COLORS)]),
            hovertemplate=f"{t}: %{{y:.1f}}<extra></extra>",
        ))
    perf.add_hline(y=100, line=dict(color=ui.TAUPE, width=1, dash="dot"))
    ui.style_fig(perf, height=430, y_title="Value of 100 invested")
    perf.update_layout(hovermode="x unified")
    ui.show_chart(perf, key="perf", zoomable=True)

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.subheader("Correlation", anchor=False)
        st.caption("How closely each pair moves together. Lower numbers mean more diversification.")
        corr = stats["correlation"]
        heat = go.Figure(go.Heatmap(
            z=corr.values, x=list(corr.columns), y=list(corr.index),
            zmin=-1, zmax=1, colorscale=ui.CORR_SCALE, xgap=4, ygap=4,
            texttemplate="%{z:.2f}",
            textfont=dict(family="IBM Plex Mono, monospace", size=14, color=ui.CREAM),
            colorbar=dict(thickness=10, outlinewidth=0, len=0.85, tickfont=dict(color=ui.TAUPE)),
            hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>",
        ))
        ui.style_fig(heat, height=380, show_legend=False)
        heat.update_xaxes(showgrid=False)
        heat.update_yaxes(showgrid=False, autorange="reversed")
        ui.show_chart(heat, key="corr")

    with right:
        st.subheader("Asset statistics", anchor=False)
        st.caption("Annualized from daily returns over the selected period.")
        asset_df = pd.DataFrame({
            "Name": [ALL_NAMES.get(t, t) for t in tickers],
            "Return": mean_returns.values * 100,
            "Volatility": volatilities.values * 100,
            "Return / risk": (mean_returns / volatilities).values,
        }, index=tickers)
        st.dataframe(
            asset_df, width="stretch",
            column_config={
                "Return": st.column_config.NumberColumn(format="%.2f%%"),
                "Volatility": st.column_config.NumberColumn(format="%.2f%%"),
                "Return / risk": st.column_config.NumberColumn(format="%.2f"),
            },
        )

# ===== OPTIMIZATION =====
with tab_opt:
    st.subheader("Optimal allocations", anchor=False)
    st.caption("Mean-variance optimization (Markowitz) finds the mix of these assets with the best trade-off between expected return and volatility.")
    if sharpe_message:
        st.warning(sharpe_message)

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("#### Maximum Sharpe")
        st.caption("The highest return earned per unit of risk.")
        if ms is not None:
            portfolio_metrics(ms)
            ui.show_chart(ui.weights_chart(max_sharpe_w, tickers, ui.SAND), key="w_ms")
        else:
            st.info("Not available for this period and risk-free rate.")
    with col_b:
        st.markdown("#### Minimum variance")
        st.caption("The calmest mix these assets allow.")
        portfolio_metrics(mv)
        ui.show_chart(ui.weights_chart(min_vol_w, tickers, ui.TAUPE), key="w_mv")

    st.subheader("Efficient frontier", anchor=False)
    st.caption("Each point on the curve is the lowest-risk portfolio for its level of return. Anything below the curve is a worse deal.")

    frontier = optimizer.efficient_frontier(n_points=40)
    ef = go.Figure()
    ef.add_trace(go.Scatter(
        x=np.array(frontier["volatilities"]) * 100, y=np.array(frontier["returns"]) * 100,
        mode="lines", name="Efficient frontier", line=dict(color=ui.SAND, width=3),
        hovertemplate="Volatility %{x:.2f}%<br>Return %{y:.2f}%<extra></extra>",
    ))
    ef.add_trace(go.Scatter(
        x=volatilities.values * 100, y=mean_returns.values * 100,
        mode="markers+text", name="Individual assets", text=tickers,
        textposition="top center", textfont=dict(color=ui.TAUPE),
        marker=dict(color=ui.TAUPE, size=9),
        hovertemplate="%{text}<br>Volatility %{x:.2f}%<br>Return %{y:.2f}%<extra></extra>",
    ))
    for name, analyzer, color, symbol, size in [
        ("Maximum Sharpe", ms, ui.NEON, "star", 18),
        ("Minimum variance", mv, ui.CREAM, "diamond", 13),
        ("Risk parity", rp, ui.BURGUNDY_TINT, "square", 12),
    ]:
        if analyzer is None:
            continue
        ef.add_trace(go.Scatter(
            x=[analyzer.portfolio_volatility() * 100], y=[analyzer.portfolio_return() * 100],
            mode="markers", name=name,
            marker=dict(color=color, size=size, symbol=symbol, line=dict(color=ui.PAGE_BG, width=1.5)),
            hovertemplate=f"{name}<br>Volatility %{{x:.2f}}%<br>Return %{{y:.2f}}%<extra></extra>",
        ))
    ui.style_fig(ef, height=470, x_title="Volatility (%)", y_title="Expected return (%)")
    ui.show_chart(ef, key="frontier", zoomable=True)

# ===== RISK PARITY =====
with tab_rp:
    st.subheader("Equal risk contribution", anchor=False)
    st.caption("Risk parity sizes each position so every asset contributes the same share of total portfolio risk, whatever its expected return.")

    c = st.columns(4)
    c[0].metric("Expected return", pct(rp.portfolio_return()))
    c[1].metric("Volatility", pct(rp.portfolio_volatility()))
    c[2].metric("Sharpe ratio", f"{rp.sharpe_ratio(risk_free_rate=risk_free_rate):.2f}")
    c[3].metric("Max drawdown", pct(rp.max_drawdown(returns)))

    cov = cov_matrix.values
    risk_share = rp_weights * (cov @ rp_weights) / (rp_weights @ cov @ rp_weights)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### Capital allocation")
        st.caption("Share of money in each asset.")
        ui.show_chart(ui.weights_chart(rp_weights, tickers, ui.SAND), key="w_rp")
    with right:
        st.markdown("#### Risk contribution")
        st.caption("Share of total risk from each asset. Near-equal bars confirm the method worked.")
        ui.show_chart(ui.weights_chart(risk_share, tickers, ui.BURGUNDY_TINT), key="rc_rp")

# ===== SCENARIOS (MONTE CARLO) =====
with tab_sim:
    st.subheader("Forward scenarios", anchor=False)
    st.caption("Monte Carlo simulation: 1,000 possible one-year paths for the risk parity portfolio, generated from these assets' historical returns and correlations.")

    initial_value = st.number_input(
        f"Starting value ({currency_symbol})", min_value=1000,
        value=100000 if currency_symbol == "₹" else 10000, step=1000,
    )

    np.random.seed(42)  # same scenarios on every rerun, so numbers don't jump around
    mc = monte_carlo_simulation(
        stats["mean_returns"].values, cov_matrix.values, rp_weights, initial_value=initial_value
    )

    c = st.columns(4)
    c[0].metric("Median outcome", money(mc["median_final_value"]))
    c[1].metric("Weak year (5th percentile)", money(mc["percentile_5"]))
    c[2].metric("Strong year (95th percentile)", money(mc["percentile_95"]))
    c[3].metric("Chance of a loss", f"{mc['probability_of_loss'] * 100:.1f}%")

    sims = mc["simulations"]
    days = np.arange(sims.shape[1])
    p5, p50, p95 = np.percentile(sims, [5, 50, 95], axis=0)

    # 60 sample paths drawn as one trace (NaN breaks between paths) - lighter and faster
    sample = sims[:60]
    x_paths = np.tile(np.append(days, np.nan), len(sample))
    y_paths = np.concatenate([np.append(path, np.nan) for path in sample])

    sim_fig = go.Figure()
    sim_fig.add_trace(go.Scatter(
        x=x_paths, y=y_paths, mode="lines", name="Sample paths",
        line=dict(color=ui.TAUPE, width=1.1), opacity=0.3, hoverinfo="skip",
    ))
    sim_fig.add_trace(go.Scatter(
        x=days, y=p95, mode="lines", name="95th percentile",
        line=dict(color=ui.SAND, width=2.4, dash="dash"),
        hovertemplate=f"95th: {currency_symbol}%{{y:,.0f}}<extra></extra>",
    ))
    sim_fig.add_trace(go.Scatter(
        x=days, y=p5, mode="lines", name="5th percentile",
        line=dict(color=ui.BURGUNDY_TINT, width=2.4, dash="dash"),
        fill="tonexty", fillcolor="rgba(172, 156, 141, 0.10)",
        hovertemplate=f"5th: {currency_symbol}%{{y:,.0f}}<extra></extra>",
    ))
    sim_fig.add_trace(go.Scatter(
        x=days, y=p50, mode="lines", name="Median",
        line=dict(color=ui.NEON, width=3),
        hovertemplate=f"Median: {currency_symbol}%{{y:,.0f}}<extra></extra>",
    ))
    sim_fig.add_hline(y=initial_value, line=dict(color=ui.CREAM, width=1, dash="dot"), opacity=0.5)
    ui.style_fig(sim_fig, height=470, x_title="Trading day", y_title=f"Portfolio value ({currency_symbol})")
    sim_fig.update_layout(hovermode="x unified")
    ui.show_chart(sim_fig, key="sim", zoomable=True)

# ===== BACKTEST =====
with tab_bt:
    st.subheader("Out-of-sample test", anchor=False)
    st.caption("Walk-forward validation: weights are chosen using only the earlier part of the history, then held unchanged through a later period the optimizer never saw.")

    split_pct = st.slider("Share of history used for training", 50, 90, 70, format="%d%%")

    try:
        bt = walk_forward_backtest(prices, split_ratio=split_pct / 100, risk_free_rate=risk_free_rate)
    except Exception as e:
        st.error(f"The backtest needs more data in both windows. Increase Years of history in the sidebar and run again. ({e})")
    else:
        tr0, tr1 = bt["train_period"]
        te0, te1 = bt["test_period"]
        st.markdown(
            f"Trained on **{tr0:%d %b %Y} to {tr1:%d %b %Y}**, "
            f"tested on **{te0:%d %b %Y} to {te1:%d %b %Y}**."
        )

        c = st.columns(4)
        c[0].metric("Annualized return", pct(bt["test_annualized_return"]))
        c[1].metric("Volatility", pct(bt["test_annualized_volatility"]))
        c[2].metric("Sharpe ratio", f"{bt['test_sharpe']:.2f}")
        c[3].metric("Max drawdown", pct(bt["test_max_drawdown"]))

        strategy = bt["cumulative_growth"]
        test_returns = prices.loc[te0:].pct_change().dropna()
        benchmark = (1 + test_returns.mean(axis=1)).cumprod()

        left, right = st.columns([2, 1], gap="large")
        with left:
            st.markdown("#### Growth on unseen data")
            bt_fig = go.Figure()
            bt_fig.add_trace(go.Scatter(
                x=benchmark.index, y=benchmark.values, mode="lines", name="Equal-weight benchmark",
                line=dict(color=ui.TAUPE, width=2, dash="dash"),
                hovertemplate="Equal weight: %{y:.3f}x<extra></extra>",
            ))
            bt_fig.add_trace(go.Scatter(
                x=strategy.index, y=strategy.values, mode="lines", name="Optimized portfolio",
                line=dict(color=ui.NEON, width=2.6),
                hovertemplate="Optimized: %{y:.3f}x<extra></extra>",
            ))
            bt_fig.add_hline(y=1, line=dict(color=ui.CREAM, width=1, dash="dot"), opacity=0.5)
            ui.style_fig(bt_fig, height=400, y_title="Growth of 1 invested")
            bt_fig.update_layout(hovermode="x unified")
            ui.show_chart(bt_fig, key="bt", zoomable=True)
            st.caption(
                f"Optimized portfolio: {pct(strategy.iloc[-1] - 1)} total return, versus "
                f"{pct(benchmark.iloc[-1] - 1)} for an equal-weight mix of the same assets."
            )
        with right:
            st.markdown("#### Weights from training data")
            ui.show_chart(
                ui.weights_chart(list(bt["weights"].values()), list(bt["weights"].keys()), ui.SAND),
                key="w_bt",
            )

# ===== ANALYST BRIEF (GEMINI) =====
with tab_brief:
    st.subheader("Analyst brief", anchor=False)
    st.caption("A plain-English reading of the results, written by Google Gemini. The model only describes figures this dashboard has already calculated.")

    brief_key = (tuple(tickers), start_date, round(risk_free_rate, 4))

    if st.button("Write brief", icon=":material/edit_note:"):
        with st.spinner("Writing brief..."):
            try:
                text = generate_portfolio_narrative(
                    tickers, stats,
                    max_sharpe_w,
                    min_vol_w, rp_weights,
                    "INR" if currency_symbol == "₹" else "USD",
                )
                st.session_state["brief"] = (brief_key, text)
            except Exception as e:
                st.error(f"Gemini didn't return a brief. Check GEMINI_API_KEY in .streamlit/secrets.toml and try again. ({e})")

    saved = st.session_state.get("brief")
    if saved and saved[0] == brief_key:
        with st.container(border=True):
            st.markdown(saved[1])
    else:
        st.info("Select **Write brief** to get commentary on the current portfolio.")