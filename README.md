# Stock Backtester

A Python backtester that simulates a moving average crossover trading strategy on historical stock data.

## Features

- Fetches 1 year of historical daily data using yfinance
- Implements a simple moving average (SMA) crossover strategy
- Simulates trades with configurable initial capital
- Compares strategy performance against buy-and-hold benchmark
- Tracks key metrics: total return, number of trades, win rate, max drawdown

## How It Works

The strategy uses two moving averages:
- **Short MA** (default: 20 days)
- **Long MA** (default: 50 days)

Trading rules:
- **Buy** when the short MA crosses above the long MA
- **Sell** when the short MA crosses below the long MA

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run with default settings (AAPL, 20/50 day MA, $10,000 capital):

```bash
python backtester.py
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--ticker`, `-t` | Stock ticker symbol | AAPL |
| `--short`, `-s` | Short MA window (days) | 20 |
| `--long`, `-l` | Long MA window (days) | 50 |
| `--capital`, `-c` | Initial capital ($) | 10000 |

### Examples

Test with Microsoft stock:

```bash
python backtester.py --ticker MSFT
```

Use a faster crossover (10/30 day):

```bash
python backtester.py --short 10 --long 30
```

Test with $50,000 starting capital on Tesla:

```bash
python backtester.py -t TSLA -c 50000
```

Combine multiple options:

```bash
python backtester.py --ticker NVDA --short 5 --long 20 --capital 25000
```

## Sample Output

```
======================================================================
  BACKTEST RESULTS: AAPL
======================================================================

  Metric                 MA Crossover (20/50)             Buy & Hold
  ------------------------------------------------------------------
  Initial Capital      $           10,000.00 $           10,000.00
  Final Value          $           12,038.23 $           11,024.98
  Total Return                         20.38%                 10.25%
  Max Drawdown                         -8.99%                -30.15%

  Strategy Metrics
  ------------------------------------------------------------------
  Number of Trades                          2
  Win Rate                              50.0%

  ------------------------------------------------------------------
  Strategy OUTPERFORMED buy-and-hold by +10.13%
```

## Metrics Explained

- **Total Return**: Percentage gain/loss from initial capital
- **Max Drawdown**: Largest peak-to-trough decline during the period
- **Win Rate**: Percentage of trades that were profitable
- **Number of Trades**: Count of completed round-trip trades (buy + sell)
