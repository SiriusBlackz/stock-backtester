#!/usr/bin/env python3
"""
Stock Backtester with Moving Average Crossover Strategy

Fetches historical data and simulates a simple MA crossover trading strategy.
"""

import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf


def fetch_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch historical daily data for a given ticker."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    if df.empty:
        raise ValueError(f"No data found for ticker: {ticker}")
    return df


def calculate_moving_averages(df: pd.DataFrame, short_window: int = 20, long_window: int = 50) -> pd.DataFrame:
    """Calculate short and long moving averages."""
    df = df.copy()
    df["SMA_Short"] = df["Close"].rolling(window=short_window).mean()
    df["SMA_Long"] = df["Close"].rolling(window=long_window).mean()
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Generate buy/sell signals based on MA crossover."""
    df = df.copy()
    df["Signal"] = 0

    # 1 = buy signal (short crosses above long)
    # -1 = sell signal (short crosses below long)
    df.loc[df["SMA_Short"] > df["SMA_Long"], "Signal"] = 1
    df.loc[df["SMA_Short"] <= df["SMA_Long"], "Signal"] = -1

    # Detect crossover points (signal changes)
    df["Position"] = df["Signal"].diff()

    return df


def simulate_trades(df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Simulate trades based on signals and calculate performance metrics.

    Returns a dictionary with trade history and metrics.
    """
    df = df.dropna().copy()

    capital = initial_capital
    shares = 0
    trades = []
    portfolio_values = []

    in_position = False
    entry_price = 0
    entry_date = None

    for date, row in df.iterrows():
        current_price = row["Close"]

        # Calculate current portfolio value
        portfolio_value = capital + (shares * current_price)
        portfolio_values.append({"Date": date, "Value": portfolio_value})

        # Buy signal: Position == 2 means signal changed from -1 to 1
        if row["Position"] == 2 and not in_position:
            shares = capital // current_price
            if shares > 0:
                cost = shares * current_price
                capital -= cost
                in_position = True
                entry_price = current_price
                entry_date = date
                trades.append({
                    "Type": "BUY",
                    "Date": date,
                    "Price": current_price,
                    "Shares": shares
                })

        # Sell signal: Position == -2 means signal changed from 1 to -1
        elif row["Position"] == -2 and in_position:
            revenue = shares * current_price
            capital += revenue
            profit = (current_price - entry_price) * shares
            profit_pct = (current_price - entry_price) / entry_price * 100

            trades.append({
                "Type": "SELL",
                "Date": date,
                "Price": current_price,
                "Shares": shares,
                "Profit": profit,
                "Profit_Pct": profit_pct
            })

            shares = 0
            in_position = False
            entry_price = 0
            entry_date = None

    # Calculate final portfolio value
    final_price = df.iloc[-1]["Close"]
    final_value = capital + (shares * final_price)

    # If still in position, calculate unrealized P&L
    if in_position:
        unrealized_profit = (final_price - entry_price) * shares
        unrealized_pct = (final_price - entry_price) / entry_price * 100
    else:
        unrealized_profit = 0
        unrealized_pct = 0

    portfolio_df = pd.DataFrame(portfolio_values)

    return {
        "trades": trades,
        "portfolio_df": portfolio_df,
        "final_value": final_value,
        "initial_capital": initial_capital,
        "shares_held": shares,
        "cash": capital,
        "in_position": in_position,
        "unrealized_profit": unrealized_profit,
        "unrealized_pct": unrealized_pct
    }


def calculate_metrics(results: dict) -> dict:
    """Calculate performance metrics from trade results."""
    trades = results["trades"]
    portfolio_df = results["portfolio_df"]
    initial_capital = results["initial_capital"]
    final_value = results["final_value"]

    # Total return
    total_return = (final_value - initial_capital) / initial_capital * 100

    # Count trades (round trips)
    sell_trades = [t for t in trades if t["Type"] == "SELL"]
    num_trades = len(sell_trades)

    # Win rate
    if num_trades > 0:
        winning_trades = len([t for t in sell_trades if t["Profit"] > 0])
        win_rate = winning_trades / num_trades * 100
    else:
        win_rate = 0

    # Max drawdown
    if not portfolio_df.empty:
        portfolio_df["Peak"] = portfolio_df["Value"].cummax()
        portfolio_df["Drawdown"] = (portfolio_df["Value"] - portfolio_df["Peak"]) / portfolio_df["Peak"] * 100
        max_drawdown = portfolio_df["Drawdown"].min()
    else:
        max_drawdown = 0

    return {
        "total_return": total_return,
        "num_trades": num_trades,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "final_value": final_value,
        "initial_capital": initial_capital
    }


