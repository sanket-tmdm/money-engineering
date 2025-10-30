# Chapter 9: Tier 3 Execution Strategy

**Learning objectives:**
- Build execution strategies that translate signals to orders
- Manage broker connections
- Handle position synchronization
- Implement order types and pricing
- Deploy to live trading

**Previous:** [08 - Tier 2 Composite](08-tier2-composite.md) | **Next:** [10 - Visualization](10-visualization.md)

---

## Overview

Tier 3 strategies execute actual trades based on Tier 2 portfolio signals. This is where signals become real market orders through broker APIs.

## Architecture

```
┌──────────────────────────────────────┐
│   Tier 2: Portfolio Signals          │
│   - signals[]                        │
│   - leverages[]                      │
│   - markets[]                        │
│   - codes[]                          │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   TIER 3: EXECUTION                  │
│   - Signal translation               │
│   - Order management                 │
│   - Position synchronization         │
│   - Broker API integration           │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   Live Market Orders                 │
│   - Buy/Sell orders                  │
│   - Position updates                 │
│   - Trade confirmations              │
└──────────────────────────────────────┘
```

## Basic Executor Template

```python
#!/usr/bin/env python3
# coding=utf-8
"""Tier 3 Execution Strategy"""

import time
import sys

# Configuration
STRATEGY_NAME = "MyExecutor"
TIER2_STRATEGY = "MyComposite"
SIGNAL_MARKER = [f'private::{TIER2_STRATEGY}', 'PORTFOLIO']

# Trading configuration
MAX_BASKETS = 10
DRY_RUN = True  # Set False for live trading

# Position tracking
local_signals = []
remote_signals = []
ticks = {}

# Order constants
ORDER_TYPE_MARKET_PRICE = ord('1')
ORDER_TYPE_FIXED_PRICE = ord('0')
DIRECTION_BUY = ord('0')
DIRECTION_SELL = ord('1')

def _local_log(timetag, msg):
    """Log with timestamp."""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timetag/1000))
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

async def on_init():
    """Initialize executor."""
    _local_log(int(time.time()*1000), 
               f"{STRATEGY_NAME} initialized. DRY_RUN={DRY_RUN}")

async def on_ready():
    """Executor ready."""
    _local_log(int(time.time()*1000), f"{STRATEGY_NAME} ready")

async def on_bar(_bar, sub_accounts):
    """Process signals and execute trades."""
    global local_signals, remote_signals

    # Initialize position tracking
    if len(local_signals) == 0:
        initialize_position_tracking()

    # Process signals from Tier 2
    if _bar.name == SIGNAL_MARKER[0] and _bar.code == SIGNAL_MARKER[1]:
        await process_trading_signals(_bar, sub_accounts)

def initialize_position_tracking():
    """Initialize position tracking arrays."""
    global local_signals, remote_signals

    for i in range(MAX_BASKETS):
        local_signals.append([0, '', '', 0.0, 0.0, 0.0])
        remote_signals.append([0, '', '', 0.0, 0.0, None])

    _local_log(int(time.time()*1000), 
               f"Initialized {MAX_BASKETS} basket positions")

async def process_trading_signals(_bar, sub_accounts):
    """Process Tier 2 signals."""
    # Extract signal arrays
    signals = _bar.values.get('signals', [])
    markets = _bar.values.get('markets', [])
    codes = _bar.values.get('codes', [])
    leverages = _bar.values.get('leverages', [])
    capital_ratios = _bar.values.get('capital_ratios', [])
    prices = _bar.values.get('prices', [])

    _local_log(_bar.time_tag, f"Processing {len(signals)} signals")

    # Process each basket
    for i in range(min(len(local_signals), len(signals))):
        signal = int(signals[i]) if i < len(signals) else 0
        market = markets[i] if i < len(markets) else ''
        code = codes[i] if i < len(codes) else ''
        leverage = float(leverages[i]) if i < len(leverages) else 0.0
        capital_ratio = float(capital_ratios[i]) if i < len(capital_ratios) else 0.0
        price = float(prices[i]) if i < len(prices) else 0.0

        # Process signal change
        process_signal_change(i, signal, market, code, leverage, capital_ratio, price)

def process_signal_change(basket_idx, signal, market, code, leverage, capital_ratio, price):
    """Process signal change for a basket."""
    global local_signals

    local_signal = local_signals[basket_idx]

    # Close position
    if signal == 0 and local_signal[0] != 0:
        _local_log(int(time.time()*1000), f"Closing basket {basket_idx}")
        if not DRY_RUN:
            empty(0, basket_idx, price, 0.0, 0.0)
        local_signals[basket_idx] = [0, '', '', 0.0, 0.0, 0.0]
        return

    # Open/modify position
    if signal != 0 and signal != local_signal[0]:
        direction = "LONG" if signal == 1 else "SHORT"
        _local_log(int(time.time()*1000),
                  f"{direction} basket {basket_idx}: {market}/{code} "
                  f"lev={leverage:.2f} cr={capital_ratio:.3f}")

        if not DRY_RUN:
            if signal == 1:
                execute_long(ORDER_TYPE_FIXED_PRICE, market, code, 
                           0, basket_idx, price, leverage, capital_ratio)
            else:
                execute_short(ORDER_TYPE_FIXED_PRICE, market, code,
                            0, basket_idx, price, leverage, capital_ratio)

        local_signals[basket_idx] = [signal, market, code, leverage, capital_ratio, price]

async def on_market_open(market, tradeday, time_tag, time_string):
    _local_log(time_tag, f"Market open: {market}")

async def on_market_close(market, tradeday, timetag, timestring):
    _local_log(timetag, f"Market close: {market}")

async def on_tradeday_end(market, tradeday, timetag, timestring):
    """Log end of day positions."""
    global local_signals
    active = sum(1 for s in local_signals if s[0] != 0)
    _local_log(timetag, f"EOD: {active} active positions")

async def on_reference(market, tradeday, data, timetag, timestring):
    """Process tick sizes."""
    global ticks
    if 'commodity' in data:
        commodities = data['commodity']
        codes = commodities.get('code', [])
        tick_sizes = commodities.get('min_variation_unit', [])
        for i, code in enumerate(codes):
            if i < len(tick_sizes):
                ticks[f"{market}/{code}"] = tick_sizes[i]
```

## Key Concepts

### Signal Translation

Map Tier 2 portfolio signals to broker orders:

```python
# Tier 2 Output → Tier 3 Orders
signals[]        → Buy/Sell direction
leverages[]      → Position sizing
capital_ratios[] → Capital allocation
markets[]        → Exchange routing
codes[]          → Instrument selection
prices[]         → Order pricing
```

### Order Types

- **MARKET**: Execute immediately at market price
- **FIXED**: Limit order at specified price
- **BEST**: Best available price

### Position Synchronization

Maintain consistency between strategy state and broker positions:

```python
local_signals[]   # Current broker positions
remote_signals[]  # Desired positions from Tier 2

# Sync when differences detected
if local != remote:
    execute_order_to_sync()
```

## Summary

Tier 3 translates portfolio signals into actual trades:
- Receives signals from Tier 2
- Manages order execution
- Synchronizes positions
- Handles broker API

**Critical**: Test thoroughly in DRY_RUN mode before live trading!

---

**Previous:** [08 - Tier 2 Composite](08-tier2-composite.md) | **Next:** [10 - Visualization](10-visualization.md)
