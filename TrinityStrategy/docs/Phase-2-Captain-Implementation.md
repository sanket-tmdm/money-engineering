# Trinity Strategy Phase-2: Captain Implementation Guide

**Document ID:** TRINITY-P2-IMPL-V1.0
**Date:** 2025-11-13
**Status:** IMPLEMENTATION GUIDE
**Purpose:** Comprehensive guide for implementing the WOS_CaptainStrategy (Tier-2 composite strategy) that consumes Phase-1 Scout outputs to generate trading signals across 12 commodities.

---

## Table of Contents

1. [Overview](#1-overview)
2. [The 12-Basket Architecture](#2-the-12-basket-architecture)
3. [Data Sources: SampleQuote vs Tier-1 Outputs](#3-data-sources-samplequote-vs-tier-1-outputs)
4. [Risk Management Design](#4-risk-management-design)
5. [Regime Logic: River, Lake, Dead Zone](#5-regime-logic-river-lake-dead-zone)
6. [Intraday Exit Logic](#6-intraday-exit-logic)
7. [File Structure](#7-file-structure)
8. [Implementation Architecture](#8-implementation-architecture)
9. [Testing Workflow](#9-testing-workflow)
10. [Success Criteria](#10-success-criteria)
11. [Expected Performance Metrics](#11-expected-performance-metrics)
12. [Troubleshooting Guide](#12-troubleshooting-guide)

---

## 1. Overview

### 1.1 What is Phase-2?

Phase-2 implements the **WOS_CaptainStrategy**, the "brain" of the Trinity system. It's a Tier-2 composite strategy that:

1. **Consumes Phase-1 Scout outputs**: Reads TrendScout (ADX), TensionScout (Bollinger Bands), and CrowdScout (Conviction) indicators
2. **Implements regime-adaptive logic**: Switches between Trend-Following ("River") and Mean-Reversion ("Lake") strategies based on ADX
3. **Manages 12 independent baskets**: One basket per commodity, each with its own capital allocation and risk parameters
4. **Generates trading signals**: Outputs Buy (1), Sell (-1), or Hold (0) signals for each commodity
5. **Enforces risk management**: Portfolio-level and per-basket drawdown limits, plus intraday exit rules

### 1.2 Goals

**Primary Goal**: Build a regime-adaptive, multi-commodity trading system that:
- Catches big trends in trending markets (River mode)
- Profits from reversions in ranging markets (Lake mode)
- Avoids whipsaws in uncertain markets (Dead Zone)
- Controls risk through volatility-based position sizing

**Design Philosophy**: "Captain's Playbook" - Just as a cricket captain adapts strategy based on pitch conditions, our system adapts trading strategy based on market regime.

### 1.3 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE-1 (Tier-1)                         │
│  TrinityStrategy.py - Three Scout Indicators                │
│  ├─ WOS_TrendScout: ADX, DI+, DI-                          │
│  ├─ WOS_TensionScout: Bollinger Bands                       │
│  └─ WOS_CrowdScout: Conviction Oscillator                   │
│                          ↓                                   │
│            Outputs 9 fields per commodity                    │
│            (published to private namespace)                  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    PHASE-2 (Tier-2)                         │
│  WOS_CaptainStrategy.py - Composite Strategy                │
│  ├─ 12 Independent Baskets (one per commodity)              │
│  ├─ Two Input Parsers:                                      │
│  │   ├─ SampleQuote: Close price (global namespace)        │
│  │   └─ ScoutParser: Scout outputs (private namespace)     │
│  ├─ Regime Detection Logic                                  │
│  ├─ Signal Generation                                        │
│  └─ Risk Management                                          │
│                          ↓                                   │
│         Outputs: Signals + Performance Metrics               │
└─────────────────────────────────────────────────────────────┘
                             ↓
                    Trading Execution
```

### 1.4 WOS Framework Positioning

| Tier | Component | Role | Input | Output |
|------|-----------|------|-------|--------|
| **Tier-1** | TrinityStrategy | Scout Indicators | OHLCV | ADX, BB, Conviction |
| **Tier-2** | WOS_CaptainStrategy | Composite Strategy | Scout outputs + OHLCV | Trading signals |
| **Tier-3** | (Future) | Execution Strategy | Signals | Orders |

---

## 2. The 12-Basket Architecture

### 2.1 Why One Basket Per Commodity?

**Question**: Why not one basket for all 12 commodities?

**Answer**: Each commodity has unique characteristics that require independent management:

1. **Different Volatilities**: Iron ore moves ~27 points/day, Copper moves ~1060 points/day
   - Without per-commodity sizing, Copper would dominate portfolio risk
   - Risk parity requires individual volatility-based position sizing

2. **Different Regimes**: At any moment:
   - Iron ore might be trending (River mode)
   - Copper might be ranging (Lake mode)
   - Gold might be in Dead Zone
   - Each needs independent strategy selection

3. **Independent Contract Rolling**: Each commodity has different:
   - Contract expiry dates (Jan, May, Sep cycles vary by market)
   - Rolling schedules (based on volume/open interest)
   - Active months (some trade 5 months, others 12 months)

4. **Isolated Risk**: One basket per commodity ensures:
   - A bad trade in Copper doesn't affect Iron ore basket
   - Per-basket drawdown limits contain damage
   - Individual performance tracking for analysis

5. **Capital Allocation**: Different market-neutral allocations:
   - High-volatility commodities get less capital (Copper: 2.6% of allocation)
   - Low-volatility commodities get more capital (Gold: 538% of baseline)
   - Enables portfolio-level risk parity

### 2.2 Basket Allocation Strategy

**Equal Capital, Unequal Risk**:

```python
# Each basket starts with equal capital
INITIAL_CAPITAL = 10_000_000.0
BASKET_COUNT = 12
CAPITAL_PER_BASKET = INITIAL_CAPITAL / BASKET_COUNT  # 833,333.33 per basket

# But position sizing differs based on volatility
# Example for Iron Ore (baseline, vol = 27.46):
iron_ore_size = 1.0  # Full position

# Example for Copper (high vol = 1060.24):
copper_size = 27.46 / 1060.24 = 0.026  # 2.6% position size
```

**Position Sizing Formula**:
```
size = baseline_volatility / instrument_volatility
```

Where:
- `baseline_volatility`: Iron ore BB width mean (27.46) - our reference
- `instrument_volatility`: Each commodity's BB width mean from tuning results

### 2.3 The 12 Commodities

From tuning results (`trinity_parameters.json`):

| Category | Market | Code | Volatility | Size | Personality |
|----------|--------|------|------------|------|-------------|
| **Ferrous** | DCE | i<00> | 27.46 | 1.00 | Baseline - Trending |
| | DCE | j<00> | 71.03 | 0.39 | Coke - High vol |
| | SHFE | rb<00> | 61.97 | 0.44 | Rebar - Moderate |
| **Base Metals** | SHFE | cu<00> | 1060.24 | 0.026 | Copper - VERY high vol |
| | SHFE | al<00> | 225.00 | 0.12 | Aluminum - High vol |
| **Precious** | SHFE | au<00> | 5.10 | 5.38 | Gold - LOW vol, safe haven |
| **Energy** | SHFE | sc<00> | 12.36 | 2.22 | Crude oil - Low vol |
| **Chemicals** | CZCE | TA<00> | 86.51 | 0.32 | PTA - Moderate |
| | CZCE | MA<00> | 46.71 | 0.59 | Methanol - Moderate |
| | SHFE | ru<00> | 305.02 | 0.09 | Rubber - High vol |
| **Agri** | DCE | m<00> | 63.02 | 0.44 | Soybeans - Moderate |
| | DCE | y<00> | 134.16 | 0.20 | Palm oil - High vol |

**Key Observations**:
- **Gold (au)**: Lowest volatility (5.10) → Highest size (5.38×) → Safe harbor during chaos
- **Copper (cu)**: Highest volatility (1060.24) → Lowest size (0.026×) → Small bet on wild swings
- **Iron Ore (i)**: Baseline reference → Normal size (1.0×) → Primary trend-following vehicle

### 2.4 Basket Initialization

```python
# In WOS_CaptainStrategy.__init__()
COMMODITIES = {
    b'DCE': [b'i<00>', b'j<00>', b'm<00>', b'y<00>'],
    b'SHFE': [b'cu<00>', b'sc<00>', b'al<00>', b'rb<00>', b'au<00>', b'ru<00>'],
    b'CZCE': [b'TA<00>', b'MA<00>']
}

# Create basket mapping
self.basket_to_commodity = {}
basket_idx = 0
for market, codes in COMMODITIES.items():
    for code in codes:
        self.basket_to_commodity[basket_idx] = (market, code)
        basket_idx += 1

# Allocate baskets
for basket_idx in range(BASKET_COUNT):
    market, code = self.basket_to_commodity[basket_idx]
    self._allocate(
        meta_id=basket_idx,
        market=market,
        code=code,
        money=CAPITAL_PER_BASKET,
        leverage=1.0
    )
```

**What `_allocate()` Does**:
- Creates a `strategyc3.strategy` instance for the basket
- Transfers capital from composite to basket
- Sets `basket.market = market`, `basket.code = code`
- **Does NOT set `target_instrument`** - This happens via `on_reference()`

**What `_allocate()` Does NOT Do**:
- Does NOT subscribe to market data
- Does NOT populate contract rolling information
- Does NOT set actual trading instrument (e.g., `i2501`)

---

## 3. Data Sources: SampleQuote vs Tier-1 Outputs

### 3.1 The Two-Parser Architecture

Phase-2 needs TWO types of data:

1. **Current Close Price**: For comparing against Bollinger Bands (Lake mode logic)
2. **Scout Indicators**: ADX, Bands, Conviction from Phase-1

**Why Not Just Use Scout Outputs?**

**Problem**: Phase-1 doesn't export `close` price - it only exports calculated indicators.

**Solution**: Import `SampleQuote` directly from global namespace to get `close`.

### 3.2 SampleQuote Parser

**Purpose**: Get current close price for Band comparison logic.

```python
class SampleQuote(pcts3.sv_object):
    """Market data parser - imports from global namespace"""

    def __init__(self):
        super().__init__()
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # OHLCV fields
        self.open = None
        self.high = None
        self.low = None
        self.close = None  # <-- This is what we need
        self.volume = None
        self.turnover = None
```

**Why from Global Namespace?**
- `SampleQuote` is the raw market data feed
- Published by data provider to `namespace_global`
- Available to all strategies without dependencies
- Same data source Phase-1 uses for calculations

### 3.3 ScoutParser

**Purpose**: Get Phase-1 Scout indicator outputs.

```python
class ScoutParser(pcts3.sv_object):
    """Scout indicator parser - imports from private namespace"""

    def __init__(self):
        super().__init__()
        self.meta_name = "WOS_TrendScout"  # Must match Phase-1 output name
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # Phase-1 outputs
        self.bar_index = 0
        self.adx_value = 0.0
        self.di_plus = 0.0
        self.di_minus = 0.0
        self.upper_band = 0.0
        self.middle_band = 0.0
        self.lower_band = 0.0
        self.conviction_oscillator = 0.0
```

**Why from Private Namespace?**
- Phase-1 publishes to `namespace_private`
- These are derived indicators, not raw market data
- Only visible to strategies in same account/workspace
- Prevents namespace pollution

### 3.4 Data Flow Diagram

```
┌────────────────────────────────────────┐
│  Data Provider                         │
│  (10.99.100.116)                      │
└───────────┬────────────────────────────┘
            │
            ↓ (publishes to namespace_global)
┌────────────────────────────────────────┐
│  SampleQuote (OHLCV)                   │
│  - open, high, low, close, volume      │
└──────┬─────────────────────┬───────────┘
       │                     │
       ↓                     ↓
┌──────────────┐    ┌───────────────────┐
│  Phase-1     │    │  Phase-2          │
│  Scouts      │    │  Captain          │
│              │    │  (SampleQuote     │
│ Calculates:  │    │   parser gets     │
│ - ADX        │    │   close price)    │
│ - BB         │    │                   │
│ - Conviction │    │                   │
└──────┬───────┘    └────────┬──────────┘
       │                     │
       ↓ (publishes to       │
          namespace_private) │
┌──────────────────────┐     │
│  Scout Outputs       │     │
│  - adx_value         │     │
│  - di_plus/minus     │     │
│  - bands             │     │
│  - conviction        │     │
└──────┬───────────────┘     │
       │                     │
       └─────────┬───────────┘
                 ↓
        ┌────────────────────┐
        │  Phase-2 Captain   │
        │  (ScoutParser gets │
        │   indicators)      │
        │                    │
        │  Decision Logic:   │
        │  if close < lower  │
        │    and ADX < lake  │
        │    → BUY           │
        └────────────────────┘
```

### 3.5 uin.json Configuration

```json
{
  "global": {
    "imports": {
      "SampleQuote": {
        "fields": ["close", "volume"],
        "granularities": [900],
        "markets": ["DCE", "SHFE", "CZCE"],
        "security_categories": [[1, 2, 3], [1, 2, 3], [1, 2, 3]],
        "securities": [
          ["i", "j", "m", "y"],
          ["cu", "sc", "al", "rb", "au", "ru"],
          ["TA", "MA"]
        ]
      }
    }
  },
  "private": {
    "imports": {
      "WOS_TrendScout": {
        "fields": [
          "bar_index",
          "adx_value",
          "di_plus",
          "di_minus",
          "upper_band",
          "middle_band",
          "lower_band",
          "conviction_oscillator"
        ],
        "granularities": [900],
        "markets": ["DCE", "SHFE", "CZCE"],
        "security_categories": [[1, 2, 3], [1, 2, 3], [1, 2, 3]],
        "securities": [
          ["i", "j", "m", "y"],
          ["cu", "sc", "al", "rb", "au", "ru"],
          ["TA", "MA"]
        ]
      }
    }
  }
}
```

**Key Points**:
- **Two import sources**: `global.SampleQuote` and `private.WOS_TrendScout`
- **Logical contracts**: Use commodity codes without `<00>` suffix in config
- **Same markets/securities**: Must match Phase-1 for data availability

### 3.6 Parser Management in Strategy

```python
class WOS_CaptainStrategy(csc3.composite_strategy):
    def __init__(self):
        # ... basket initialization ...

        # Create parsers for each commodity
        self.quote_parsers = {}
        self.scout_parsers = {}

        for market, codes in COMMODITIES.items():
            for code in codes:
                key = (market, code)

                # SampleQuote parser (close price)
                quote = SampleQuote()
                quote.market = market
                quote.code = code
                quote.granularity = granularity
                self.quote_parsers[key] = quote

                # ScoutParser (indicators)
                scout = ScoutParser()
                scout.market = market
                scout.code = code
                scout.granularity = granularity
                self.scout_parsers[key] = scout
```

---

## 4. Risk Management Design

### 4.1 Overview

Trinity implements **three-tier risk management**:

1. **Position Sizing (Risk Parity)**: Volatility-based per-commodity sizing
2. **Per-Basket Drawdown Limits**: Individual basket risk controls
3. **Portfolio-Level Drawdown Limits**: Overall portfolio protection

### 4.2 Position Sizing (Risk Parity)

**Goal**: Equalize risk contribution across commodities.

**Implementation**:

```python
# Load tuning results
import json
with open('trinity_parameters.json', 'r') as f:
    params = json.load(f)

# Calculate risk parity sizes
BASELINE_VOL = 27.46  # Iron ore volatility (reference)

TRINITY_PLAYBOOK = {}
for code, data in params['instruments'].items():
    instrument_vol = data['bb_width_mean']
    size = BASELINE_VOL / instrument_vol

    TRINITY_PLAYBOOK[code.encode()] = {
        'adx_river': data['adx_river_threshold'],
        'adx_lake': data['adx_lake_threshold'],
        'conviction_bull': data['conviction_bull_threshold'],
        'conviction_bear': data['conviction_bear_threshold'],
        'size': round(size, 2)
    }
```

**Example Calculation**:

| Commodity | Volatility | Size | Position Value (on 1M capital) |
|-----------|------------|------|--------------------------------|
| Iron Ore | 27.46 | 1.00 | 1,000,000 (baseline) |
| Copper | 1060.24 | 0.026 | 26,000 (controlled exposure) |
| Gold | 5.10 | 5.38 | 5,380,000 (safe leverage) |

**Result**: All positions contribute similar volatility to portfolio.

### 4.3 Per-Basket Drawdown Limits

**Purpose**: Prevent single commodity from destroying portfolio.

**Parameters**:

```python
# In WOS_CaptainStrategy.__init__()
self.max_basket_dd_pct = 0.15  # 15% per-basket drawdown limit
self.basket_peak_nv = {}       # Track each basket's peak NV

# Initialize tracking
for i in range(BASKET_COUNT):
    self.basket_peak_nv[i] = 1.0  # Start at 1.0 (100%)
```

**Logic**:

```python
def _check_basket_drawdown(self, basket_idx):
    """Check if basket has hit drawdown limit."""
    basket = self.strategies[basket_idx]
    current_nv = basket.nv

    # Update peak
    if current_nv > self.basket_peak_nv[basket_idx]:
        self.basket_peak_nv[basket_idx] = current_nv

    # Calculate drawdown
    peak = self.basket_peak_nv[basket_idx]
    dd_pct = (peak - current_nv) / peak

    if dd_pct >= self.max_basket_dd_pct:
        logger.warning(f"BASKET {basket_idx} DD LIMIT HIT: {dd_pct*100:.2f}%")
        # Force close position
        if basket.signal != 0:
            basket._signal(basket.price, basket.timetag, 0)
        return True

    return False
```

**Expected Impact**:
- Limits damage from bad commodity-specific events
- Preserves capital for other baskets
- Typical trigger: Unexpected policy change, supply shock

### 4.4 Portfolio-Level Drawdown Limits

**Purpose**: Protect overall portfolio from systemic risk.

**Parameters**:

```python
self.max_portfolio_dd_pct = 0.20  # 20% portfolio drawdown limit
self.portfolio_peak_nv = 1.0       # Track portfolio peak NV
self.risk_off_mode = False         # Risk-off flag
```

**Logic**:

```python
def _check_portfolio_drawdown(self):
    """Check portfolio-level drawdown."""
    current_nv = self.nv

    # Update peak
    if current_nv > self.portfolio_peak_nv:
        self.portfolio_peak_nv = current_nv
        self.risk_off_mode = False  # Reset risk-off

    # Calculate drawdown
    dd_pct = (self.portfolio_peak_nv - current_nv) / self.portfolio_peak_nv

    if dd_pct >= self.max_portfolio_dd_pct:
        if not self.risk_off_mode:
            logger.error(f"PORTFOLIO DD LIMIT HIT: {dd_pct*100:.2f}%")
            self.risk_off_mode = True
            self._close_all_positions()

    return self.risk_off_mode
```

**Expected Impact**:
- Triggers during market-wide crashes (2015 China crash, COVID-19)
- Closes ALL positions across all baskets
- Prevents catastrophic losses
- Requires manual intervention to resume trading

### 4.5 Risk Management Summary

| Level | Limit | Trigger | Action |
|-------|-------|---------|--------|
| **Position Size** | Volatility-based | Always active | Scale position by `size` factor |
| **Per-Basket DD** | 15% | Basket NV drop | Close basket position only |
| **Portfolio DD** | 20% | Portfolio NV drop | Close ALL positions, risk-off mode |

**Risk Layering**:
```
Normal Operation → Position sizing active
           ↓
Commodity Issue → Per-basket DD (15%) → Close bad basket
           ↓
Systemic Crisis → Portfolio DD (20%) → Close everything
```

---

## 5. Regime Logic: River, Lake, Dead Zone

### 5.1 The Three Regimes

Trinity adapts strategy based on ADX (trend strength):

| Regime | ADX Range | Market State | Strategy | Hold Overnight? |
|--------|-----------|--------------|----------|-----------------|
| **River** | > River threshold (typically 39-43) | Strong trend | Trend-following | YES |
| **Lake** | < Lake threshold (typically 25-27) | Ranging/choppy | Mean-reversion | NO (intraday only) |
| **Dead Zone** | Between River and Lake | Uncertain | Hold | N/A |

### 5.2 River Mode (Trend-Following)

**Philosophy**: "The trend is your friend." Ride strong directional moves.

**Entry Conditions**:

```python
# River mode - Trend is strong
if adx > rules['adx_river']:
    regime = "RIVER"

    # LONG: Uptrend confirmed by volume
    if di_plus > di_minus and conviction > rules['conviction_bull']:
        signal = 1  # BUY
        # Hold overnight - big moves often continue

    # SHORT: Downtrend confirmed by volume
    elif di_minus > di_plus and conviction < rules['conviction_bear']:
        signal = -1  # SELL
        # Hold overnight - momentum continues
```

**Key Points**:
- **DI+ vs DI-**: Directional movement indicators show which side is winning
- **Conviction Filter**: Volume must confirm the move (prevents false breakouts)
- **Hold Overnight**: Trends often accelerate after hours (policy announcements, overseas moves)

**Example - Iron Ore Trend**:

```
Date: 2024-03-15 14:00
ADX: 45.2 (> 39.93 River threshold)
DI+: 35.8, DI-: 18.2  (Strong uptrend)
Conviction: 0.85 (> 0.58 bull threshold)
Close: 880, Upper Band: 920

Decision: BUY (River mode)
Reasoning: Strong uptrend, volume confirming
Action: Hold overnight - expecting multi-day trend
```

**Exit Logic**:
- ADX falls below Lake threshold (trend weakening)
- DI indicators reverse (trend changing direction)
- Conviction flips sign (volume no longer supporting)

### 5.3 Lake Mode (Mean-Reversion)

**Philosophy**: "Buy low, sell high" in choppy markets.

**Entry Conditions**:

```python
# Lake mode - Market is ranging
elif adx < rules['adx_lake']:
    regime = "LAKE"

    # BUY DIP: Price stretched low, volume supporting bounce
    if close < lower_band and conviction > rules['conviction_bull']:
        signal = 1  # BUY oversold bounce

    # SELL RIP: Price stretched high, volume supporting pullback
    elif close > upper_band and conviction < rules['conviction_bear']:
        signal = -1  # SELL overbought pullback

    # CRITICAL: Intraday only - exit before close
    if is_near_eod(timetag):
        signal = 0  # FORCE EXIT
```

**Key Points**:
- **Bollinger Band Extremes**: Price outside bands = stretched = reversion opportunity
- **Conviction Filter**: Volume must support reversion (prevents catching falling knives)
- **Intraday Only**: MUST exit by 14:55 (see Section 6)

**Example - Copper Range**:

```
Date: 2024-03-15 10:30
ADX: 22.3 (< 26.56 Lake threshold)
Close: 71,200
Lower Band: 71,500 (Price BELOW band - oversold)
Conviction: 40.5 (> 33.0 bull threshold)

Decision: BUY (Lake mode)
Reasoning: Oversold in ranging market, volume supporting bounce
Action: Enter long, set alarm for 14:55 exit

Date: 2024-03-15 14:55
Close: 71,450 (Small profit)
Decision: EXIT (forced by intraday rule)
Reasoning: Don't hold choppy market overnight
```

**Why Intraday Only?**
- Ranging markets have NO directional bias
- Overnight gaps in ranging markets are pure coin flips
- Avoids "gap risk" (open at loss despite being right intraday)
- See Section 6 for detailed rationale

### 5.4 Dead Zone (Hold)

**Philosophy**: "When in doubt, stay out."

**Conditions**:

```python
# Dead Zone - Uncertain market
else:
    # ADX between Lake and River thresholds
    regime = "DEAD_ZONE"
    signal = 0  # HOLD / CLOSE
```

**Key Points**:
- ADX between 25-27 (Lake) and 39-43 (River) = transition phase
- Market could be:
  - Transitioning from trend to range
  - Transitioning from range to trend
  - Just oscillating (whipsaw territory)
- **Safer to wait** than to pick wrong strategy

**Example - Gold Transition**:

```
Date: 2024-03-15 11:00
ADX: 32.5 (between 24.98 Lake and 40.91 River)
Close: 548.2
Bands: 547.5 - 549.0 (price in middle)
Conviction: 0.05 (near zero - no conviction)

Decision: HOLD (Dead Zone)
Reasoning: No clear regime, no clear signal
Action: Wait for ADX to clarify (above 40.91 or below 24.98)
```

**Dead Zone Benefits**:
- Avoids whipsaws (repeated small losses from false signals)
- Preserves capital for clear opportunities
- Reduces transaction costs
- Improves win rate (only trade when edge is clear)

### 5.5 Regime Detection Code Example

```python
def _determine_regime_and_signal(self, basket_idx, close, scout_data, rules):
    """Core regime detection and signal generation logic."""

    adx = scout_data['adx_value']
    di_plus = scout_data['di_plus']
    di_minus = scout_data['di_minus']
    conviction = scout_data['conviction_oscillator']
    lower_band = scout_data['lower_band']
    upper_band = scout_data['upper_band']

    signal = 0
    regime = "DEAD_ZONE"

    # === RIVER MODE (Trend-Following) ===
    if adx > rules['adx_river']:
        regime = "RIVER"

        # Uptrend with volume confirmation
        if di_plus > di_minus and conviction > rules['conviction_bull']:
            signal = 1
            logger.info(f"[{regime}] LONG: ADX={adx:.2f}, "
                       f"DI+={di_plus:.2f} > DI-={di_minus:.2f}, "
                       f"Conv={conviction:.2f}")

        # Downtrend with volume confirmation
        elif di_minus > di_plus and conviction < rules['conviction_bear']:
            signal = -1
            logger.info(f"[{regime}] SHORT: ADX={adx:.2f}, "
                       f"DI-={di_minus:.2f} > DI+={di_plus:.2f}, "
                       f"Conv={conviction:.2f}")

    # === LAKE MODE (Mean-Reversion) ===
    elif adx < rules['adx_lake']:
        regime = "LAKE"

        # Oversold with volume supporting bounce
        if close < lower_band and conviction > rules['conviction_bull']:
            signal = 1
            logger.info(f"[{regime}] BUY DIP: Price={close:.2f} < "
                       f"LowerBand={lower_band:.2f}, Conv={conviction:.2f}")

        # Overbought with volume supporting pullback
        elif close > upper_band and conviction < rules['conviction_bear']:
            signal = -1
            logger.info(f"[{regime}] SELL RIP: Price={close:.2f} > "
                       f"UpperBand={upper_band:.2f}, Conv={conviction:.2f}")

        # INTRADAY EXIT LOGIC (See Section 6)
        if self._is_near_eod(self.timetag):
            if signal != 0:
                logger.warning(f"[{regime}] FORCING EOD EXIT (was signal={signal})")
            signal = 0  # Force flat

    # === DEAD ZONE ===
    else:
        logger.debug(f"[DEAD_ZONE] ADX={adx:.2f} in range "
                    f"[{rules['adx_lake']:.2f}, {rules['adx_river']:.2f}]")

    return signal, regime
```

### 5.6 Regime Statistics (From Tuning)

Based on 2024 full-year data:

| Commodity | River % | Lake % | Dead Zone % | Most Common Regime |
|-----------|---------|--------|-------------|--------------------|
| Iron Ore (i) | 30% | 30% | 40% | Dead Zone |
| Copper (cu) | 28% | 32% | 40% | Lake (ranging) |
| Gold (au) | 35% | 25% | 40% | River (trending) |
| Crude (sc) | 32% | 28% | 40% | Balanced |

**Key Insight**: Markets spend ~40% of time in Dead Zone - regime unclear. This is NORMAL and expected. Strategy effectiveness comes from trading the clear 60% aggressively.

---

## 6. Intraday Exit Logic

### 6.1 Why Lake Mode Exits at 14:55

**The Problem**: Overnight gap risk in ranging markets.

**Scenario**:

```
Day 1, 14:30: Copper in LAKE mode
- ADX: 22 (ranging)
- Close: 71,200
- Lower Band: 71,500
- Entry: LONG (oversold bounce)

Day 1, 15:00: Market closes
- Close: 71,350 (+150 points, +0.21% profit)

Day 2, 09:00: Market opens
- Open: 70,800 (-550 points from yesterday close)
- Reason: Overnight Chile production report (bearish surprise)

Result: -0.77% loss despite correct intraday read
```

**The Insight**:
- In ranging markets (Lake mode), there's NO directional bias
- Overnight news/events are random relative to position
- Expected value of holding overnight = 0, but variance is high
- Intraday mean-reversion has edge, overnight has none

**The Solution**: Force exit at 14:55 in Lake mode.

### 6.2 Why River Mode Holds Overnight

**The Contrast**: Trends have directional bias that persists.

**Scenario**:

```
Day 1, 14:30: Iron Ore in RIVER mode
- ADX: 45 (strong uptrend)
- DI+: 35, DI-: 18
- Close: 880
- Entry: LONG (trend following)

Day 1, 15:00: Market closes
- Close: 882 (+2 points)

Day 2, 09:00: Market opens
- Open: 890 (+8 points from yesterday close)
- Reason: Trend continuation + China stimulus rumors

Result: +10 points total, trend accelerates
```

**The Insight**:
- In trending markets (River mode), directional bias persists
- Overnight news often REINFORCES existing trend
- Big policy moves happen after hours (China announcements)
- Expected value of holding overnight > 0

**The Solution**: Hold overnight in River mode, capture multi-day trends.

### 6.3 Implementation

```python
def _is_near_eod(self, timetag):
    """
    Check if time is near end-of-day (14:50-15:00).
    Chinese futures day session closes at 15:00.
    We exit Lake positions 5-10 minutes early.
    """
    if timetag is None:
        return False

    s_time = str(timetag)
    if len(s_time) < 12:  # Format: YYYYMMDDHHMMSS
        return False

    hhmm = int(s_time[8:12])  # Extract HHMM

    # 14:50-15:00 = near EOD
    return 1450 <= hhmm < 1500

def _apply_intraday_exit_logic(self, signal, regime, timetag):
    """
    Force exit Lake positions near EOD.
    River positions are exempt (hold overnight for trend).
    """
    if regime == "LAKE" and self._is_near_eod(timetag):
        if signal != 0:
            logger.warning(f"[LAKE MODE EOD EXIT] Forcing signal 0->0 (was {signal})")
        return 0  # Force flat

    return signal  # Keep original signal
```

### 6.4 Session Handling

Chinese futures markets have TWO sessions:

| Session | Time | Description |
|---------|------|-------------|
| **Day** | 09:00 - 15:00 | Main trading session |
| **Night** | 21:00 - 02:30 (next day) | Extended trading (most commodities) |

**Complications**:
1. Not all commodities have night sessions
2. Night sessions have lower liquidity
3. Exit logic must handle both sessions

**Simplified Approach for Phase-2**:

```python
def _is_near_eod(self, timetag):
    """
    For Phase-2, we only handle day session EOD (14:50-15:00).
    Night session complexity deferred to Phase-3.
    """
    s_time = str(timetag)
    if len(s_time) < 12:
        return False

    hhmm = int(s_time[8:12])

    # Day session EOD
    if 1450 <= hhmm < 1500:
        return True

    # Night session EOD (optional, for future enhancement)
    # if 2320 <= hhmm or hhmm < 30:  # 23:20-00:30
    #     return True

    return False
```

**Future Enhancement**: Implement night session exit logic (23:20-02:30) if backtests show night trades are significant.

### 6.5 Expected Impact

**Backtest Expectations**:

| Scenario | Without Intraday Rule | With Intraday Rule |
|----------|----------------------|-------------------|
| **Lake Mode Trades** | 100 trades, 52 winners | 100 trades, 58 winners |
| **Avg Win/Loss** | +0.3% / -0.4% | +0.25% / -0.25% |
| **Max Loss** | -2.5% (gap down) | -0.8% (intraday) |
| **Sharpe Ratio** | 0.8 | 1.2 |

**Why Improvement?**:
- Eliminates random overnight gaps in ranging markets
- Reduces tail risk (max loss)
- Improves win rate (no unlucky gap losses)
- Slightly reduces avg win (miss overnight favorable gaps), but reduces avg loss more

---

## 7. File Structure

Phase-2 creates the following files:

```
TrinityStrategy/
├── WOS_CaptainStrategy.py          # Main Phase-2 implementation (NEW)
├── trinity_playbook.py             # Tuned parameters lookup table (NEW)
├── uin_captain.json                # Captain input config (NEW)
├── uout_captain.json               # Captain output config (NEW)
├── .vscode/
│   └── launch.json                 # Add Captain test configs (MODIFY)
├── docs/
│   ├── Phase-2-Captain-Implementation.md  # This document (NEW)
│   └── Phase-2.md                  # Initial design notes (EXISTING)
├── trinity_parameters.json         # Tuning results (EXISTING)
├── TrinityStrategy.py              # Phase-1 Scouts (EXISTING)
├── uin.json                        # Phase-1 inputs (EXISTING)
├── uout.json                       # Phase-1 outputs (EXISTING)
└── wos/                            # WOS documentation (EXISTING)
```

### 7.1 New Files Description

| File | Purpose | Size | Complexity |
|------|---------|------|------------|
| **WOS_CaptainStrategy.py** | Main Tier-2 strategy | ~600 lines | HIGH |
| **trinity_playbook.py** | Parameter lookup | ~50 lines | LOW |
| **uin_captain.json** | Input configuration | ~60 lines | MEDIUM |
| **uout_captain.json** | Output configuration | ~30 lines | LOW |

---

## 8. Implementation Architecture

### 8.1 Class Hierarchy

```
csc3.composite_strategy (Framework base class)
         ↓
WOS_CaptainStrategy (Our implementation)
         ↓ (has-a, 12 instances)
   strategyc3.strategy (Basket)
```

### 8.2 WOS_CaptainStrategy Structure

```python
class WOS_CaptainStrategy(csc3.composite_strategy):
    """
    Trinity Tier-2 Composite Strategy.
    Manages 12 independent baskets, one per commodity.
    Implements regime-adaptive logic with risk management.
    """

    def __init__(self, initial_cash=10_000_000.0):
        # CRITICAL: Initialize these BEFORE super().__init__()
        self.bar_index_this_run = -1
        self.latest_sv = None

        # Commodity-basket mapping
        self.basket_to_commodity = {}  # {0: (b'DCE', b'i<00>'), ...}
        self.commodity_to_basket = {}  # {(b'DCE', b'i<00>'): 0, ...}

        # Parsers (2 per commodity)
        self.quote_parsers = {}  # {(market, code): SampleQuote}
        self.scout_parsers = {}  # {(market, code): ScoutParser}

        # Initialize composite with baskets
        super().__init__(initial_cash, BASKET_COUNT)

        # Metadata
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'  # Arbitrary, composite spans markets
        self.code = b'COMPOSITE<00>'
        self.meta_name = "WOS_CaptainStrategy"
        self.revision = (1 << 32) - 1
        self.timetag_ = None

        # Output fields
        self.bar_index = 0
        self.active_positions = 0
        self.total_signals_generated = 0
        self.portfolio_nv = 1.0

        # Risk management state
        self.max_basket_dd_pct = 0.15
        self.max_portfolio_dd_pct = 0.20
        self.basket_peak_nv = {i: 1.0 for i in range(BASKET_COUNT)}
        self.portfolio_peak_nv = 1.0
        self.risk_off_mode = False

        # Current cycle data
        self.current_quotes = {}  # {(market, code): close_price}
        self.current_scouts = {}  # {(market, code): scout_data_dict}
```

### 8.3 The _allocate() Method

**Purpose**: Initialize basket structure and capital allocation.

```python
# In __init__(), after super().__init__()
for basket_idx in range(BASKET_COUNT):
    market, code = self.basket_to_commodity[basket_idx]
    basket_capital = initial_cash / BASKET_COUNT

    self._allocate(
        meta_id=basket_idx,
        market=market,
        code=code,
        money=basket_capital,
        leverage=1.0
    )

    logger.info(f"Allocated basket {basket_idx}: {market.decode()}/{code.decode()} "
                f"with ${basket_capital:,.2f}")
```

**What `_allocate()` Does**:
1. Creates `strategyc3.strategy` instance (basket)
2. Transfers `money` from `self.cash` to `basket.cash`
3. Sets `basket.market = market`, `basket.code = code`
4. Sets `basket.meta_id = meta_id` (for lookups)
5. **Sets `basket.target_instrument = b''`** (EMPTY, unusable)
6. Adds basket to `self.strategies` list
7. Adds basket to `self.strategy_map` dict

**What It Does NOT Do**:
- Does NOT set `target_instrument` to actual contract (e.g., `i2501`)
- Does NOT subscribe basket to market data
- Does NOT populate contract rolling information

**Why `target_instrument` Stays Empty**:
- `_allocate()` happens in `__init__()` (before any market data)
- Actual trading contract determined by exchange reference data
- Reference data arrives via `on_reference()` callback
- Framework populates `target_instrument` via rolling mechanism

### 8.4 Two Parsers Per Commodity

**Why Two Parsers?**

Because we need data from TWO sources:
1. **SampleQuote**: Current close price (from global namespace)
2. **ScoutParser**: ADX, Bands, Conviction (from private namespace)

**Parser Initialization**:

```python
def _initialize_parsers(self):
    """Create SampleQuote and ScoutParser for each commodity."""
    for market, codes in COMMODITIES.items():
        for code in codes:
            key = (market, code)

            # SampleQuote parser
            quote = SampleQuote()
            quote.market = market
            quote.code = code
            quote.granularity = granularity
            self.quote_parsers[key] = quote

            # ScoutParser
            scout = ScoutParser()
            scout.market = market
            scout.code = code
            scout.granularity = granularity
            self.scout_parsers[key] = scout

    logger.info(f"Initialized {len(self.quote_parsers)} quote parsers and "
                f"{len(self.scout_parsers)} scout parsers")
```

### 8.5 on_bar() Routing Logic

**Purpose**: Route incoming bars to correct parser.

```python
def on_bar(self, bar: pc.StructValue):
    """
    Main bar processing callback.
    Routes bars to parsers and triggers cycle processing.
    """
    market = bar.get_market()
    code = bar.get_stock_code()
    tm = bar.get_time_tag()
    ns = bar.get_namespace()
    meta_id = bar.get_meta_id()

    # Initialize timetag
    if self.timetag is None:
        self.timetag = tm

    # Cycle boundary detection
    if self.timetag < tm:
        # End of previous cycle - process signals
        self._on_cycle_pass(tm)

        # Generate output
        results = []
        if self.bar_index > 0:
            results.append(self.sv_copy())

        # Advance to new cycle
        self.timetag = tm
        self.bar_index += 1

        # Clear cycle data
        self.current_quotes.clear()
        self.current_scouts.clear()

        return results

    # Parse incoming bar
    self._parse_bar(bar)

    # Forward to baskets (for price updates)
    super().on_bar(bar)

    return []

def _parse_bar(self, bar: pc.StructValue):
    """Parse bar into appropriate parser."""
    market = bar.get_market()
    code = bar.get_stock_code()
    ns = bar.get_namespace()
    meta_id = bar.get_meta_id()

    # Extract commodity code (strip <00> if present)
    commodity = self.calc_commodity(code)
    key = (market, commodity)

    # Parse SampleQuote (global namespace)
    if ns == pc.namespace_global:
        if key in self.quote_parsers:
            parser = self.quote_parsers[key]
            if meta_id == parser.meta_id:
                parser.from_sv(bar)
                self.current_quotes[key] = parser.close

    # Parse Scout outputs (private namespace)
    elif ns == pc.namespace_private:
        if key in self.scout_parsers:
            parser = self.scout_parsers[key]
            if meta_id == parser.meta_id:
                parser.from_sv(bar)
                self.current_scouts[key] = {
                    'adx_value': parser.adx_value,
                    'di_plus': parser.di_plus,
                    'di_minus': parser.di_minus,
                    'upper_band': parser.upper_band,
                    'middle_band': parser.middle_band,
                    'lower_band': parser.lower_band,
                    'conviction_oscillator': parser.conviction_oscillator
                }
```

**Key Points**:
- **Cycle boundary**: `timetag < tm` triggers signal processing
- **Namespace routing**: `namespace_global` → quotes, `namespace_private` → scouts
- **Temporary storage**: `current_quotes` and `current_scouts` cleared each cycle
- **Basket forwarding**: `super().on_bar(bar)` updates basket prices

### 8.6 _on_cycle_pass() Signal Processing

**Purpose**: Generate and execute trading signals for all baskets.

```python
def _on_cycle_pass(self, time_tag):
    """
    Process end of cycle - generate signals for all baskets.
    Called when timetag advances (new 15-min bar starts).
    """
    # Framework cycle processing
    super()._on_cycle_pass(time_tag)

    # Check portfolio-level risk
    if self._check_portfolio_drawdown():
        logger.error("Portfolio in RISK-OFF mode, no new signals")
        return

    # Process each basket
    for basket_idx in range(BASKET_COUNT):
        self._process_basket_signal(basket_idx)

    # Update metrics
    self._update_metrics()

    # Persist state
    self._save()
    self._sync()

    # Logging
    logger.info(f"Bar {self.bar_index}: NV={self.nv:.4f}, PV={self.pv:,.2f}, "
                f"Active={self.active_positions}/{BASKET_COUNT}, "
                f"Signals={self.total_signals_generated}")

def _process_basket_signal(self, basket_idx):
    """Generate and execute signal for one basket."""
    market, code = self.basket_to_commodity[basket_idx]
    key = (market, code)

    # Check data availability
    if key not in self.current_quotes or key not in self.current_scouts:
        return  # Skip this basket if data missing

    close = self.current_quotes[key]
    scout_data = self.current_scouts[key]

    # Get tuned parameters
    if code not in TRINITY_PLAYBOOK:
        logger.warning(f"No playbook rules for {code.decode()}")
        return

    rules = TRINITY_PLAYBOOK[code]

    # Check per-basket drawdown
    if self._check_basket_drawdown(basket_idx):
        return  # Basket hit DD limit

    # Generate signal
    signal, regime = self._determine_regime_and_signal(
        basket_idx, close, scout_data, rules
    )

    # Execute if signal changed
    basket = self.strategies[basket_idx]
    if signal != basket.signal:
        self._execute_basket_signal(basket_idx, signal, regime, rules)
```

**Signal Execution**:

```python
def _execute_basket_signal(self, basket_idx, signal, regime, rules):
    """Execute signal for a basket with position sizing."""
    basket = self.strategies[basket_idx]
    market, code = self.basket_to_commodity[basket_idx]

    # Apply risk parity sizing
    size = rules['size']
    leverage = 1.0 * size  # Base leverage scaled by volatility size

    if signal == 0:
        # Close position
        logger.info(f"CLOSE basket {basket_idx} ({market.decode()}/{code.decode()}): "
                   f"{regime}")
        basket._signal(basket.price, basket.timetag, 0)

    elif signal == 1:
        # Open long
        logger.info(f"LONG basket {basket_idx} ({market.decode()}/{code.decode()}): "
                   f"{regime}, size={size:.3f}, lev={leverage:.2f}")
        basket._fit_position(leverage)
        basket._signal(basket.price, basket.timetag, -1)  # -1 to go long (framework quirk)

    elif signal == -1:
        # Open short
        logger.info(f"SHORT basket {basket_idx} ({market.decode()}/{code.decode()}): "
                   f"{regime}, size={size:.3f}, lev={leverage:.2f}")
        basket._fit_position(leverage)
        basket._signal(basket.price, basket.timetag, 1)  # 1 to go short (framework quirk)

    self.total_signals_generated += 1
```

**Note**: Framework signal convention is inverted:
- `basket._signal(..., -1)` → Go LONG
- `basket._signal(..., 1)` → Go SHORT
- `basket._signal(..., 0)` → Close position

### 8.7 MANDATORY Callbacks

**Critical**: These three callbacks are REQUIRED for composite strategies.

#### on_reference() - Contract Rolling

```python
async def on_reference(market, tradeday, data, timetag, timestring):
    """
    CRITICAL: Forward reference data to baskets.
    Without this, baskets cannot determine target_instrument.
    """
    global strategy
    strategy.on_reference(bytes(market, 'utf-8'), tradeday, data)
```

**What It Does**:
1. Forwards exchange reference data to `composite_strategy.on_reference()`
2. Framework routes to each basket's `strategy.on_reference()`
3. Each basket extracts:
   - Available contracts (e.g., i2501, i2505, i2509)
   - Contract expiry dates
   - Contract multipliers
   - Commission rates
4. Each basket determines `leading_contract` (highest volume/OI)
5. Populates `basket.target_instrument` with actual contract code

**Failure Mode**:
- Empty implementation → `basket.target_instrument = b''` (stays empty)
- Market data arrives as `DCE/i2501`
- Framework tries to match `i2501` against `b''`
- No match → `basket.on_bar()` never called
- `basket.price = 0` → No P&L tracking → Trading fails

#### on_tradeday_begin() - Session Start

```python
async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    """
    Called at start of each trading day.
    Triggers contract rolling if needed.
    """
    global strategy
    strategy.on_tradeday_begin(bytes(market, 'utf-8'), tradeday)
```

**What It Does**:
1. Framework checks each basket's `leading_contract` (set by `on_reference()`)
2. If `leading_contract` changed (e.g., rolled from i2501 to i2505):
   - Update `basket.target_instrument = new_leading_contract`
   - Close position in old contract
   - Open position in new contract (if signal active)
3. Logs rolling events

#### on_tradeday_end() - Session End

```python
async def on_tradeday_end(market, tradeday, timetag, timestring):
    """
    Called at end of each trading day.
    Handles EOD settlement and metrics.
    """
    global strategy
    strategy.on_tradeday_end(bytes(market, 'utf-8'), tradeday)
```

**What It Does**:
1. Framework updates basket settlement prices
2. Calculates EOD P&L
3. Updates performance metrics
4. Persists state to database

**Callback Summary**:

| Callback | Frequency | Purpose | Required? |
|----------|-----------|---------|-----------|
| `on_reference()` | 1x per day (market open) | Populate contract info | **YES** |
| `on_tradeday_begin()` | 1x per day (session start) | Trigger rolling | **YES** |
| `on_tradeday_end()` | 1x per day (session end) | EOD settlement | **YES** |

---

## 9. Testing Workflow

### 9.1 Test Sequence

**Phase-2 testing follows a four-stage process**:

1. **Quick Test (7 days)**: Verify implementation works
2. **Visual Validation**: Inspect signals via notebook
3. **Full Backtest (1 year)**: Generate performance metrics
4. **Replay Consistency**: Ensure deterministic behavior

### 9.2 Quick Test (7 Days)

**Purpose**: Fast smoke test to catch implementation errors.

**Configuration** (add to `.vscode/launch.json`):

```json
{
    "name": "WOS_CaptainStrategy - Quick Test (7 days)",
    "type": "debugpy",
    "request": "launch",
    "program": "/home/wolverine/bin/running/calculator3_test.py",
    "args": [
        "--testcase", "${workspaceFolder}",
        "--algoname", "WOS_CaptainStrategy",
        "--sourcefile", "WOS_CaptainStrategy.py",
        "--start", "20241025000000",
        "--end", "20241101000000",
        "--granularity", "900",
        "--tm", "wss://10.99.100.116:4433/tm",
        "--tm-master", "10.99.100.116:6102",
        "--rails", "https://10.99.100.116:4433/private-api/",
        "--token", "58abd12edbde042536637bfba9d20d5faf366ef481651cdbb046b1c3b4f7bf7a97ae7a2e6e5dc8fe05cd91147c8906f8a82aaa1bb1356d8cb3d6a076eadf5b5a",
        "--category", "2",
        "--is-managed", "1",
        "--restore-length", "864000000",
        "--multiproc", "1"
    ],
    "cwd": "${workspaceFolder}",
    "console": "integratedTerminal",
    "justMyCode": false,
    "env": {
        "PYTHONPATH": "/home/wolverine/bin/running"
    }
}
```

**Key Difference from Phase-1**: `--category 2` (Tier-2 strategy)

**Execution**:
1. Press `F5` in VS Code
2. Select: **"WOS_CaptainStrategy - Quick Test (7 days)"**
3. Monitor console for logs:
   ```
   [2025-11-13 10:15:00][INFO] Allocated basket 0: DCE/i<00> with $833,333.33
   [2025-11-13 10:15:00][INFO] Allocated basket 1: DCE/j<00> with $833,333.33
   ...
   [2025-11-13 10:15:05][INFO] Bar 1: NV=1.0000, PV=10,000,000.00, Active=0/12, Signals=0
   [2025-11-13 10:15:10][INFO] LONG basket 0 (DCE/i<00>): RIVER, size=1.000, lev=1.00
   [2025-11-13 10:15:10][INFO] Bar 2: NV=1.0002, PV=10,002,000.00, Active=1/12, Signals=1
   ...
   [2025-11-13 10:20:00][INFO] ON FINISHED
   ```
4. Wait for "ON FINISHED" message
5. **IMPORTANT**: Manually stop debugger (Shift+F5)

**Success Criteria**:
- No exceptions/crashes
- Baskets initialize (12 allocation messages)
- Signals generate (Active > 0)
- NV changes (gains/losses tracked)
- "ON FINISHED" appears

### 9.3 Visual Validation

**Purpose**: Inspect signals and regime detection via Jupyter notebook.

**Prerequisites**:
1. Quick Test or Full Backtest completed
2. Data persisted to server
3. Debugger stopped

**Notebook**: `WOS_CaptainStrategy_viz.ipynb` (NEW, to be created)

**Key Plots**:

1. **Panel 1: Price + Signals**
   - Candlestick price chart
   - Buy/Sell arrows (from strategy signals)
   - Colored background (green=RIVER, blue=LAKE, gray=DEAD_ZONE)

2. **Panel 2: ADX Regime**
   - ADX line
   - River threshold (horizontal line)
   - Lake threshold (horizontal line)
   - Shaded regions for regimes

3. **Panel 3: Conviction**
   - Conviction oscillator
   - Bull/Bear thresholds
   - Zero line

4. **Panel 4: Performance**
   - Portfolio NV curve
   - Drawdown curve
   - Active positions count

**Validation Checklist**:
- [ ] Buy signals occur in RIVER (uptrend) or LAKE (oversold)
- [ ] Sell signals occur in RIVER (downtrend) or LAKE (overbought)
- [ ] No signals in DEAD_ZONE
- [ ] Lake positions exit by 14:55 (check timestamps)
- [ ] River positions hold overnight (check timestamps)
- [ ] NV curve generally upward (if not, investigate)

### 9.4 Full Backtest (1 Year)

**Purpose**: Generate statistically significant performance metrics.

**Configuration**:

```json
{
    "name": "WOS_CaptainStrategy - Full Backtest (1 year)",
    "type": "debugpy",
    "request": "launch",
    "program": "/home/wolverine/bin/running/calculator3_test.py",
    "args": [
        "--testcase", "${workspaceFolder}",
        "--algoname", "WOS_CaptainStrategy",
        "--sourcefile", "WOS_CaptainStrategy.py",
        "--start", "20240101000000",
        "--end", "20241231235959",
        "--granularity", "900",
        "--tm", "wss://10.99.100.116:4433/tm",
        "--tm-master", "10.99.100.116:6102",
        "--rails", "https://10.99.100.116:4433/private-api/",
        "--token", "58abd12edbde042536637bfba9d20d5faf366ef481651cdbb046b1c3b4f7bf7a97ae7a2e6e5dc8fe05cd91147c8906f8a82aaa1bb1356d8cb3d6a076eadf5b5a",
        "--category", "2",
        "--is-managed", "1",
        "--restore-length", "864000000",
        "--multiproc", "1"
    ],
    "cwd": "${workspaceFolder}",
    "console": "integratedTerminal",
    "justMyCode": false,
    "env": {
        "PYTHONPATH": "/home/wolverine/bin/running"
    }
}
```

**Execution Time**: 10-20 minutes (depends on server load)

**Expected Output**:
```
[2025-11-13 11:00:00][INFO] Processing 2024-01-01 to 2024-12-31
[2025-11-13 11:00:05][INFO] Total bars processed: ~26,000
[2025-11-13 11:00:05][INFO] Total signals generated: ~1,500
[2025-11-13 11:00:05][INFO] Final NV: 1.2850 (+28.5% return)
[2025-11-13 11:00:05][INFO] Max drawdown: -8.3%
[2025-11-13 11:00:05][INFO] Sharpe ratio: 1.85
[2025-11-13 11:00:05][INFO] ON FINISHED
```

### 9.5 Replay Consistency Test

**Purpose**: Ensure strategy is stateless and deterministic.

**Test Script**: `test_resuming_mode_captain.py` (NEW, to be created)

**What It Tests**:
1. Run full backtest, save outputs
2. Run backtest in chunks (simulate interruption + resume)
3. Compare outputs - must be IDENTICAL

**Expected Result**:
```
[TEST] Full run: NV=1.2850, Signals=1,523
[TEST] Chunked run: NV=1.2850, Signals=1,523
[TEST] Outputs match: ✓ PASS
```

**Failure Modes**:
- State leakage between bars (forgot to clear cycle data)
- Non-deterministic random() calls (none should exist)
- Order-dependent dictionary iteration (use sorted keys)

---

## 10. Success Criteria

### 10.1 Implementation Success

Phase-2 is successfully implemented when:

- [ ] **Code Quality**
  - [ ] No syntax errors, imports resolve
  - [ ] Follows WOS doctrines (stateless, online algorithms)
  - [ ] Code style consistent with Phase-1
  - [ ] Comments explain "why", not "what"

- [ ] **Functional Correctness**
  - [ ] Quick test runs without crashes
  - [ ] All 12 baskets initialize correctly
  - [ ] Signals generate for all commodities
  - [ ] Parsers correctly extract SampleQuote + Scout data
  - [ ] Regime detection logic matches specification
  - [ ] Intraday exit logic triggers at 14:55 (Lake mode)
  - [ ] Risk management enforces DD limits

- [ ] **Data Flow**
  - [ ] `on_reference()` callback implemented → `target_instrument` populated
  - [ ] `on_tradeday_begin/end()` callbacks implemented
  - [ ] SampleQuote parser gets close prices (namespace_global)
  - [ ] ScoutParser gets indicators (namespace_private)
  - [ ] Baskets receive market data (price updates)

- [ ] **Output Validation**
  - [ ] Full backtest completes successfully
  - [ ] Output fields populated (NV, PV, signals)
  - [ ] Visualization notebook generates plots
  - [ ] Replay consistency test passes

### 10.2 Performance Success

Phase-2 is performance-validated when:

- [ ] **Return Metrics**
  - [ ] Annual return: 15-35% (target: 25%)
  - [ ] Sharpe ratio: > 1.5 (target: 2.0)
  - [ ] Max drawdown: < 15% (target: 10%)
  - [ ] Win rate: > 50% (target: 55%)

- [ ] **Risk Metrics**
  - [ ] Portfolio DD never exceeds 20%
  - [ ] Per-basket DD never exceeds 15%
  - [ ] No single basket contributes > 30% of total risk
  - [ ] Volatility annualized: 12-18%

- [ ] **Regime Performance**
  - [ ] River mode: Profitable in trending periods
  - [ ] Lake mode: Profitable in ranging periods
  - [ ] Dead Zone: No significant losses (small opportunity cost)
  - [ ] Intraday rule: Improves Lake mode Sharpe by 20-40%

- [ ] **Per-Commodity Performance**
  - [ ] All 12 commodities tradeable (no data gaps)
  - [ ] High-vol commodities (cu, al) don't dominate risk
  - [ ] Low-vol commodities (au, sc) contribute meaningfully
  - [ ] No single commodity causes > 10% portfolio DD

### 10.3 Deployment Readiness

Phase-2 is deployment-ready when:

- [ ] **Documentation**
  - [ ] This guide complete and accurate
  - [ ] Code docstrings comprehensive
  - [ ] Parameter rationale documented
  - [ ] Known issues/limitations listed

- [ ] **Testing**
  - [ ] Quick test suite passes (7 days)
  - [ ] Full backtest suite passes (1 year)
  - [ ] Replay consistency test passes
  - [ ] Visual validation completed
  - [ ] Edge cases tested (missing data, holidays, etc.)

- [ ] **Operations**
  - [ ] Logging comprehensive but not verbose
  - [ ] Error handling graceful (no crashes on bad data)
  - [ ] Performance acceptable (< 50ms per bar)
  - [ ] Memory usage stable (no leaks)

---

## 11. Expected Performance Metrics

### 11.1 Baseline Expectations

Based on similar strategies and Phase-1 tuning results:

| Metric | Conservative | Target | Optimistic |
|--------|--------------|--------|------------|
| **Annual Return** | 15% | 25% | 35% |
| **Sharpe Ratio** | 1.2 | 2.0 | 2.5 |
| **Max Drawdown** | 15% | 10% | 8% |
| **Win Rate** | 48% | 55% | 60% |
| **Profit Factor** | 1.3 | 1.8 | 2.2 |
| **Trades/Year** | 1,200 | 1,500 | 1,800 |

### 11.2 Per-Regime Performance

**River Mode (Trend-Following)**:

| Metric | Expected |
|--------|----------|
| Contribution to Return | 60-70% |
| Win Rate | 45-50% |
| Avg Win/Loss Ratio | 2.5-3.0 |
| Max Consecutive Losses | 5-7 |
| Best Performing Commodity | Gold (au), Iron Ore (i) |

**Lake Mode (Mean-Reversion)**:

| Metric | Expected |
|--------|----------|
| Contribution to Return | 30-40% |
| Win Rate | 60-65% |
| Avg Win/Loss Ratio | 1.2-1.5 |
| Max Consecutive Losses | 3-4 |
| Best Performing Commodity | Copper (cu), Crude Oil (sc) |

**Dead Zone**:

| Metric | Expected |
|--------|----------|
| Contribution to Return | 0-5% (opportunity cost) |
| Time in Dead Zone | 35-45% |
| False Signal Avoidance | 80-90% |

### 11.3 Per-Commodity Performance

| Commodity | Expected Return | Sharpe | Max DD | Notes |
|-----------|----------------|--------|--------|-------|
| **i (Iron Ore)** | 20-30% | 1.8-2.2 | 10% | Baseline, reliable trends |
| **j (Coke)** | 15-25% | 1.5-2.0 | 12% | Follows iron ore |
| **cu (Copper)** | 25-40% | 1.6-2.2 | 15% | High vol, good ranges |
| **al (Aluminum)** | 18-28% | 1.7-2.1 | 11% | Moderate vol |
| **au (Gold)** | 12-20% | 2.0-2.5 | 6% | Low vol, safe haven |
| **sc (Crude Oil)** | 22-35% | 1.8-2.3 | 12% | Good trends + ranges |
| **rb (Rebar)** | 15-25% | 1.5-2.0 | 13% | Follows construction |
| **TA (PTA)** | 18-28% | 1.6-2.1 | 11% | Chemical cycles |
| **MA (Methanol)** | 20-30% | 1.7-2.2 | 10% | Energy proxy |
| **ru (Rubber)** | 15-28% | 1.4-2.0 | 14% | High vol, sporadic |
| **m (Soybeans)** | 18-25% | 1.6-2.0 | 11% | Seasonal patterns |
| **y (Palm Oil)** | 16-26% | 1.5-2.0 | 13% | Agri commodity |

### 11.4 Monthly Returns Distribution

**Expected Pattern**:

| Month | Avg Return | Notes |
|-------|------------|-------|
| Jan | +1.5% | Post-holiday rally |
| Feb | +0.5% | Chinese New Year volatility |
| Mar | +2.5% | Spring construction start |
| Apr | +2.0% | Peak construction season |
| May | +1.0% | Consolidation |
| Jun | +1.5% | Mid-year positioning |
| Jul | +0.5% | Summer lull |
| Aug | +1.0% | Back-to-work rally |
| Sep | +2.5% | Fall construction push |
| Oct | +3.0% | Peak seasonal demand |
| Nov | +2.0% | Winter prep |
| Dec | +1.0% | Year-end profit-taking |

### 11.5 Risk-Adjusted Metrics

**Information Ratio**: 1.5-2.0
**Sortino Ratio**: 2.5-3.5
**Calmar Ratio**: 2.0-3.0
**Omega Ratio**: 1.8-2.2

**Monthly Volatility**: 3-5%
**Annualized Volatility**: 12-18%
**Downside Volatility**: 6-10%

**Max Consecutive Wins**: 8-12
**Max Consecutive Losses**: 5-8

### 11.6 Benchmark Comparisons

**vs. Buy-and-Hold Iron Ore**:
- Trinity expected: +25% return, 10% DD, 2.0 Sharpe
- Buy-hold expected: +15% return, 18% DD, 0.8 Sharpe
- Trinity advantage: Lower DD, higher Sharpe

**vs. Balanced Commodity Index**:
- Trinity expected: +25% return, 10% DD
- Index expected: +12% return, 15% DD
- Trinity advantage: Higher return, lower DD

**vs. Phase-1 Single-Commodity**:
- Trinity (12 commodities): +25% return, 10% DD, 2.0 Sharpe
- Phase-1 (iron ore only): +20% return, 12% DD, 1.6 Sharpe
- Trinity advantage: Diversification benefit

---

## 12. Troubleshooting Guide

### 12.1 Common Issues

#### Issue: basket.price = 0.00 (Never Updates)

**Symptoms**:
- Baskets initialize successfully
- Signals generate
- But basket.price stays at 0
- basket.pv frozen at initial capital
- No P&L tracking

**Root Cause**: `on_reference()` callback not implemented or not forwarding.

**Diagnosis**:

```python
# Add logging in _on_cycle_pass()
for i, basket in enumerate(self.strategies):
    logger.info(f"Basket {i}: target={basket.target_instrument}, "
                f"price={basket.price}, pv={basket.pv}")
```

Expected: `target_instrument = b'i2501'` (actual contract)
If see: `target_instrument = b''` (empty) → `on_reference()` not working

**Solution**:

```python
async def on_reference(market, tradeday, data, timetag, timestring):
    """CRITICAL: Forward reference data to baskets."""
    global strategy
    strategy.on_reference(bytes(market, 'utf-8'), tradeday, data)
```

#### Issue: No Signals Generated

**Symptoms**:
- Baskets initialize
- Parsers receive data
- But `total_signals_generated = 0`
- `active_positions = 0`

**Root Causes**:

1. **Missing Data**: Quotes or scouts not arriving

**Diagnosis**:
```python
# In _process_basket_signal()
logger.info(f"Basket {basket_idx}: key={key}, "
            f"has_quote={key in self.current_quotes}, "
            f"has_scout={key in self.current_scouts}")
```

**Solution**: Check uin_captain.json matches Phase-1 uout.json

2. **Thresholds Too Strict**: No market state meets criteria

**Diagnosis**:
```python
# In _determine_regime_and_signal()
logger.info(f"ADX={adx:.2f} (River>{rules['adx_river']:.2f}, "
            f"Lake<{rules['adx_lake']:.2f})")
```

**Solution**: Adjust thresholds in trinity_playbook.py

3. **Logic Error**: Signal logic broken

**Diagnosis**: Add breakpoint in `_determine_regime_and_signal()`, step through

**Solution**: Fix logic bug

#### Issue: All Signals in Dead Zone

**Symptoms**:
- ADX always between River and Lake thresholds
- No trades execute
- regime = "DEAD_ZONE" for all bars

**Root Cause**: Thresholds too wide (River too high, Lake too low).

**Diagnosis**:
```python
# Check threshold ranges
for code, rules in TRINITY_PLAYBOOK.items():
    logger.info(f"{code.decode()}: Lake={rules['adx_lake']:.2f}, "
                f"River={rules['adx_river']:.2f}, "
                f"Gap={rules['adx_river'] - rules['adx_lake']:.2f}")
```

Typical gap: 12-15 points
If gap > 20: Thresholds too strict

**Solution**: Re-run tuning with different percentiles (e.g., 0.25/0.75 instead of 0.3/0.7)

#### Issue: Lake Positions Not Exiting at 14:55

**Symptoms**:
- Lake mode trades occurring
- But positions held overnight
- No "EOD EXIT" log messages

**Root Cause**: `_is_near_eod()` not triggering.

**Diagnosis**:
```python
# In _is_near_eod()
s_time = str(timetag)
hhmm = int(s_time[8:12])
logger.info(f"EOD check: timetag={timetag}, hhmm={hhmm}, "
            f"near_eod={1450 <= hhmm < 1500}")
```

**Common Mistakes**:
- Wrong timetag format (not YYYYMMDDHHMMSS)
- Wrong timezone (server time vs local time)
- Wrong slice indices (`s_time[8:12]` must extract HHMM)

**Solution**: Verify timetag format, adjust slice indices

#### Issue: Positions Opening with price=0

**Symptoms**:
- Signal generates
- basket._signal() called
- But trade uses price=0 → 0 contracts opened

**Root Cause**: basket.price not updated yet (market data delayed).

**Diagnosis**:
```python
# In _execute_basket_signal(), before basket._signal()
logger.info(f"Executing: basket.price={basket.price}, "
            f"basket.timetag={basket.timetag}")
```

If price=0: Market data routing broken (see "basket.price=0" issue above)

**Solution**: Fix `on_reference()` callback first

#### Issue: MemoryError or Slow Performance

**Symptoms**:
- Backtest slows down over time
- Memory usage grows continuously
- Eventually crashes with MemoryError

**Root Causes**:

1. **Cycle data not cleared**: `current_quotes`, `current_scouts` accumulating

**Solution**:
```python
# In on_bar(), after _on_cycle_pass()
self.current_quotes.clear()
self.current_scouts.clear()
```

2. **Logging too verbose**: Writing GB of logs

**Solution**: Reduce logger.info() calls, use logger.debug()

3. **Not using online algorithms**: Accidentally storing arrays

**Solution**: Review code for any `list.append()` or `numpy.array()` calls

#### Issue: Different Results on Re-run

**Symptoms**:
- Run backtest, get NV=1.25
- Run again (same parameters), get NV=1.27
- Replay consistency test fails

**Root Cause**: Non-deterministic behavior (state leakage, random(), dict iteration).

**Diagnosis**:
1. Check for `random()` calls: `grep -r "random\(\)" *.py`
2. Check for unsorted dict iteration: `grep -r "\.items\(\)" *.py`
3. Check for state leakage: Review cycle data clearing

**Solution**: Fix non-deterministic code, always use sorted keys

### 12.2 Debugging Techniques

#### Verbose Logging

```python
# Add to __init__()
self.debug_mode = True  # Toggle for extra logging

# In signal processing
if self.debug_mode:
    logger.info(f"[DEBUG] Basket {basket_idx}: "
                f"close={close:.2f}, "
                f"adx={scout_data['adx_value']:.2f}, "
                f"conv={scout_data['conviction_oscillator']:.2f}, "
                f"signal={signal}, regime={regime}")
```

#### Breakpoint Debugging

**Key Breakpoints**:

| File | Line | Purpose |
|------|------|---------|
| WOS_CaptainStrategy.py | `_allocate()` call | Check basket initialization |
| WOS_CaptainStrategy.py | `_parse_bar()` | Check data arrival |
| WOS_CaptainStrategy.py | `_on_cycle_pass()` | Check cycle processing |
| WOS_CaptainStrategy.py | `_determine_regime_and_signal()` | Check signal logic |
| WOS_CaptainStrategy.py | `_execute_basket_signal()` | Check trade execution |

#### Temporary Output Files

```python
# In _on_cycle_pass()
if self.bar_index % 100 == 0:  # Every 100 bars
    with open(f'/tmp/captain_debug_{self.bar_index}.json', 'w') as f:
        debug_state = {
            'bar_index': self.bar_index,
            'nv': self.nv,
            'pv': self.pv,
            'active_positions': self.active_positions,
            'baskets': [
                {
                    'idx': i,
                    'market': basket.market.decode(),
                    'code': basket.code.decode(),
                    'signal': basket.signal,
                    'price': basket.price,
                    'nv': basket.nv,
                    'pv': basket.pv
                }
                for i, basket in enumerate(self.strategies)
            ]
        }
        json.dump(debug_state, f, indent=2)
```

#### Comparison with Phase-1

**Validate inputs match Phase-1 outputs**:

```python
# In WOS_CaptainStrategy, after parsing scouts
phase1_adx = scout_data['adx_value']

# In Phase-1 viz notebook, for same timetag
phase1_adx_from_viz = 42.5

# Compare
assert abs(phase1_adx - phase1_adx_from_viz) < 0.01, "Scout data mismatch"
```

### 12.3 Performance Optimization

#### Reduce Parser Overhead

```python
# Instead of creating new parser dicts every cycle
# Pre-allocate and reuse
self.scout_data_cache = {
    key: {
        'adx_value': 0.0,
        'di_plus': 0.0,
        # ...
    }
    for key in self.scout_parsers.keys()
}

# In _parse_bar(), update in-place
cache = self.scout_data_cache[key]
cache['adx_value'] = parser.adx_value
cache['di_plus'] = parser.di_plus
# ...
```

#### Batch Logging

```python
# Instead of logging every basket every cycle
# Log summary once per cycle
if self.bar_index % 10 == 0:  # Every 10 cycles
    active_baskets = [i for i, b in enumerate(self.strategies) if b.signal != 0]
    logger.info(f"Bar {self.bar_index}: Active baskets: {active_baskets}")
```

#### Lazy Evaluation

```python
# Only process baskets with new data
def _process_basket_signal(self, basket_idx):
    key = self.basket_to_commodity[basket_idx]

    # Skip if no new data this cycle
    if key not in self.current_quotes or key not in self.current_scouts:
        return

    # Only process if data changed
    # (Add hash comparison if needed)
```

---

## Conclusion

This document provides a complete blueprint for implementing Trinity Strategy Phase-2. Key takeaways:

1. **12-Basket Architecture**: One basket per commodity enables independent regime detection, risk management, and contract rolling

2. **Two-Parser Design**: SampleQuote (close price) + ScoutParser (indicators) provides all needed data

3. **Three-Regime Logic**: River (trend-following), Lake (mean-reversion), Dead Zone (hold) adapts to market conditions

4. **Intraday Exit Rule**: Lake mode exits at 14:55 to avoid overnight gap risk in ranging markets

5. **Risk Management**: Three layers (position sizing, per-basket DD, portfolio DD) contain risk

6. **MANDATORY Callbacks**: `on_reference()`, `on_tradeday_begin()`, `on_tradeday_end()` are required for basket operation

7. **Testing Workflow**: Quick test → Visual validation → Full backtest → Replay consistency

Follow this guide systematically, and Phase-2 will be a robust, transparent, adaptive multi-commodity trading system.

---

**Next Steps**: Begin implementation by creating `WOS_CaptainStrategy.py` and `trinity_playbook.py`.

**Questions?** Review WOS Chapter 8 (Tier-2 Composite) and this document's troubleshooting section.

**Good luck building the Captain!**
