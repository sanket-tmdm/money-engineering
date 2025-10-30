# Chapter 8: Tier 2 Composite Strategy

**Learning objectives:**
- Build portfolio-level composite strategies
- Manage multiple baskets efficiently
- Aggregate Tier 1 signals
- Implement risk management
- Allocate capital dynamically

**Previous:** [07 - Tier 1 Indicator](07-tier1-indicator.md) | **Next:** [09 - Tier 3 Execution Strategy](09-tier3-strategy.md)

---

## Overview

Tier 2 strategies aggregate signals from multiple Tier 1 indicators into unified portfolio decisions. They manage capital allocation, risk limits, and position sizing across multiple instruments.

## Tier 2 Architecture

```
┌──────────────────────────────────────┐
│   Tier 1: Multiple Indicators       │
│   - Copper indicator                 │
│   - Iron ore indicator               │
│   - Crude oil indicator              │
│   - ... (N indicators)               │
└────────────┬─────────────────────────┘
             │ Individual signals
             ▼
┌──────────────────────────────────────┐
│   TIER 2: COMPOSITE STRATEGY         │
│   - Signal aggregation               │
│   - Basket management                │
│   - Capital allocation               │
│   - Risk management                  │
│   - Performance tracking             │
└────────────┬─────────────────────────┘
             │ Portfolio signals
             ▼
┌──────────────────────────────────────┐
│   Output: Portfolio State            │
│   - Signals per basket               │
│   - Leverages                        │
│   - Capital ratios                   │
│   - Performance metrics              │
└──────────────────────────────────────┘
```

## Building a Composite Strategy

### Step 1: Project Structure

```bash
mkdir MyComposite
cd MyComposite
touch MyComposite.py
touch uin.json
touch uout.json
mkdir .vscode
touch .vscode/launch.json
```

### Step 2: uin.json - Import Tier 1 Signals

```json
{
  "private": {
    "imports": {
      "MyIndicator": {
        "fields": [
          "bar_index",
          "ema_fast",
          "ema_slow",
          "signal",
          "confidence"
        ],
        "granularities": [900],
        "markets": ["SHFE"],
        "security_categories": [[1, 2, 3]],
        "securities": [["cu", "al"]]
      }
    }
  }
}
```

### Step 3: Complete Composite Implementation

