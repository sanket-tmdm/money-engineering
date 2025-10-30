# Chapter 10: Visualization and Analysis

**Learning objectives:**
- Create visualization scripts for indicator analysis
- Fetch data using svr3 API
- Analyze parameter performance
- Generate diagnostic plots
- Optimize indicator parameters

**Previous:** [09 - Tier 3 Strategy](09-tier3-strategy.md) | **Next:** [11 - Fine-tune and Iterate](11-fine-tune-and-iterate.md)

---

## Overview

Visualization helps understand indicator behavior, identify issues, and optimize parameters. This chapter shows how to create analysis scripts using the svr3 API.

## Visualization Script Template

```python
#!/usr/bin/env python3
"""Indicator Visualization Script"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict
import svr3

# Configuration
STRATEGY_NAME = "MyIndicator"
NAMESPACE = "private"
MARKET = "SHFE"
CODE = "cu<00>"
GRANULARITY = 900

# Time range
START_TIME = "20250701000000"
END_TIME = "20250710000000"

# SVR3 connection
SVR_HOST = "10.99.100.116"
SVR_PORT = 8080
TOKEN = "YOUR_TOKEN"

def fetch_indicator_data(start, end):
    """Fetch indicator data using svr3."""
    client = svr3.Client(SVR_HOST, SVR_PORT, TOKEN)

    data = client.fetch(
        namespace=NAMESPACE,
        strategy=STRATEGY_NAME,
        market=MARKET,
        code=CODE,
        granularity=GRANULARITY,
        start=start,
        end=end
    )

    return pd.DataFrame(data)

def plot_indicator_signals(df):
    """Plot indicator signals over time."""
    fig, axes = plt.subplots(3, 1, figsize=(15, 10))

    # Plot 1: EMAs and Price
    ax1 = axes[0]
    ax1.plot(df['timestamp'], df['ema_fast'], label='EMA Fast', color='blue')
    ax1.plot(df['timestamp'], df['ema_slow'], label='EMA Slow', color='red')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.set_title('EMA Indicators')
    ax1.grid(True)

    # Plot 2: Signals
    ax2 = axes[1]
    ax2.scatter(df['timestamp'], df['signal'], c=df['signal'], 
                cmap='RdYlGn', alpha=0.6)
    ax2.set_ylabel('Signal')
    ax2.set_ylim(-1.5, 1.5)
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax2.set_title('Trading Signals')
    ax2.grid(True)

    # Plot 3: Confidence
    ax3 = axes[2]
    ax3.fill_between(df['timestamp'], 0, df['confidence'], 
                     alpha=0.3, color='green')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Confidence')
    ax3.set_title('Signal Confidence')
    ax3.grid(True)

    plt.tight_layout()
    plt.savefig('indicator_analysis.png', dpi=150)
    print("Saved: indicator_analysis.png")

def analyze_signal_distribution(df):
    """Analyze signal distribution."""
    print("\n=== Signal Distribution ===")
    print(df['signal'].value_counts())

    print("\n=== Confidence Statistics ===")
    print(df['confidence'].describe())

    # Plot distributions
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Signal distribution
    df['signal'].value_counts().plot(kind='bar', ax=axes[0])
    axes[0].set_title('Signal Distribution')
    axes[0].set_ylabel('Count')

    # Confidence distribution
    axes[1].hist(df['confidence'], bins=20, edgecolor='black')
    axes[1].set_title('Confidence Distribution')
    axes[1].set_xlabel('Confidence')
    axes[1].set_ylabel('Frequency')

    plt.tight_layout()
    plt.savefig('distributions.png', dpi=150)
    print("Saved: distributions.png")

def main():
    """Main analysis workflow."""
    print(f"Fetching data for {STRATEGY_NAME}...")
    df = fetch_indicator_data(START_TIME, END_TIME)

    print(f"Loaded {len(df)} bars")

    # Generate plots
    plot_indicator_signals(df)
    analyze_signal_distribution(df)

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
```

## Key Visualizations

### 1. Indicator Time Series

```python
def plot_time_series(df):
    """Plot all indicator values over time."""
    fields = ['ema_fast', 'ema_slow', 'tsi', 'vai', 'mdi']

    fig, axes = plt.subplots(len(fields), 1, figsize=(15, 3*len(fields)))

    for i, field in enumerate(fields):
        axes[i].plot(df['timestamp'], df[field])
        axes[i].set_title(f'{field.upper()}')
        axes[i].grid(True)

    plt.tight_layout()
    plt.savefig('time_series.png', dpi=150)
```

### 2. Correlation Analysis

```python
def analyze_correlations(df):
    """Analyze correlations between indicators."""
    corr_matrix = df[['ema_fast', 'ema_slow', 'signal', 'confidence']].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('Indicator Correlations')
    plt.tight_layout()
    plt.savefig('correlations.png', dpi=150)
```

### 3. Signal Performance

```python
def analyze_signal_performance(df):
    """Analyze signal performance."""
    # Calculate returns
    df['returns'] = df['close'].pct_change()

    # Signal-based returns
    df['signal_returns'] = df['signal'].shift(1) * df['returns']

    # Cumulative returns
    cumulative = (1 + df['signal_returns']).cumprod()

    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], cumulative)
    plt.title('Cumulative Strategy Returns')
    plt.xlabel('Time')
    plt.ylabel('Cumulative Return')
    plt.grid(True)
    plt.savefig('performance.png', dpi=150)
```

## Parameter Analysis

### Finding Optimal Parameters

```python
def parameter_sweep(start, end):
    """Test different parameter combinations."""
    results = []

    # Test different EMA periods
    for fast in [5, 10, 15, 20]:
        for slow in [20, 30, 40, 50]:
            if slow <= fast:
                continue

            # Fetch data with these parameters
            df = run_backtest_with_params(fast, slow)

            # Calculate performance metrics
            sharpe = calculate_sharpe_ratio(df)
            max_dd = calculate_max_drawdown(df)
            win_rate = calculate_win_rate(df)

            results.append({
                'fast': fast,
                'slow': slow,
                'sharpe': sharpe,
                'max_dd': max_dd,
                'win_rate': win_rate
            })

    return pd.DataFrame(results)

def plot_parameter_heatmap(results_df):
    """Visualize parameter sweep results."""
    pivot = results_df.pivot(index='fast', columns='slow', values='sharpe')

    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn')
    plt.title('Sharpe Ratio by EMA Parameters')
    plt.xlabel('Slow EMA Period')
    plt.ylabel('Fast EMA Period')
    plt.savefig('parameter_sweep.png', dpi=150)
```

## Summary

Visualization helps:
- Understand indicator behavior
- Identify parameter issues
- Optimize performance
- Debug problems
- Communicate results

Key tools:
- svr3 API for data fetching
- pandas for data manipulation
- matplotlib/seaborn for plotting

**Next**: Iterative optimization workflow.

---

**Previous:** [09 - Tier 3 Strategy](09-tier3-strategy.md) | **Next:** [11 - Fine-tune and Iterate](11-fine-tune-and-iterate.md)
