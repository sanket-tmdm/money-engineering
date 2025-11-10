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

### Position Sizing with Fixed Leverage

**IMPORTANT**: WOS framework uses **FIXED 1.5x leverage** for all trades. Dynamic leverage is not supported.

All trades execute with: `¥300,000 × 1.5x = ¥450,000 buying power`

**Contract Sizing by Instrument:**
```
Copper (SHFE/cu):   ¥450k / ¥400k = 1 contract per trade
Iron Ore (DCE/i):   ¥450k / ¥78k  = 5-6 contracts per trade
Soybean (DCE/m):    ¥450k / ¥27k  = 16-17 contracts per trade

Fixed leverage ensures:
- Copper trades consistently (was 0 contracts at 1.0x)
- Predictable position sizing across all instruments
- Safe, manageable risk profile (max 1.5x exposure)
```

**Risk Management by Conviction:**

**STRONG Conviction (conviction ≥ 0.55)**
```
Risk: Tighter stops (2.0%), earlier profit targets (8%)
When: All indicators strongly aligned, high volume
```

**MEDIUM Conviction (0.35 ≤ conviction < 0.55)**
```
Risk: Balanced stops (2.5%), standard profit targets (10%)
When: Moderate signal quality, some confirmation
```

**WEAK Conviction (0.20 ≤ conviction < 0.35)**
```
Risk: Conservative stops (3.0%), standard profit targets (10%)
When: Signal present but weak, low confidence
```

### Position Sizing Formula

```python
# WOS framework limitation: All trades use FIXED 1.5x leverage
# Position sizing is determined by contract sizing only

# Fixed parameters
basket_capital = ¥300,000
allocation_leverage = 1.5
buying_power = basket_capital × allocation_leverage = ¥450,000

# Determine conviction tier (for risk parameter selection)
if conviction >= 0.55:
    tier = 'STRONG'
    stop_loss = 0.020  # 2%
    profit_target = 0.08  # 8%
elif conviction >= 0.35:
    tier = 'MEDIUM'
    stop_loss = 0.025  # 2.5%
    profit_target = 0.10  # 10%
else:
    tier = 'WEAK'
    stop_loss = 0.030  # 3%
    profit_target = 0.10  # 10%

# Contract sizing (WOS framework determines this)
contracts = buying_power / contract_size
# Copper: ¥450k / ¥400k = 1 contract
# Iron ore: ¥450k / ¥78k = 5-6 contracts
# Soybean: ¥450k / ¥27k = 16-17 contracts
```

### Example: Real Position Sizing

**Scenario**: Iron ore STRONG signal

```
Signal Data:
  confidence = 0.72
  signal_strength = 0.65
  regime = 1 (uptrend)

Calculation:
  conviction = (0.72 × 0.6) + (0.65 × 0.4) = 0.692

  ✓ conviction >= 0.55 → STRONG tier

  # Fixed leverage system
  buying_power = ¥300,000 × 1.5 = ¥450,000

  # Iron ore contract size
  contract_size = 780 × 100 = ¥78,000

  # Contracts executed
  contracts = ¥450,000 / ¥78,000 = 5.77 → 5 contracts

  # Actual notional
  position_value = 5 × ¥78,000 = ¥390,000

  # Risk parameters (STRONG tier)
  stop_loss = 2.0%
  profit_target = 8%

Result: LONG 5 iron ore contracts, ¥390k notional (1.3x effective leverage)
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

### Layer 2: Fixed Leverage System

```
Fixed Allocation Leverage: 1.5x for ALL trades

WOS Framework Limitation:
  - All trades execute with fixed ¥450k buying power per basket
  - Dynamic leverage NOT supported by WOS framework
  - Position sizing controlled by contract sizing only

Contract Sizing by Instrument:
  Copper (SHFE/cu):   ¥450k / ¥400k = 1 contract
  Iron Ore (DCE/i):   ¥450k / ¥78k  = 5-6 contracts
  Soybean (DCE/m):    ¥450k / ¥27k  = 16-17 contracts

Benefits:
  - Predictable position sizing
  - Safe, conservative leverage (1.5x max)
  - Copper trades consistently (was 0 at 1.0x)
  - No over-leverage risk