```python
#!/usr/bin/env python3
# coding=utf-8
"""Tier 2 Composite Strategy"""

import math
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

import pycaitlyn as pc
import pycaitlynutils3 as pcu3
import pycaitlynts3 as pcts3
import composite_strategyc3 as csc3

# Framework globals
use_raw = True
overwrite = False
granularity = 900
schema = None
max_workers = 1
worker_no = None
exports = {}
imports = {}
metas = {}
logger = pcu3.vanilla_logger()

# Configuration
BASKET_COUNT = 5
COMMODITIES = {
    b'SHFE': [b'cu', b'al', b'zn', b'pb', b'ni']
}

class IndicatorParser(pcts3.sv_object):
    """Parse Tier 1 indicator signals."""
    def __init__(self):
        super().__init__()
        self.meta_name = "MyIndicator"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        # Fields from Tier 1
        self.bar_index = 0
        self.ema_fast = 0.0
        self.ema_slow = 0.0
        self.signal = 0
        self.confidence = 0.0

class MyComposite(csc3.composite_strategy):
    """Composite strategy managing multiple baskets."""

    def __init__(self, initial_cash=10000000.0):
        # Initialize critical attributes FIRST
        self.bar_index_this_run = -1
        self.latest_sv = None

        # Commodity to basket mapping
        self.commodity_to_basket = {}
        self.basket_to_commodity = {}
        idx = 0
        for market, codes in COMMODITIES.items():
            for code in codes:
                self.commodity_to_basket[(market, code)] = idx
                self.basket_to_commodity[idx] = (market, code)
                idx += 1

        # Signal parsers for each commodity
        self.parsers = {}
        for market, codes in COMMODITIES.items():
            for code in codes:
                key = (market, code)
                parser = IndicatorParser()
                parser.market = market
                parser.code = code + b'<00>'
                parser.granularity = granularity
                self.parsers[key] = parser

        # Current signals from Tier 1
        self.tier1_signals = {}

        # Initialize composite strategy
        super().__init__(initial_cash, BASKET_COUNT)

        # Metadata
        self.namespace = pc.namespace_private
        self.granularity = granularity
        self.market = b'SHFE'
        self.code = b'COMPOSITE'
        self.meta_name = "MyComposite"
        self.revision = (1 << 32) - 1
        self.timetag_ = None

        # Output fields
        self.bar_index = 0
        self.active_positions = 0
        self.total_signals_processed = 0

        # Risk parameters
        self.max_leverage = 2.5
        self.min_signal_strength = 0.3
        self.min_confidence = 0.5

        # Initialize baskets
        for basket_idx in range(BASKET_COUNT):
            market, code = self.basket_to_commodity[basket_idx]
            basket_capital = initial_cash / BASKET_COUNT
            self._allocate(basket_idx, market, code + b'<00>', basket_capital, 1.0)

        logger.info(f"Initialized {BASKET_COUNT} baskets")

    def on_bar(self, bar: pc.StructValue):
        """Main bar processing."""
        market = bar.get_market()
        code = bar.get_stock_code()
        tm = bar.get_time_tag()
        ns = bar.get_namespace()
        meta_id = bar.get_meta_id()

        # Initialize timetag
        if self.timetag is None:
            self.timetag = tm

        # Handle cycle boundaries
        if self.timetag < tm:
            self._on_cycle_pass(tm)

            results = []
            if self.bar_index > 0:
                results.append(self.sv_copy())

            self.timetag = tm
            self.bar_index += 1

            return results

        # Process Tier 1 signals
        self._process_tier1_signal(bar)

        return []

    def _process_tier1_signal(self, bar: pc.StructValue):
        """Parse and store Tier 1 signals."""
        market = bar.get_market()
        code = bar.get_stock_code()
        meta_id = bar.get_meta_id()
        ns = bar.get_namespace()

        # Extract commodity code
        commodity = self.calc_commodity(code)
        key = (market, commodity)

        # Parse if we have a parser for this commodity
        if key in self.parsers:
            parser = self.parsers[key]
            if ns == parser.namespace and meta_id == parser.meta_id:
                parser.from_sv(bar)

                # Store signal data
                self.tier1_signals[key] = {
                    'signal': parser.signal,
                    'confidence': parser.confidence,
                    'ema_fast': parser.ema_fast,
                    'ema_slow': parser.ema_slow
                }
                self.total_signals_processed += 1

    def _on_cycle_pass(self, time_tag):
        """Process end of cycle."""
        super()._on_cycle_pass(time_tag)

        # Process trading signals
        self._process_trading_signals()

        # Update metrics
        self.active_positions = sum(1 for s in self.strategies if s.signal != 0)

        # Sync state
        self._save()
        self._sync()

        logger.info(f"Bar {self.bar_index}: NV={self.nv:.4f}, "
                   f"PV={self.pv:.2f}, Active={self.active_positions}")

    def _process_trading_signals(self):
        """Execute trading signals for each basket."""
        for basket_idx in range(BASKET_COUNT):
            market, commodity = self.basket_to_commodity[basket_idx]
            key = (market, commodity)

            # Get Tier 1 signal
            if key not in self.tier1_signals:
                continue

            signal_data = self.tier1_signals[key]
            signal = signal_data['signal']
            confidence = signal_data['confidence']

            # Filter by confidence
            if abs(signal) < self.min_signal_strength or confidence < self.min_confidence:
                signal = 0

            # Get current basket state
            basket = self.strategies[basket_idx]
            current_signal = basket.signal

            # Execute if signal changed
            if signal != current_signal:
                self._execute_basket_signal(basket_idx, signal, confidence)

    def _execute_basket_signal(self, basket_idx, signal, confidence):
        """Execute signal for a basket."""
        basket = self.strategies[basket_idx]
        market, commodity = self.basket_to_commodity[basket_idx]

        # Calculate leverage based on confidence
        leverage = 1.0 + (confidence * 1.5)  # 1.0 to 2.5
        leverage = min(leverage, self.max_leverage)

        if signal == 0:
            logger.info(f"CLOSE basket {basket_idx}: {market.decode()}/{commodity.decode()}")
            basket._signal(basket.price, basket.timetag, signal)
        else:
            logger.info(f"{'LONG' if signal == 1 else 'SHORT'} basket {basket_idx}: "
                       f"{market.decode()}/{commodity.decode()} lev={leverage:.2f}")
            basket._fit_position(leverage)
            basket._signal(basket.price, basket.timetag, signal * -1)

# Global strategy
strategy = MyComposite()

# Framework callbacks
async def on_init():
    global strategy, imports, metas, worker_no
    if worker_no != 0 and metas and imports:
        strategy.load_def_from_dict(metas)
        for parser in strategy.parsers.values():
            parser.load_def_from_dict(metas)
            parser.set_global_imports(imports)

async def on_ready():
    pass

async def on_bar(bar: pc.StructValue):
    global strategy, worker_no
    if worker_no != 1:
        return []
    return strategy.on_bar(bar)

async def on_market_open(market, tradeday, time_tag, time_string):
    pass

async def on_market_close(market, tradeday, timetag, timestring):
    pass

async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    global strategy
    strategy.on_tradeday_begin(bytes(market, 'utf-8'), tradeday)

async def on_tradeday_end(market, tradeday, timetag, timestring):
    global strategy
    strategy.on_tradeday_end(bytes(market, 'utf-8'), tradeday)

async def on_reference(market, tradeday, data, timetag, timestring):
    pass

async def on_historical(params, records):
    pass
```

## Key Concepts

### Basket Management

Each basket represents an individual trading strategy:

```python
# Basket state
basket.signal      # Current signal: -1, 0, 1
basket.leverage    # Position leverage
basket.pv          # Portfolio value
basket.nv          # Net value (performance)
basket.price       # Current price
basket.instrument  # Trading instrument
```

### Signal Aggregation

Aggregate multiple Tier 1 signals:

```python
def aggregate_signals(self):
    """Combine signals from multiple indicators."""
    signals = []
    for key, signal_data in self.tier1_signals.items():
        if signal_data['confidence'] > 0.6:
            signals.append(signal_data['signal'])

    # Consensus signal
    if len(signals) > 0:
        avg_signal = sum(signals) / len(signals)
        if avg_signal > 0.5:
            return 1
        elif avg_signal < -0.5:
            return -1
    return 0
```

### Capital Allocation

Dynamically allocate capital:

```python
def calculate_allocation(self, signal_data):
    """Calculate capital allocation based on signal quality."""
    base_allocation = 1.0 / self.basket_count
    confidence_mult = 0.5 + signal_data['confidence'] * 0.5
    return base_allocation * confidence_mult
```

## Summary

- Tier 2 aggregates Tier 1 signals into portfolio decisions
- Manages multiple baskets per instrument
- Implements risk management and capital allocation
- Tracks performance at portfolio level
- Uses composite_strategyc3 base class

**Next:** Tier 3 execution strategies.

---

**Previous:** [07 - Tier 1 Indicator](07-tier1-indicator.md) | **Next:** [09 - Tier 3 Execution Strategy](09-tier3-strategy.md)
