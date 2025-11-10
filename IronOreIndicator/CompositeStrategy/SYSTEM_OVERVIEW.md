# Multi-Commodity Trading System Overview

**A Two-Tier Signal-Based Trading Architecture**

Version: 2.0
Last Updated: 2025-11-10

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Tier-1: Signal Generation](#tier-1-signal-generation)
3. [Tier-2: Portfolio Management](#tier-2-portfolio-management)
4. [Signal Processing Pipeline](#signal-processing-pipeline)
5. [Position Sizing Logic](#position-sizing-logic)
6. [Risk Management](#risk-management)
7. [Trade Execution](#trade-execution)
8. [Exit Strategy](#exit-strategy)
9. [Real-World Example](#real-world-example)

---

## System Architecture

### The Big Picture

This is a **two-tier trading system** that separates signal generation from portfolio management:

```
┌─────────────────────────────────────────────────────────────┐
│                        TIER-2                               │
│                   CompositeStrategy                         │
│            (Portfolio Manager & Risk Controller)            │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Basket 0   │  │  Basket 1   │  │  Basket 2   │       │
│  │   DCE/i     │  │  SHFE/cu    │  │   DCE/m     │       │
│  │  ¥300,000   │  │  ¥300,000   │  │  ¥300,000   │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         ↑                ↑                ↑                │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
    Signals │          Signals │        Signals │
          │                │                │
┌─────────┴────────────────┴────────────────┴────────────────┐
│                        TIER-1                               │
│                  Signal Generators                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │IronOreInd.   │  │CopperInd.    │  │SoybeanInd.   │    │
│  │   (DCE/i)    │  │  (SHFE/cu)   │  │   (DCE/m)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         ↑                ↑                ↑                │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
     Market Data      Market Data      Market Data
```

**Key Principle**:
- **Tier-1** indicators analyze market data and produce trading signals
- **Tier-2** composite strategy consumes those signals and executes trades
- Each tier is independent and can be developed/tested separately

---

## Tier-1: Signal Generation

### What Tier-1 Indicators Do

Each Tier-1 indicator is a **signal generator** for one commodity. It analyzes price action using multiple technical indicators and produces a unified trading signal.

### The Three Indicators

**1. IronOreIndicator (DCE/i)**
- **Market**: DCE (Dalian Commodity Exchange)
- **Commodity**: Iron Ore futures (i2501, i2505, etc.)
- **Granularity**: 15 minutes (900s bars)

**2. CopperIndicator (SHFE/cu)**
- **Market**: SHFE (Shanghai Futures Exchange)
- **Commodity**: Copper futures (cu2412, cu2501, etc.)
- **Granularity**: 15 minutes (900s bars)

**3. SoybeanIndicator (DCE/m)**
- **Market**: DCE (Dalian Commodity Exchange)
- **Commodity**: Soybean meal futures (m2501, m2505, etc.)
- **Granularity**: 15 minutes (900s bars)

### Technical Indicators Used (Common Across All Three)

Each Tier-1 indicator combines multiple technical analysis tools:

```
INPUT: OHLCV Bar (Open, High, Low, Close, Volume)
  ↓
┌─────────────────────────────────────────┐
│   Multi-Indicator Analysis              │
│                                         │
│   1. EMA Crossovers (12/26/50)         │
│      → Trend detection                  │
│                                         │
│   2. MACD (12, 26, 9)                  │
│      → Momentum confirmation            │
│                                         │
│   3. RSI (14-period)                   │
│      → Overbought/oversold              │
│                                         │
│   4. Bollinger Bands (20, 2)           │
│      → Volatility & support/resistance  │
│                                         │
│   5. ATR (14-period)                   │
│      → Volatility measurement           │
│                                         │
│   6. Volume Analysis                    │
│      → Liquidity confirmation           │
└─────────────────────────────────────────┘
  ↓
OUTPUT: Signal Package
```

### Signal Package Format

Each Tier-1 indicator outputs a comprehensive signal package every 15 minutes:

```python
{
    # TRADING SIGNALS
    'signal': 1,              # -1 (SHORT) / 0 (NEUTRAL) / 1 (LONG)
    'confidence': 0.75,       # 0.0-1.0 (conviction level)
    'signal_strength': 0.68,  # 0.0-1.0 (multi-factor strength)
    'regime': 2,              # 1=uptrend, 2=downtrend, 3=ranging, 4=chaos

    # PRICE DATA
    'close': 777.5,           # Current close price

    # TECHNICAL INDICATORS (for analysis)
    'ema_12': 775.2,
    'ema_26': 772.8,
    'ema_50': 770.1,
    'macd': 2.4,
    'rsi': 58.3,
    'bb_upper': 785.0,
    'bb_lower': 765.0,
    'atr': 8.5,
}
```

### Signal Generation Logic (Example: Long Signal)

Here's how a Tier-1 indicator decides to generate a LONG signal:

```
1. TREND CHECK (EMA Crossover)
   ✓ ema_12 > ema_26 > ema_50  → Uptrend confirmed

2. MOMENTUM CHECK (MACD)
   ✓ macd > 0 and macd > signal_line  → Bullish momentum

3. MEAN REVERSION CHECK (RSI)
   ✓ 30 < rsi < 70  → Not overbought/oversold

4. VOLUME CHECK
   ✓ volume > 1.2 × volume_ema  → High liquidity

5. BOLLINGER BANDS CHECK
   ✓ price near lower band → Potential bounce

IF all checks pass:
   signal = 1 (LONG)
   confidence = weighted average of indicator strengths
   signal_strength = volume × momentum factor
   regime = uptrend (1)
```

### Key Insight: Independence

Each Tier-1 indicator operates **independently**:
- Iron ore might be LONG while copper is SHORT
- Each analyzes its own commodity's price action
- No correlation analysis at Tier-1 level
- Diversity provides portfolio-level protection

---

## Tier-2: Portfolio Management

### What CompositeStrategy Does

The CompositeStrategy is the **portfolio manager**. It:
1. Receives signals from all 3 Tier-1 indicators
2. Manages capital allocation across commodities
3. Sizes positions based on signal quality
4. Executes trades through "baskets"
5. Manages risk at portfolio level
6. Coordinates exits across positions

### Capital Allocation Model

**Starting Capital**: ¥1,000,000

**Pre-Allocation Structure**:
```
Total Portfolio: ¥1,000,000
├── Basket 0 (DCE/i):   ¥300,000 (30%)
├── Basket 1 (SHFE/cu): ¥300,000 (30%)
├── Basket 2 (DCE/m):   ¥300,000 (30%)
└── Composite Cash:     ¥100,000 (10% reserve)
```

**Important**: Each basket has **pre-allocated** capital that it manages independently. The composite cash is a reserve for rebalancing or emergencies.

### The Basket Concept

A **basket** is a mini-portfolio dedicated to one commodity:

```python
Basket {
    market: b'DCE'
    commodity: b'i'
    allocated_capital: ¥300,000
    current_position: 0 (or LONG/SHORT)
    leverage: 1.0-1.4x
    entry_price: 0.0
    pv: ¥300,000  # Portfolio value (changes with P&L)
}
```

Each basket:
- Receives signals from its Tier-1 indicator
- Trades independently
- Manages its own capital
- Can use leverage (up to 1.4x)

---

## Signal Processing Pipeline

### Step-by-Step: From Signal to Trade

**Every 15 minutes**, this pipeline executes:

```
1. SIGNAL ARRIVAL
   ├─ IronOreIndicator → signal package → Basket 0
   ├─ CopperIndicator  → signal package → Basket 1
   └─ SoybeanIndicator → signal package → Basket 2

2. PORTFOLIO-LEVEL ANALYSIS
   ├─ Aggregate conviction across baskets
   ├─ Count chaos regimes
   ├─ Determine dynamic cash reserve target
   └─ Calculate portfolio-level risk

3. FOR EACH BASKET:

   3a. IF in position (signal != 0):
       → Check exit conditions
       → If should exit, close position
       → Go to next basket

   3b. IF flat (signal == 0):
       → Check entry conditions
       → If should enter, calculate position size
       → Execute entry
       → Go to next basket

4. UPDATE METRICS
   ├─ Portfolio value
   ├─ Active positions
   ├─ Exposure percentage
   ├─ Drawdown
   └─ Cash reserve

5. LOGGING & OUTPUT
   └─ Export state to private namespace
```

---

## Position Sizing Logic

### Tiered Sizing Based on Signal Quality

Position sizing is **graduated**, not binary. The size depends on signal conviction.

### Conviction Score Calculation

```python
confidence = signal_data['confidence']        # 0.0-1.0
strength = signal_data['signal_strength']     # 0.0-1.0

# Weighted combination (confidence matters more)
conviction = (confidence × 0.6) + (strength × 0.4)
```

### Three Size Tiers

**STRONG Conviction (conviction ≥ 0.55)**
```
Position Size: 80-100% of basket capital
Leverage: 1.3-1.4x
Example: ¥240k-¥300k × 1.4 = ¥336k-¥420k notional

When: All indicators strongly aligned, high volume
```

**MEDIUM Conviction (0.35 ≤ conviction < 0.55)**
```
Position Size: 40-60% of basket capital
Leverage: 1.1-1.2x
Example: ¥120k-¥180k × 1.2 = ¥144k-¥216k notional

When: Moderate signal quality, some confirmation
```

**WEAK Conviction (0.20 ≤ conviction < 0.35)**
```
Position Size: 20-30% of basket capital
Leverage: 1.0-1.1x
Example: ¥60k-¥90k × 1.05 = ¥63k-¥95k notional

When: Signal present but weak, low confidence
```

### Size Calculation Formula

```python
# Base size tier
if conviction >= 0.55:
    size_pct = 0.80 + (conviction - 0.55) × 0.44  # 80-100%
elif conviction >= 0.35:
    size_pct = 0.40 + (conviction - 0.35) × 1.0   # 40-60%
else:
    size_pct = 0.20 + (conviction - 0.20) × 0.67  # 20-30%

# Risk adjustment for high volatility
if chaos_baskets >= 2:
    size_pct *= 0.70  # Reduce by 30%

# Leverage calculation
leverage = 1.0 + (conviction × 1.4)
leverage = min(leverage, 1.4)  # Cap at 1.4x

# Final position value
position_value = basket.pv × size_pct × leverage
```

### Example: Real Position Sizing

**Scenario**: Iron ore signal arrives

```
Signal Data:
  confidence = 0.72
  signal_strength = 0.65
  regime = 1 (uptrend)

Calculation:
  conviction = (0.72 × 0.6) + (0.65 × 0.4) = 0.692

  ✓ conviction >= 0.55 → STRONG tier

  size_pct = 0.80 + (0.692 - 0.55) × 0.44 = 0.862 (86.2%)
  leverage = 1.0 + (0.692 × 1.4) = 1.969 → capped at 1.4

  position_value = ¥300,000 × 0.862 × 1.4 = ¥362,040

Result: LONG 86% of basket capital with 1.4x leverage
```

---

## Risk Management

### Multi-Layer Risk Controls

The system has **7 layers** of risk management:

### Layer 1: Total Exposure Limit

```
Maximum Portfolio Exposure: 90%

Check: sum(active_basket_values) / portfolio_value ≤ 0.90

Prevents: Over-leverage across portfolio
```

### Layer 2: Leverage Limit

```
Maximum Leverage per Basket: 1.4x

Check: position_value / basket_capital ≤ 1.4

Prevents: Excessive leverage on single position
```

### Layer 3: Drawdown Limit

```
Maximum Portfolio Drawdown: 10%

Check: (peak_value - current_value) / peak_value ≤ 0.10

Action: If breached, close ALL positions (circuit breaker)
```

### Layer 4: Daily Loss Limit

```
Maximum Daily Loss: 3%

Check: (day_start_value - current_value) / day_start_value ≤ 0.03

Action: If breached, no new trades for rest of day
```

### Layer 5: Position-Level Stop Loss

```
Stop Loss per Position: 3%

Check: For LONG: (entry - current) / entry ≥ 0.03
       For SHORT: (current - entry) / entry ≥ 0.03

Action: Immediate exit
```

### Layer 6: Dynamic Cash Reserve

```
Adaptive Cash Reserve:
  - Aggressive: 5% (strong signals, low volatility)
  - Balanced: 15% (normal conditions)
  - Defensive: 25% (high volatility, weak signals)

Check: cash / portfolio_value ≥ target_reserve

Ensures: Liquidity for rebalancing and exits
```

### Layer 7: Chaos Regime Protection

```
Chaos Regime Detection:
  - Count baskets with regime == 4 (chaos)

If chaos_baskets >= 2:
  - Reduce new position sizes by 30%
  - Exit losing positions (P&L < -1%)

Prevents: Trading in highly volatile, directionless markets
```

---

## Trade Execution

### Entry Process

**Decision Flow**:

```
1. SIGNAL CHECK
   ├─ Is signal directional? (signal == 1 or -1)
   ├─ Is confidence sufficient? (confidence >= 0.20)
   └─ Is strength sufficient? (signal_strength >= 0.15)

   ✗ NO → Skip entry
   ✓ YES → Proceed

2. POSITION SIZE CALCULATION
   ├─ Calculate conviction score
   ├─ Determine size tier (STRONG/MEDIUM/WEAK)
   ├─ Calculate position percentage
   ├─ Calculate leverage
   └─ Compute position value

3. RISK CHECKS
   ├─ Check total exposure limit
   ├─ Check drawdown limit
   └─ Check daily loss limit

   ✗ BLOCKED → Proceed to fallback chain
   ✓ PASS → Execute trade

4. FALLBACK CHAIN (if blocked)
   ├─ Fallback 1: Reduce size by 40%
   ├─ Fallback 2: Reduce leverage to 1.1x
   └─ Fallback 3: Minimum position (20%, 1.0x)

   ✗ Still blocked → Log and skip
   ✓ Pass → Execute trade

5. EXECUTE
   ├─ Set basket leverage
   ├─ Call basket._signal(price, time, signal)
   ├─ Record entry price
   └─ Log: "LONG basket 0 [STRONG]: DCE/i, size=85%, lev=1.4..."
```

### The Fallback Chain

**Purpose**: Never block valid trades unnecessarily.

**Scenario**: Original position blocked by exposure limit

```
Original:
  Position: ¥362k (86% × 1.4x)
  Reason: "Total exposure 92% exceeds limit 90%"

Fallback 1: Reduce size by 40%
  Position: ¥217k (51.6% × 1.4x)
  Check: Still blocked? → Try Fallback 2

Fallback 2: Reduce leverage to 1.1x
  Position: ¥168k (51.6% × 1.1x)
  Check: Still blocked? → Try Fallback 3

Fallback 3: Minimum position
  Position: ¥60k (20% × 1.0x)
  Check: Still blocked? → Log and skip

Result: Trade executed at reduced size instead of blocked
```

---

## Exit Strategy

### Multi-Trigger Exit System

Exits are **smarter than entries**. Multiple triggers protect profits and limit losses.

### Exit Trigger 1: Profit Targets

```
10% Profit Target:
  ├─ Condition: P&L >= 10%
  ├─ Action: FULL exit (100%)
  └─ Reason: Lock in substantial gains

5% Profit Target (Conditional):
  ├─ Condition: P&L >= 5% AND conviction < 0.40
  ├─ Action: FULL exit (100%)
  └─ Reason: Protect gains when signal weakens
```

### Exit Trigger 2: Stop Loss

```
3% Stop Loss:
  ├─ Condition: P&L <= -3%
  ├─ Action: IMMEDIATE full exit
  └─ Reason: Limit losses per position
```

### Exit Trigger 3: Signal Reversal

```
Signal Flips:
  ├─ Example: Was LONG (signal=1), now signal=-1
  ├─ Action: IMMEDIATE full exit
  └─ Reason: Indicator predicting opposite direction
```

### Exit Trigger 4: Confidence Degradation

```
Low Confidence:
  ├─ Condition: confidence < 0.20
  ├─ Action: FULL exit
  └─ Reason: Indicator no longer confident

Confidence Drop + Loss:
  ├─ Condition: confidence < 0.30 AND P&L < -1%
  ├─ Action: FULL exit
  └─ Reason: Weak signal + losing trade
```

### Exit Trigger 5: Chaos Regime

```
High Volatility Exit:
  ├─ Condition: chaos_baskets >= 2 AND P&L < -1%
  ├─ Action: FULL exit
  └─ Reason: Multiple baskets in chaos, cut losses
```

### Exit Decision Tree

```
FOR each basket with active position:

1. Calculate P&L
   ├─ For LONG: (current - entry) / entry
   └─ For SHORT: (entry - current) / entry

2. Check profit targets
   ├─ IF P&L >= 10%: EXIT [profit_target_10pct]
   ├─ IF P&L >= 5% AND conviction < 0.40: EXIT [profit_protect_5pct]
   └─ ELSE: Continue

3. Check stop loss
   ├─ IF P&L <= -3%: EXIT [stop_loss]
   └─ ELSE: Continue

4. Check signal reversal
   ├─ IF signal × position < 0: EXIT [signal_reversal]
   └─ ELSE: Continue

5. Check confidence
   ├─ IF confidence < 0.20: EXIT [low_confidence]
   ├─ IF confidence < 0.30 AND P&L < -1%: EXIT [confidence_drop_with_loss]
   └─ ELSE: Continue

6. Check chaos regime
   ├─ IF chaos_baskets >= 2 AND P&L < -1%: EXIT [chaos_regime_exit]
   └─ ELSE: Hold position
```

---

## Real-World Example

### Complete Trading Cycle

Let's walk through a complete trading day for the system.

### Starting State

```
Time: 2024-10-25 09:00:00
Portfolio Value: ¥1,000,000
Active Positions: 0
Cash: ¥100,000 (composite)
Basket Capitals: ¥300k each (all flat)
```

---

### Bar 1: 09:00 AM - Iron Ore Entry Signal

**Tier-1 Signal Arrives**:
```python
{
    'signal': 1,              # LONG
    'confidence': 0.68,
    'signal_strength': 0.72,
    'regime': 1,              # Uptrend
    'close': 765.0,
}
```

**Tier-2 Processing**:
```
1. Calculate conviction:
   conviction = (0.68 × 0.6) + (0.72 × 0.4) = 0.696

2. Determine tier: STRONG (conviction >= 0.55)
   size_pct = 0.80 + (0.696 - 0.55) × 0.44 = 0.864 (86%)
   leverage = 1.0 + (0.696 × 1.4) = 1.974 → capped at 1.4

3. Position value:
   ¥300,000 × 0.864 × 1.4 = ¥362,880

4. Risk checks:
   - Total exposure: 36.3% < 90% ✓
   - Drawdown: 0% < 10% ✓
   - Daily loss: 0% < 3% ✓

5. EXECUTE
```

**Log Output**:
```
[09:00] LONG basket 0 [STRONG]: DCE/i, size=86%, lev=1.4,
        price=765.00, conv=0.70 (conf=0.68, str=0.72)
```

**Updated State**:
```
Active Positions: 1
Basket 0: LONG i2501 @ 765.0, size=¥362,880
Portfolio Exposure: 36.3%
```

---

### Bar 3: 09:30 AM - Copper Entry Signal

**Tier-1 Signal Arrives**:
```python
{
    'signal': -1,             # SHORT
    'confidence': 0.58,
    'signal_strength': 0.45,
    'regime': 2,              # Downtrend
    'close': 76770.0,
}
```

**Tier-2 Processing**:
```
1. Calculate conviction:
   conviction = (0.58 × 0.6) + (0.45 × 0.4) = 0.528

2. Determine tier: MEDIUM (0.35 ≤ conviction < 0.55)
   size_pct = 0.40 + (0.528 - 0.35) × 1.0 = 0.578 (58%)
   leverage = 1.0 + (0.528 × 1.4) = 1.739 → capped at 1.4

3. Position value:
   ¥300,000 × 0.578 × 1.4 = ¥242,760

4. Risk checks:
   - Total exposure: 60.6% < 90% ✓

5. EXECUTE
```

**Log Output**:
```
[09:30] SHORT basket 1 [MEDIUM]: SHFE/cu, size=58%, lev=1.4,
        price=76770.00, conv=0.53 (conf=0.58, str=0.45)
```

**Updated State**:
```
Active Positions: 2
Basket 0: LONG i2501 @ 765.0
Basket 1: SHORT cu2412 @ 76770.0
Portfolio Exposure: 60.6%
```

---

### Bar 15: 12:45 PM - Iron Ore Profit Target

**Price Movement**:
```
Iron ore: 765.0 → 842.5 (+10.1%)
```

**Exit Trigger Check**:
```
P&L = (842.5 - 765.0) / 765.0 = 0.101 (10.1%)

✓ P&L >= 10% → Trigger: Profit Target
```

**Log Output**:
```
[12:45] PROFIT TARGET: Basket 0 (DCE/i) hit 10% profit (10.1%)
[12:45] CLOSE basket 0 [profit_target_10pct]: DCE/i, LONG
        entry=765.00, exit=842.50, P&L=+10.1%
```

**P&L Calculation**:
```
Entry: ¥362,880
Exit: ¥399,548
Realized P&L: +¥36,668
```

**Updated State**:
```
Active Positions: 1
Basket 0: FLAT (¥336,668 capital now)
Basket 1: SHORT cu2412 @ 76770.0
Portfolio Value: ¥1,036,668
```

---

### Bar 22: 15:00 PM - Copper Stop Loss

**Price Movement**:
```
Copper: 76770.0 → 79105.0 (+3.04%)
For SHORT: P&L = (76770 - 79105) / 76770 = -3.04%
```

**Exit Trigger Check**:
```
P&L = -3.04%

✓ P&L <= -3% → Trigger: Stop Loss
```

**Log Output**:
```
[15:00] STOP-LOSS: Basket 1 (SHFE/cu) hit 3% loss (-3.04%)
[15:00] CLOSE basket 1 [stop_loss]: SHFE/cu, SHORT
        entry=76770.00, exit=79105.00, P&L=-3.04%
```

**P&L Calculation**:
```
Entry: ¥242,760
Exit: ¥235,380
Realized P&L: -¥7,380
```

**Updated State**:
```
Active Positions: 0
Portfolio Value: ¥1,029,288
Net P&L for day: +¥29,288 (+2.93%)
```

---

### Summary of Trading Day

**Trades Executed**:
```
1. Iron Ore LONG (STRONG tier, 86% size)
   → +10.1% profit = +¥36,668

2. Copper SHORT (MEDIUM tier, 58% size)
   → -3.04% loss = -¥7,380

Net Result: +¥29,288 (+2.93%)
```

**Key Observations**:
- Different position sizes based on conviction
- Diversified (LONG + SHORT)
- Profit target protected gains
- Stop loss limited damage
- System working as designed ✓

---

## Key Principles Summary

### 1. **Separation of Concerns**
- Tier-1: Signal generation (technical analysis)
- Tier-2: Portfolio management (risk & execution)

### 2. **Graduated Position Sizing**
- Not binary (all-or-nothing)
- Size scales with signal quality
- 3 tiers: STRONG (80-100%), MEDIUM (40-60%), WEAK (20-30%)

### 3. **Multi-Layer Risk Management**
- 7 independent risk controls
- Portfolio-level AND position-level
- Circuit breakers for extreme scenarios

### 4. **Adaptive Behavior**
- Reduce sizes in high volatility
- Dynamic cash reserves
- Fallback chains prevent unnecessary blocks

### 5. **Smart Exits**
- Multiple exit triggers
- Protect profits (10%, 5% targets)
- Limit losses (3% stop)
- React to signal changes

### 6. **Independent Baskets**
- Each commodity managed separately
- Pre-allocated capital
- Can be LONG/SHORT simultaneously
- Portfolio diversification

---

## Replication Guide

To replicate this system:

### Step 1: Implement Tier-1 Indicators

For each commodity:
1. Calculate technical indicators (EMA, MACD, RSI, BB, ATR)
2. Combine into unified signal (-1/0/1)
3. Calculate confidence (0.0-1.0)
4. Calculate signal_strength (0.0-1.0)
5. Detect regime (1-4)
6. Output to private namespace every 15 minutes

### Step 2: Implement Tier-2 Composite

1. **Initialize**:
   - Pre-allocate capital to baskets (30% each)
   - Set up risk manager
   - Create signal parsers

2. **On Bar Arrival**:
   - Route market data to baskets
   - Parse Tier-1 signals
   - Process trading logic

3. **Process Trading Signals**:
   - For each basket, check exits first
   - Then check entries
   - Calculate position sizes
   - Execute trades via framework

4. **Risk Management**:
   - Check all 7 risk layers
   - Update drawdown tracking
   - Enforce circuit breakers

5. **Exit Management**:
   - Check all 5 exit triggers
   - Execute exits immediately
   - Log reasons

### Step 3: Testing

1. **Unit Test**: Individual components
2. **Quick Test**: 7 days of data
3. **Replay Test**: Ensure determinism
4. **Full Backtest**: Multi-month validation
5. **Analysis**: Review P&L curves, drawdowns, exposure

### Step 4: Optimization

1. Tune thresholds (confidence, strength)
2. Adjust position size percentages
3. Modify leverage limits
4. Refine exit triggers
5. Iterate based on performance

---

## Appendix: Configuration Quick Reference

### Tier-1 Indicator Thresholds

```python
# Entry thresholds
MIN_CONFIDENCE = 0.20
MIN_SIGNAL_STRENGTH = 0.15

# Exit thresholds
EXIT_CONFIDENCE = 0.30
CRITICAL_EXIT_CONFIDENCE = 0.20
```

### Tier-2 Position Sizing

```python
# Conviction tiers
STRONG_THRESHOLD = 0.55    # 80-100% size
MEDIUM_THRESHOLD = 0.35    # 40-60% size
WEAK_THRESHOLD = 0.20      # 20-30% size

# Leverage
MAX_LEVERAGE = 1.4
CONFIDENCE_WEIGHT = 0.6
STRENGTH_WEIGHT = 0.4
```

### Risk Limits

```python
# Portfolio limits
MAX_TOTAL_EXPOSURE = 0.90    # 90%
MIN_CASH_RESERVE = 0.10      # 10%
MAX_PORTFOLIO_DD = 0.10      # 10%
MAX_DAILY_LOSS = 0.03        # 3%

# Position limits
STOP_LOSS = 0.03             # 3%
PROFIT_TARGET_1 = 0.10       # 10%
PROFIT_TARGET_2 = 0.05       # 5%
```

### Cash Reserve Targets

```python
AGGRESSIVE_RESERVE = 0.05    # 5%
BALANCED_RESERVE = 0.15      # 15%
DEFENSIVE_RESERVE = 0.25     # 25%
```

---

**End of System Overview**

*This document provides a complete understanding of the two-tier trading system architecture, signal generation, position sizing, risk management, and execution logic. Use it as a reference for development, testing, and optimization.*