Prevents: Over-leveraging disasters (51% circuit breaker events)
```

### Layer 3: Conviction-Based Stop Loss

```
Stop-Loss by Conviction Tier (Fixed 1.5x leverage):
  STRONG: 2.0% stop
  MEDIUM: 2.5% stop
  WEAK: 3.0% stop

Logic: Higher conviction = tighter stops
       → Stronger signals should work quickly or exit

Prevents: Excessive losses on weak signals
```

### Layer 4: Profit Targets

```
Profit Target by Conviction:
  STRONG: 8% target (earlier exit on strong moves)
  MEDIUM: 10% target (standard exit)
  WEAK: 10% target (standard exit)

Logic: Take profits faster on strong conviction trades
       → Lock in gains when indicators strongly aligned

Prevents: Giving back profits when trend exhausts
```

### Layer 5: Drawdown Limit

```
Maximum Portfolio Drawdown: 10%

Check: (peak_value - current_value) / peak_value ≤ 0.10

Action: If breached, close ALL positions (circuit breaker)
       Also reduces max leverage for future trades
```

### Layer 6: Daily Loss Limit

```
Maximum Daily Loss: 3%

Check: (day_start_value - current_value) / day_start_value ≤ 0.03

Action: If breached, no new trades for rest of day
       Reduces leverage by 60% for remaining positions
```

### Layer 7: Portfolio Exposure Limit

```
Maximum Active Positions: 3/3 baskets (one per instrument)

With Fixed 1.5x Leverage:
  Maximum exposure per basket: ¥450k
  Maximum total exposure: 3 × ¥450k = ¥1.35M
  On ¥1M portfolio: 135% notional, 90% capital at risk

Logic: Fixed leverage limits total risk automatically
       Each basket can only hold one position at a time

Prevents: Over-concentration, excessive simultaneous exposure
```

### Layer 8: Dynamic Cash Reserve

```
Adaptive Cash Reserve:
  - Aggressive: 5% (strong signals, low volatility)
  - Balanced: 15% (normal conditions)
  - Defensive: 25% (high volatility, weak signals)

Check: cash / portfolio_value ≥ target_reserve

Ensures: Liquidity for rebalancing and exits
```

### Layer 9: Chaos Regime Protection

```
Chaos Regime Detection:
  - Count baskets with regime == 4 (chaos/high volatility)

If chaos_baskets >= 2:
  - Exit losing positions (P&L < -1%)
  - No new entries until volatility subsides
  - Tighten stops to 2% across all tiers

If chaos_baskets >= 1:
  - Use conservative WEAK tier stops (3%)
  - Reduce profit targets to 8%

Prevents: Trading in highly volatile, directionless markets
         Whipsaw losses during unstable conditions
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

### Exit Trigger 0: Trailing Stop (High Leverage)

```
Activation: Leverage >= 5x AND profit >= 5%
Trail Distance: 2% below peak

Example:
  ├─ LONG at ¥800 with 8x leverage
  ├─ Price hits ¥840 (+5%) → Trailing stop activates
  ├─ Peak: ¥860 → Trail stop: ¥842.80
  ├─ Price drops to ¥842.80 → EXIT
  └─ Result: Lock in +5.35% profit

Reason: Protect profits on high-leverage winners
        Higher leverage = need to secure gains faster
```

### Exit Trigger 1: Leverage-Adjusted Profit Targets

```
Dynamic Profit Targets (based on leverage):

High Leverage (≥5x):
  ├─ Condition: P&L >= 7%
  ├─ Action: FULL exit (100%)
  └─ Reason: Earlier exit reduces risk on high-leverage positions

Medium-High Leverage (≥3x):
  ├─ Condition: P&L >= 8%
  ├─ Action: FULL exit (100%)
  └─ Reason: Balanced profit taking

Standard Leverage (<3x):
  ├─ Condition: P&L >= 10%
  ├─ Action: FULL exit (100%)
  └─ Reason: Lock in substantial gains

5% Profit Protection (all leverage):
  ├─ Condition: P&L >= 5% AND conviction < 0.40
  ├─ Action: FULL exit (100%)
  └─ Reason: Protect gains when signal weakens
```

### Exit Trigger 2: Leverage-Adjusted Stop Loss