def calculate_buy_and_hold(df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """Calculate buy-and-hold performance metrics."""
    start_price = df.iloc[0]["Close"]
    end_price = df.iloc[-1]["Close"]

    # Buy as many shares as possible on day 1
    shares = initial_capital // start_price
    cost = shares * start_price
    remaining_cash = initial_capital - cost

    # Final value
    final_value = (shares * end_price) + remaining_cash
    total_return = (final_value - initial_capital) / initial_capital * 100

    # Calculate max drawdown for buy-and-hold
    portfolio_values = (shares * df["Close"]) + remaining_cash
    peak = portfolio_values.cummax()
    drawdown = (portfolio_values - peak) / peak * 100
    max_drawdown = drawdown.min()

    return {
        "start_price": start_price,
        "end_price": end_price,
        "shares": shares,
        "initial_capital": initial_capital,
        "final_value": final_value,
        "total_return": total_return,
        "max_drawdown": max_drawdown
    }


def print_summary(ticker: str, metrics: dict, results: dict, buy_hold: dict, short_window: int, long_window: int):
    """Print a formatted summary of backtest results with buy-and-hold comparison."""
    print("\n" + "=" * 70)
    print(f"  BACKTEST RESULTS: {ticker}")
    print("=" * 70)

    # Side-by-side comparison header
    strategy_name = f"MA Crossover ({short_window}/{long_window})"
    print(f"\n  {'Metric':<20} {strategy_name:>22} {'Buy & Hold':>22}")
    print("  " + "-" * 66)

    # Initial capital
    print(f"  {'Initial Capital':<20} ${metrics['initial_capital']:>20,.2f} ${buy_hold['initial_capital']:>20,.2f}")

    # Final value
    print(f"  {'Final Value':<20} ${metrics['final_value']:>20,.2f} ${buy_hold['final_value']:>20,.2f}")

    # Total return with color indicator
    strat_ret = metrics['total_return']
    bh_ret = buy_hold['total_return']
    diff = strat_ret - bh_ret
    print(f"  {'Total Return':<20} {strat_ret:>21.2f}% {bh_ret:>21.2f}%")

    # Max drawdown
    print(f"  {'Max Drawdown':<20} {metrics['max_drawdown']:>21.2f}% {buy_hold['max_drawdown']:>21.2f}%")

    # Strategy-specific metrics
    print(f"\n  {'Strategy Metrics':<20}")
    print("  " + "-" * 66)
    print(f"  {'Number of Trades':<20} {metrics['num_trades']:>22}")
    print(f"  {'Win Rate':<20} {metrics['win_rate']:>21.1f}%")

    if results["in_position"]:
        print(f"  {'Currently Holding':<20} {results['shares_held']:>18} shares")
        print(f"  {'Unrealized P&L':<20} ${results['unrealized_profit']:>15,.2f} ({results['unrealized_pct']:+.2f}%)")

    # Performance comparison
    print(f"\n  " + "-" * 66)
    if diff > 0:
        print(f"  Strategy OUTPERFORMED buy-and-hold by {diff:+.2f}%")
    elif diff < 0:
        print(f"  Strategy UNDERPERFORMED buy-and-hold by {diff:.2f}%")
    else:
        print(f"  Strategy performed EQUAL to buy-and-hold")

    # Buy and hold details
    print(f"\n  Buy & Hold: Bought {buy_hold['shares']:.0f} shares @ ${buy_hold['start_price']:.2f}, "
          f"now worth ${buy_hold['end_price']:.2f}/share")

    print("\n" + "-" * 70)
    print("  TRADE HISTORY")
    print("-" * 70)

    trades = results["trades"]
    if trades:
        for trade in trades:
            date_str = trade["Date"].strftime("%Y-%m-%d")
            if trade["Type"] == "BUY":
                print(f"  {date_str}  BUY   {trade['Shares']:>4} shares @ ${trade['Price']:.2f}")
            else:
                print(f"  {date_str}  SELL  {trade['Shares']:>4} shares @ ${trade['Price']:.2f}  "
                      f"P&L: ${trade['Profit']:+,.2f} ({trade['Profit_Pct']:+.2f}%)")
    else:
        print("  No trades executed.")

    print("=" * 70 + "\n")


def run_backtest(ticker: str = "AAPL", short_window: int = 20, long_window: int = 50,
                 initial_capital: float = 10000.0):
    """Run the complete backtest pipeline."""
    print(f"\nFetching 1 year of data for {ticker}...")
    df = fetch_data(ticker)
    print(f"Retrieved {len(df)} trading days of data.")

    # Calculate buy-and-hold benchmark
    buy_hold = calculate_buy_and_hold(df, initial_capital)

    df = calculate_moving_averages(df, short_window, long_window)
    df = generate_signals(df)

    results = simulate_trades(df, initial_capital)
    metrics = calculate_metrics(results)

    print_summary(ticker, metrics, results, buy_hold, short_window, long_window)

    return metrics, results, buy_hold


def main():
    parser = argparse.ArgumentParser(description="Stock Backtester with MA Crossover Strategy")
    parser.add_argument("--ticker", "-t", type=str, default="AAPL",
                        help="Stock ticker symbol (default: AAPL)")
    parser.add_argument("--short", "-s", type=int, default=20,
                        help="Short MA window in days (default: 20)")
    parser.add_argument("--long", "-l", type=int, default=50,
                        help="Long MA window in days (default: 50)")
    parser.add_argument("--capital", "-c", type=float, default=10000.0,
                        help="Initial capital in dollars (default: 10000)")

    args = parser.parse_args()

    if args.short >= args.long:
        print("Error: Short window must be smaller than long window.")
        return

    run_backtest(args.ticker, args.short, args.long, args.capital)


if __name__ == "__main__":
    main()