```
Dynamic Stop-Loss (tighter at higher leverage):

High Leverage (>10x):
  ├─ Condition: P&L <= -1.0%
  ├─ Action: IMMEDIATE full exit
  └─ Reason: Very tight control on extreme leverage

Medium-High Leverage (6-10x):
  ├─ Condition: P&L <= -1.5%
  ├─ Action: IMMEDIATE full exit
  └─ Reason: Tight control on high leverage

Medium Leverage (4-6x):
  ├─ Condition: P&L <= -2.0%
  ├─ Action: IMMEDIATE full exit
  └─ Reason: Balanced risk management

Low-Medium Leverage (2-4x):
  ├─ Condition: P&L <= -2.5%
  ├─ Action: IMMEDIATE full exit
  └─ Reason: More room for normal volatility

Low Leverage (<2x):
  ├─ Condition: P&L <= -3.0%
  ├─ Action: IMMEDIATE full exit
  └─ Reason: Standard stop loss
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

0. Update trailing stop (if leverage >= 5x)
   ├─ Update peak price and trail stop level
   └─ Check if trailing stop hit: EXIT [trailing_stop]

1. Calculate P&L
   ├─ For LONG: (current - entry) / entry
   └─ For SHORT: (entry - current) / entry

2. Check leverage-adjusted profit targets
   ├─ Get profit target based on leverage (7-10%)
   ├─ IF P&L >= profit_target: EXIT [profit_target_Npct]
   ├─ IF P&L >= 5% AND conviction < 0.40: EXIT [profit_protect_5pct]
   └─ ELSE: Continue

3. Check leverage-adjusted stop loss
   ├─ Get stop loss based on leverage (1.0-3.0%)
   ├─ IF P&L <= -stop_loss: EXIT [stop_loss_Npct]
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

3. Smart leverage calculation:
   base_leverage = 1.0 + (0.696 × 12.86) = 9.95x
   # No risk adjustments (no chaos, low DD, no daily loss)
   leverage = 9.95x → capped at 10.0x (STRONG tier max)

4. Position value:
   ¥300,000 × 0.864 × 9.95 = ¥2,578,080

5. Risk parameters:
   stop_loss = 1.5% (tighter due to 10x leverage)
   profit_target = 7% (earlier exit due to high leverage)

6. Risk checks:
   - Leverage-weighted exposure: 25.8% < 90% ✓
   - Drawdown: 0% < 10% ✓
   - Daily loss: 0% < 3% ✓

7. EXECUTE
```

**Log Output**:
```
[09:00] LONG basket 0 [STRONG]: DCE/i, size=86%, lev=9.95x,
        stop=1.5%, target=7%, price=765.00,
        conv=0.70 (conf=0.68, str=0.72)
```

**Updated State**:
```
Active Positions: 1
Basket 0: LONG i2501 @ 765.0, notional=¥2,578,080
Portfolio Exposure: 25.8% (leverage-weighted)
Average Leverage: 9.95x
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

3. Smart leverage calculation:
   base_leverage = 1.0 + (0.528 × 10.0) = 6.28x
   # No risk adjustments
   leverage = 6.28x → capped at 6.0x (MEDIUM tier max)

4. Position value:
   ¥300,000 × 0.578 × 6.0 = ¥1,040,400

5. Minimum contract check:
   contract_size = 76,770 × 5 = ¥383,850
   min_position = ¥383,850 × 1 = ¥383,850
   ✓ ¥1,040,400 > ¥383,850 → 2.7 contracts → 2 contracts

6. Risk parameters:
   stop_loss = 2.0% (tighter due to 6x leverage)
   profit_target = 8% (earlier exit due to medium-high leverage)

7. Risk checks:
   - Leverage-weighted exposure: 43.1% < 90% ✓

8. EXECUTE
```

**Log Output**:
```
[09:30] SHORT basket 1 [MEDIUM]: SHFE/cu, size=58%, lev=6.00x,
        stop=2.0%, target=8%, price=76770.00,
        conv=0.53 (conf=0.58, str=0.45)
```

**Updated State**:
```
Active Positions: 2
Basket 0: LONG i2501 @ 765.0, lev=9.95x
Basket 1: SHORT cu2412 @ 76770.0, lev=6.0x
Portfolio Exposure: 43.1% (leverage-weighted)
Average Leverage: 7.98x
```

---

### Bar 15: 12:45 PM - Iron Ore Profit Target

**Price Movement**:
```
Iron ore: 765.0 → 818.5 (+7.0%)
```

**Exit Trigger Check**:
```
P&L = (818.5 - 765.0) / 765.0 = 0.070 (7.0%)
Leverage = 9.95x
Profit Target = 7% (for high leverage ≥5x)

✓ P&L >= 7% → Trigger: Leverage-Adjusted Profit Target
```

**Log Output**:
```
[12:45] PROFIT TARGET: Basket 0 (DCE/i) hit 7% profit (7.0%) at 9.95x leverage
[12:45] CLOSE basket 0 [profit_target_7pct]: DCE/i, LONG
        entry=765.00, exit=818.50, P&L=+7.0%
```

**P&L Calculation**:
```
Notional Entry: ¥2,578,080 (with 9.95x leverage)
Base Capital: ¥259,000 (¥2,578,080 / 9.95)
Realized P&L: ¥259,000 × 0.070 × 9.95 = +¥180,365
(7% price move × 9.95x leverage = 69.7% return on base capital)
```

**Updated State**:
```
Active Positions: 1
Basket 0: FLAT (¥480,365 capital now, +¥180,365 profit)
Basket 1: SHORT cu2412 @ 76770.0, lev=6.0x
Portfolio Value: ¥1,180,365
```

---

### Bar 22: 15:00 PM - Copper Stop Loss

**Price Movement**:
```
Copper: 76770.0 → 78306.0 (+2.0%)
For SHORT: P&L = (76770 - 78306) / 76770 = -2.0%
```

**Exit Trigger Check**:
```
P&L = -2.0%
Leverage = 6.0x
Stop Loss = 2.0% (for 6x leverage)

✓ P&L <= -2.0% → Trigger: Leverage-Adjusted Stop Loss
```

**Log Output**:
```
[15:00] STOP-LOSS: Basket 1 (SHFE/cu) hit 2.0% loss (-2.0%) at 6.0x leverage
[15:00] CLOSE basket 1 [stop_loss_2pct]: SHFE/cu, SHORT
        entry=76770.00, exit=78306.00, P&L=-2.0%
```

**P&L Calculation**:
```
Notional Entry: ¥1,040,400 (with 6.0x leverage)
Base Capital: ¥173,400 (¥1,040,400 / 6.0)
Realized P&L: ¥173,400 × 0.020 × 6.0 = -¥20,808
(2% price move × 6.0x leverage = 12% loss on base capital)
```

**Updated State**:
```
Active Positions: 0
Basket 0: FLAT (¥480,365 capital, +¥180,365 profit)
Basket 1: FLAT (¥279,192 capital, -¥20,808 loss)
Portfolio Value: ¥1,159,557
Net P&L for day: +¥159,557 (+15.96%)
```

---

### Summary of Trading Day

**Trades Executed**:
```
1. Iron Ore LONG (STRONG tier, 86% size, 9.95x leverage)
   → +7.0% price move × 9.95x leverage = +69.7% return
   → Profit: +¥180,365

2. Copper SHORT (MEDIUM tier, 58% size, 6.0x leverage)
   → -2.0% price move × 6.0x leverage = -12.0% loss
   → Loss: -¥20,808

Net Result: +¥159,557 (+15.96% portfolio return)
```

**Key Observations**:
- Smart leverage amplified profits: 7% move → 69.7% return (9.95x)
- Different leverage based on conviction (STRONG=10x, MEDIUM=6x)
- Leverage-adjusted exits: 7% target (vs 10%), 2% stop (vs 3%)
- Tighter risk controls protected capital on losing trade
- Diversified (LONG + SHORT)
- Net positive despite 1 winner, 1 loser
- System working as designed with smart leverage ✓

**Comparison to Old System (1.4x fixed leverage)**:
- Old Iron Ore profit: +¥36,668 (10.1% move × 1.4x)
- New Iron Ore profit: +¥180,365 (7% move × 9.95x)
- **5x more profit with earlier exit and tighter stops**

---

## Key Principles Summary

### 1. **Separation of Concerns**
- Tier-1: Signal generation (technical analysis)
- Tier-2: Portfolio management (risk & execution)

### 2. **Graduated Position Sizing with Smart Leverage**
- Not binary (all-or-nothing)
- Size scales with signal quality
- 3 tiers: STRONG (80-100%), MEDIUM (40-60%), WEAK (20-30%)
- Smart leverage scales with conviction:
  - STRONG: 4-10x (high confidence = high leverage)
  - MEDIUM: 2.5-6x (moderate confidence)
  - WEAK: 1.5-4x (low confidence)
- Auto-adjusts for risk conditions (chaos, drawdown, daily loss)

### 3. **Multi-Layer Risk Management**
- 9 independent risk controls
- Portfolio-level AND position-level
- Leverage-adjusted stops and targets
- Trailing stops for high-leverage positions
- Leverage-weighted exposure tracking
- Circuit breakers for extreme scenarios

### 4. **Adaptive Behavior**
- Reduce sizes in high volatility
- Reduce leverage in bad conditions (chaos, drawdown, daily loss)
- Dynamic cash reserves
- Fallback chains prevent unnecessary blocks
- Auto-increase leverage to meet minimum contracts

### 5. **Smart Exits with Leverage Awareness**
- Multiple exit triggers (6 types)
- Leverage-adjusted profit targets (7-10%, earlier for high leverage)
- Leverage-adjusted stop losses (1-3%, tighter for high leverage)
- Trailing stops for high-leverage winners (5x+ leverage)
- React to signal changes and confidence degradation

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

# Smart Leverage Ranges
LEVERAGE_TIERS = {
    'STRONG': {'min': 4.0, 'max': 10.0, 'multiplier': 12.86},
    'MEDIUM': {'min': 2.5, 'max': 6.0, 'multiplier': 10.0},
    'WEAK': {'min': 1.5, 'max': 4.0, 'multiplier': 10.0},
}

# Hard Caps
MAX_LEVERAGE = 20.0          # Absolute maximum
MAX_BASKET_LEVERAGE = 15.0   # Per-basket maximum

# Leverage-Adjusted Stop Loss
STOP_LOSS_TIERS = [
    (2.0, 0.030),   # Up to 2x: 3.0% stop
    (4.0, 0.025),   # Up to 4x: 2.5% stop
    (6.0, 0.020),   # Up to 6x: 2.0% stop
    (10.0, 0.015),  # Up to 10x: 1.5% stop
    (20.0, 0.010),  # Above 10x: 1.0% stop
]

# Leverage-Adjusted Profit Targets
PROFIT_TARGETS = [
    (5.0, 0.07),    # 5x+: 7% target
    (3.0, 0.08),    # 3x+: 8% target
    (0.0, 0.10),    # Default: 10% target
]

# Trailing Stop
TRAILING_STOP_ACTIVATION_LEV = 5.0   # Activate at 5x+ leverage
TRAILING_STOP_ACTIVATION_PROFIT = 0.05  # Activate at 5% profit
TRAILING_STOP_DISTANCE = 0.02        # Trail 2% below peak

# Weights
CONFIDENCE_WEIGHT = 0.6
STRENGTH_WEIGHT = 0.4
```

### Risk Limits

```python
# Portfolio limits
MAX_TOTAL_EXPOSURE = 0.90           # 90% (leverage-weighted)
MIN_CASH_RESERVE = 0.10             # 10%
MAX_PORTFOLIO_DD = 0.10             # 10%
MAX_DAILY_LOSS = 0.03               # 3%

# Position limits (leverage-adjusted)
STOP_LOSS_RANGE = (0.010, 0.030)   # 1.0-3.0% (based on leverage)
PROFIT_TARGET_RANGE = (0.07, 0.10) # 7-10% (based on leverage)
PROFIT_PROTECT = 0.05               # 5% (with low conviction)

# Contract Multipliers (for minimum contract sizing)
CONTRACT_MULTIPLIERS = {
    'DCE/i': 100,    # Iron Ore: 100 tons
    'SHFE/cu': 5,    # Copper: 5 tons
    'DCE/m': 10,     # Soybean: 10 tons
}
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
