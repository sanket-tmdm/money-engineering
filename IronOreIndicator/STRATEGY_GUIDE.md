# Iron Ore Trading Strategy - Complete Guide

**Strategy Name**: IronOreIndicatorRelaxed (with Position Accumulation)
**Type**: Long-Only Multi-Indicator Confirmation System with Pyramiding
**Market**: DCE (Dalian Commodity Exchange)
**Security**: Iron Ore Futures (i<00> - Logical Contract)
**Timeframe**: 15 minutes (900 seconds)
**Initial Capital**: ¥1,000,000 CNY
**Max Allocation**: 70% (¥700,000 max in positions)
**Reserve**: 30% (¥300,000 minimum cash)

---

## Table of Contents

1. [Strategy Overview](#strategy-overview)
2. [Technical Indicators](#technical-indicators)
3. [Market Regime Detection](#market-regime-detection)
4. [Entry Conditions](#entry-conditions)
5. [Exit Conditions](#exit-conditions)
6. [Position Sizing & Portfolio Management](#position-sizing--portfolio-management)
7. [Risk Management](#risk-management)
8. [Complete Trading Rules](#complete-trading-rules)
9. [Reproduction Steps](#reproduction-steps)

---

## Strategy Overview

### Philosophy

This is a **LONG-ONLY** trend-following and mean-reversion hybrid strategy with **POSITION ACCUMULATION** (pyramiding). The strategy adapts to different market conditions, buying dips incrementally up to a 70% portfolio allocation limit, and selling all positions when exit conditions trigger. It uses a **scoring system** instead of requiring all conditions to be met simultaneously, making it more flexible and generating more trading opportunities.

### Key Features

- ✅ **Long-only positions** (no short selling)
- ✅ **Position accumulation** (add 50 contracts on each buy signal)
- ✅ **70% maximum allocation** (keep 30% cash reserve)
- ✅ **Buy the dip strategy** (accumulate during pullbacks)
- ✅ **Sell all on exits** (take profit or cut loss completely)
- ✅ **Multi-regime adaptation** (4 market regimes)
- ✅ **Scoring-based entries** (relaxed conditions)
- ✅ **Stricter exits than entries** (let winners run)
- ✅ **3-bar cooldown period** (only after full exit to flat)
- ✅ **Average entry price tracking** (for P&L calculation)
- ✅ **Capital preservation mode** (exits during high volatility chaos)

### Strategy Type by Regime

| Regime | Type | Description |
|--------|------|-------------|
| **1 - Strong Uptrend** | Trend Following | Buy pullbacks in uptrend, ride momentum |
| **2 - Strong Downtrend** | Exit Only | Close longs, no new entries |
| **3 - Sideways/Ranging** | Mean Reversion | Buy oversold, sell overbought |
| **4 - High Volatility Chaos** | Capital Preservation | Exit all positions immediately |

---

## Technical Indicators

The strategy combines **7 technical indicators** to detect market conditions and generate signals:

### 1. Triple EMA (Exponential Moving Average)

**Purpose**: Trend identification and directional bias

**Periods**:
- **EMA 12**: Short-term trend (alpha = 2/13 = 0.1538)
- **EMA 26**: Medium-term trend (alpha = 2/27 = 0.0741)
- **EMA 50**: Long-term trend (alpha = 2/51 = 0.0392)

**Calculation** (Online Algorithm):
```
EMA(t) = alpha × Price(t) + (1 - alpha) × EMA(t-1)
```

**Interpretation**:
- **Uptrend**: EMA12 > EMA26 > EMA50 (all aligned bullish)
- **Downtrend**: EMA12 < EMA26 < EMA50 (all aligned bearish)
- **Neutral**: Mixed alignment

---

### 2. MACD (Moving Average Convergence Divergence)

**Purpose**: Momentum confirmation

**Components**:
- **MACD Line** = EMA12 - EMA26
- **Signal Line** = 9-period EMA of MACD (alpha = 2/10 = 0.2000)
- **Histogram** = MACD Line - Signal Line

**Calculation**:
```
MACD = EMA12 - EMA26
Signal = EMA9(MACD)
Histogram = MACD - Signal
```

**Interpretation**:
- **Bullish Momentum**: MACD > Signal (histogram > 0)
- **Bearish Momentum**: MACD < Signal (histogram < 0)
- **Crossovers**: Signal line crosses indicate momentum shifts

---

### 3. RSI (Relative Strength Index)

**Purpose**: Mean reversion signals (overbought/oversold detection)

**Period**: 14-bar EMA (alpha = 2/15 = 0.1333)

**Calculation** (Online Algorithm):
```
Change = Close - PreviousClose
Gain = max(Change, 0)
Loss = max(-Change, 0)

GainEMA = alpha × Gain + (1 - alpha) × GainEMA(previous)
LossEMA = alpha × Loss + (1 - alpha) × LossEMA(previous)

RS = GainEMA / LossEMA
RSI = 100 - (100 / (1 + RS))
```

**Thresholds** (RELAXED):
- **Oversold**: RSI < 40 (relaxed from traditional 30)
- **Overbought**: RSI > 60 (relaxed from traditional 70)
- **Neutral**: 40 ≤ RSI ≤ 60

**Why Relaxed?**
- Traditional 30/70 levels are too extreme
- 40/60 generates more trading opportunities
- Still captures significant mean reversion moves

---

### 4. Bollinger Bands

**Purpose**: Price extreme detection and volatility measurement

**Parameters**:
- **Period**: 20 bars (Welford's online variance algorithm)
- **Standard Deviation**: 2σ

**Calculation**:
```
Middle Band = 20-period SMA (using Welford's algorithm)
Upper Band = Middle + (2 × StdDev)
Lower Band = Middle - (2 × StdDev)
BB Width = Upper - Lower
BB Width % = (BB Width / Middle) × 100
```

**Interpretation**:
- **Price at Lower Band**: Potential oversold (buy opportunity)
- **Price at Upper Band**: Potential overbought (sell opportunity)
- **Band Expansion**: Increased volatility
- **Band Contraction**: Low volatility (ranging market)

---

### 5. ATR (Average True Range)

**Purpose**: Volatility measurement and regime detection

**Period**: 14-bar EMA (alpha = 2/15 = 0.1333)

**Calculation**:
```
True Range = max(
    High - Low,
    |High - PreviousClose|,
    |Low - PreviousClose|
)

ATR = EMA14(True Range)
Mean ATR = Online average of ATR (100-bar cap)
```

**Interpretation**:
- **Normal Volatility**: ATR ≤ 1.2 × Mean ATR
- **Elevated Volatility**: 1.2 × Mean ATR < ATR ≤ 1.5 × Mean ATR
- **Extreme Volatility**: ATR > 1.5 × Mean ATR (chaos regime)

---

### 6. BB Width Percentage

**Purpose**: Volatility confirmation (secondary volatility metric)

**Calculation**:
```
BB Width % = ((Upper Band - Lower Band) / Middle Band) × 100
```

**Interpretation**:
- **BB Width % > 5.0%**: High volatility (chaos regime indicator)
- **BB Width % < 3.0%**: Low volatility (ranging market)

---

### 7. Volume EMA

**Purpose**: Liquidity confirmation

**Period**: 20-bar EMA (alpha = 2/21 = 0.0952)

**Calculation**:
```
VolumeEMA = alpha × CurrentVolume + (1 - alpha) × VolumeEMA(previous)
```

**Thresholds**:
- **Uptrend/Downtrend**: Volume > 1.2 × VolumeEMA
- **Ranging**: Volume > 1.1 × VolumeEMA

**Why Volume Matters?**
- Confirms genuine price movements
- Filters false signals during low-liquidity periods
- Higher volume = more reliable signals

---

## Market Regime Detection

The strategy automatically detects which of **4 market regimes** is currently active:

### Regime 1: Strong Uptrend

**Detection Criteria**:
```
✓ EMA12 > EMA26 > EMA50 (all aligned bullish)
✓ MACD > Signal AND Histogram > 0 (bullish momentum)
✓ Close > EMA26 (price above medium-term trend)
✓ ATR ≤ 1.2 × Mean ATR (normal volatility)
```

**Trading Style**: Trend following - buy pullbacks, ride momentum

---

### Regime 2: Strong Downtrend

**Detection Criteria**:
```
✓ EMA12 < EMA26 < EMA50 (all aligned bearish)
✓ MACD < Signal AND Histogram < 0 (bearish momentum)
✓ Close < EMA26 (price below medium-term trend)
✓ ATR ≤ 1.2 × Mean ATR (normal volatility)
```

**Trading Style**: EXIT ONLY - close longs, no new entries

---

### Regime 3: Sideways/Ranging

**Detection Criteria**:
```
✓ EMAs not aligned (mixed signals)
✓ No clear trend direction
✓ ATR ≤ 1.2 × Mean ATR (normal volatility)
```

**Trading Style**: Mean reversion - buy oversold, sell overbought

---

### Regime 4: High Volatility Chaos

**Detection Criteria** (Priority #1 - checked first):
```
✓ ATR > 1.5 × Mean ATR (extreme volatility)
   OR
✓ BB Width % > 5.0% (band expansion)
```

**Trading Style**: Capital preservation - EXIT ALL positions immediately

---

## Entry Conditions

### Uptrend Entry (Regime 1)

**Strategy**: Buy pullbacks during uptrend

**Scoring System**: Need **3 out of 5 points** to enter

| # | Condition | Points |
|---|-----------|--------|
| 1 | EMA12 > EMA26 (partial trend alignment) | +1 |
| 2 | MACD > Signal (bullish momentum) | +1 |
| 3 | RSI < 40 (pullback/oversold) | +1 |
| 4 | Volume > 1.2 × VolumeEMA (liquidity) | +1 |
| 5 | Price near lower BB (within 20% of band width) | +1 |

**Entry Signal**: BUY when score ≥ 3

**Confidence Calculation**:
```
Confidence = (40 - RSI) / 40
```
- RSI = 20 → Confidence = 0.50
- RSI = 30 → Confidence = 0.25
- RSI = 40 → Confidence = 0.00

**Additional Requirement**: Must not be in 3-bar cooldown period

---

### Ranging Entry (Regime 3)

**Strategy**: Mean reversion at oversold levels

**Scoring System**: Need **2 out of 4 points** to enter

| # | Condition | Points |
|---|-----------|--------|
| 1 | Price near lower BB (within 30% of band width) | +1 |
| 2 | RSI < 40 (oversold) | +1 |
| 3 | Volume > 1.1 × VolumeEMA (liquidity) | +1 |
| 4 | Close > Low (showing bounce potential) | +1 |

**Entry Signal**: BUY when score ≥ 2

**Confidence Calculation**:
```
BBRange = Upper - Lower
Distance = Middle - Close
Confidence = min(|Distance| / BBRange, 1.0)
```

**Additional Requirement**: Must not be in 3-bar cooldown period

---

### Downtrend Entry (Regime 2)

**NO ENTRIES IN DOWNTREND** ❌

This is a long-only strategy. In downtrends, we only exit existing positions.

---

### Chaos Entry (Regime 4)

**NO ENTRIES IN CHAOS** ❌

During extreme volatility, we preserve capital by staying flat or exiting.

---

## Exit Conditions

### Uptrend Exit (Regime 1)

**Strategy**: Exit on weakness signals

**Scoring System**: Need **2 out of 3 points** to exit

| # | Condition | Points |
|---|-----------|--------|
| 1 | RSI > 65 (overbought - stricter than entry) | +1 |
| 2 | MACD < Signal AND Histogram < 0 (momentum shift) | +1 |
| 3 | Close < EMA26 (price below key support) | +1 |

**Exit Signal**: SELL when score ≥ 2

**Why Stricter?**
- Entry uses RSI < 40, exit uses RSI > 65
- Prevents premature exits during normal pullbacks
- Allows trades to run and capture more profit

---

### Ranging Exit (Regime 3)

**Strategy**: Exit at overbought levels (mean reversion complete)

**Scoring System**: Need **3 out of 4 points** to exit

| # | Condition | Points |
|---|-----------|--------|
| 1 | Price near upper BB (within 20% of band width) | +1 |
| 2 | RSI > 65 (overbought - stricter threshold) | +1 |
| 3 | Volume > 1.1 × VolumeEMA (selling pressure) | +1 |
| 4 | Price shows resistance (Close < High by >0.2%) | +1 |

**Exit Signal**: SELL when score ≥ 3

**Confidence Calculation**:
```
BBRange = Upper - Lower
Distance = Close - Middle
Confidence = min(|Distance| / BBRange, 1.0)
```

---

### Downtrend Exit (Regime 2)

**Strategy**: Exit longs immediately in downtrend

**Scoring System**: Need **1 out of 3 points** to exit

| # | Condition | Points |
|---|-----------|--------|
| 1 | EMA12 < EMA26 (bearish trend) | +1 |
| 2 | MACD < Signal (bearish momentum) | +1 |
| 3 | Close < BB Middle (price weakness) | +1 |

**Exit Signal**: SELL when score ≥ 1

**Why So Aggressive?**
- Long-only strategy is vulnerable in downtrends
- Better to exit early and preserve capital
- Can re-enter when conditions improve

---

### Chaos Exit (Regime 4)

**Strategy**: Emergency exit all positions

**Exit Signal**: SELL immediately if in position

**Confidence**: 1.0 (maximum urgency)

**Purpose**: Protect capital during extreme volatility when normal risk management breaks down

---

## Position Sizing & Portfolio Management

### Capital Structure

```
Initial Capital: ¥1,000,000 CNY
Maximum Allocation: 70% (¥700,000 max in positions)
Reserve Allocation: 30% (¥300,000 minimum cash)
Position Size Per Signal: 50 contracts
```

### Position Accumulation Strategy

This strategy uses **POSITION ACCUMULATION** (pyramiding):

```python
contracts_per_trade = 50  # Add 50 contracts per buy signal
max_allocation = 0.70     # Max 70% of portfolio in positions
reserve_allocation = 0.30  # Keep 30% cash reserve
```

**How It Works**:
- Each BUY signal adds 50 contracts to position
- Can accumulate multiple positions up to 70% limit
- SELL signal closes ALL positions (no partial exits)

### Position Accumulation Example

**Starting State**:
```
Portfolio Value: ¥1,000,000
Cash: ¥1,000,000
Position: 0 contracts
Current Price: ¥780
```

**First Buy Signal (Bar 100)**:
```
Action: BUY 50 contracts @ ¥780
Cost: 50 × 780 = ¥39,000
Cash After: ¥1,000,000 - ¥39,000 = ¥961,000
Position: 50 contracts
Position Value: 50 × 780 = ¥39,000
Allocation: ¥39,000 / ¥1,000,000 = 3.9%
Average Entry: ¥780
```

**Second Buy Signal (Bar 105 - Price Dips to ¥770)**:
```
Action: BUY 50 more contracts @ ¥770
Cost: 50 × 770 = ¥38,500
Cash After: ¥961,000 - ¥38,500 = ¥922,500
Position: 100 contracts (50 + 50)
Position Value: 100 × 770 = ¥77,000
Allocation: ¥77,000 / ¥999,500 = 7.7%
Average Entry: (50×780 + 50×770) / 100 = ¥775
```

**Third Buy Signal (Bar 110 - Price at ¥765)**:
```
Action: BUY 50 more contracts @ ¥765
Cost: 50 × 765 = ¥38,250
Cash After: ¥922,500 - ¥38,250 = ¥884,250
Position: 150 contracts (100 + 50)
Position Value: 150 × 765 = ¥114,750
Allocation: ¥114,750 / ¥999,000 = 11.5%
Average Entry: (50×780 + 50×770 + 50×765) / 150 = ¥771.67
```

**Continue Accumulating Until 70% Limit**:
```
Max Position Value = ¥1,000,000 × 0.70 = ¥700,000
At Price ¥780:
  Max Contracts = ¥700,000 / ¥780 ≈ 897 contracts
  Number of 50-contract buys = 897 / 50 ≈ 17-18 signals
```

**Exit Signal (Bar 150 - Price Rises to ¥800)**:
```
Action: SELL ALL 150 contracts @ ¥800
Revenue: 150 × 800 = ¥120,000
Cash After: ¥884,250 + ¥120,000 = ¥1,004,250
Position: 0 contracts
Realized P&L: ¥800 - ¥771.67 = ¥28.33 per contract
Total Profit: ¥28.33 × 150 = ¥4,250 ✅
Portfolio Value: ¥1,004,250 (0.425% gain)
```

### 70% Allocation Limit Logic

**Before Each Buy**:
```python
# Calculate current state
position_value = contracts_held × current_price
portfolio_value = cash + position_value

# Calculate proposed state (if we buy 50 more)
proposed_position_value = (contracts_held + 50) × current_price
proposed_allocation = proposed_position_value / portfolio_value

# Check if can add
can_add = (proposed_allocation <= 0.70) AND (cash >= 50 × price)

if can_add and buy_signal:
    BUY 50 contracts
else:
    HOLD (allocation limit reached or insufficient cash)
```

### Average Entry Price Tracking

**Formula**:
```
New_Avg_Entry = (Total_Cost_Before + New_Cost) / Total_Contracts_After

Where:
  Total_Cost_Before = contracts_held × avg_entry_price
  New_Cost = 50 × current_price
  Total_Contracts_After = contracts_held + 50
```

**Example**:
```
Before: 100 contracts @ ¥775 avg = ¥77,500 total cost
Buy: 50 contracts @ ¥765 = ¥38,250 new cost
After: 150 contracts @ ¥771.67 avg = ¥115,750 total cost
```

### Portfolio Value Calculation

```
Always:
  Position Value = contracts_held × current_price
  Portfolio Value = cash + position_value
  Allocation % = position_value / portfolio_value × 100
  Unrealized P&L = (current_price - avg_entry) × contracts_held
```

### Position States

Unlike the previous binary strategy, position state is now continuous:

```
contracts_held = 0:    FLAT (no position)
contracts_held = 50:   SMALL position (1 signal)
contracts_held = 100:  MEDIUM position (2 signals)
contracts_held = 150:  LARGE position (3 signals)
...
contracts_held ≤ 70% limit: Can still add
contracts_held > 70% limit: Cannot add more
```

### Why 70/30 Split?

**70% Maximum Allocation**:
- ✅ Allows meaningful exposure to capture trends
- ✅ Permits position accumulation (average down on dips)
- ✅ Provides upside leverage when right

**30% Cash Reserve**:
- ✅ Ensures liquidity for more buys on deeper dips
- ✅ Safety buffer for drawdowns
- ✅ Reduces forced liquidation risk
- ✅ Allows flexibility to add positions

### Risk Characteristics

**Advantages of Accumulation**:
- ✅ Average down on dips (lower cost basis)
- ✅ Larger position when right = bigger profits
- ✅ Flexible entry (don't need to time perfectly)
- ✅ Captures full trend moves

**Risks of Accumulation**:
- ⚠️ Can accumulate into losing trades (catching falling knife)
- ⚠️ Larger drawdowns if market reverses after accumulation
- ⚠️ Higher capital commitment per trade
- ⚠️ No partial exits (all-or-nothing profit taking)

---

## Risk Management

### 1. Cooldown Period

**Purpose**: Prevent rapid re-entry after full exit

**Rule**: After FULL EXIT (all positions sold), wait **3 bars** before first new buy

```
cooldown_bars = 3
last_exit_bar = bar_index (when position closed to FLAT)

Cannot enter if: (current_bar - last_exit_bar) < 3 AND position = 0
```

**Important**: Cooldown ONLY applies after FULL exit to flat (0 contracts). When accumulating positions, there is NO cooldown between buys.

**Example 1 - Cooldown After Full Exit**:
- Bar 100: Sell ALL (150 → 0 contracts) - **Trigger cooldown**
- Bar 101: Cooldown (cannot buy) - Position still 0
- Bar 102: Cooldown (cannot buy) - Position still 0
- Bar 103: Cooldown (cannot buy) - Position still 0
- Bar 104: Eligible to enter again (cooldown expired)

**Example 2 - NO Cooldown When Accumulating**:
- Bar 100: BUY (0 → 50 contracts)
- Bar 101: BUY again (50 → 100 contracts) - **NO cooldown**
- Bar 102: BUY again (100 → 150 contracts) - **NO cooldown**
- Bar 105: SELL ALL (150 → 0 contracts) - **Trigger cooldown**

---

### 2. Regime-Based Risk Control

**Chaos Regime (Regime 4)**: Forced exit when volatility is extreme

```
If ATR > 1.5 × Mean ATR OR BB Width % > 5.0%:
    Force exit all positions
    Do not enter new trades
```

**Downtrend Regime (Regime 2)**: Exit-only mode

```
If strong downtrend detected:
    Exit long positions with 1/3 confirmations
    Do not enter new longs
    Wait for better regime
```

---

### 3. Scoring System (Partial Confirmations)

**Entry Requirements**:
- Uptrend: 3/5 conditions (60%)
- Ranging: 2/4 conditions (50%)

**Exit Requirements** (Stricter):
- Uptrend: 2/3 conditions (67%)
- Ranging: 3/4 conditions (75%)

**Why Stricter Exits?**
- Allows trades to breathe
- Captures more trend movement
- Reduces whipsaw losses

---

### 4. 70% Allocation Limit (Portfolio Risk Cap)

**Purpose**: Prevent over-leverage and maintain liquidity

**Rule**: Cannot add more positions if it would exceed 70% allocation

```python
proposed_position_value = (contracts_held + 50) × price
proposed_allocation = proposed_position_value / portfolio_value

if proposed_allocation > 0.70:
    CANNOT BUY (allocation limit reached)
else:
    CAN BUY (still room)
```

**Benefits**:
- ✅ Prevents over-concentration in single position
- ✅ Maintains 30% cash buffer for deeper dips
- ✅ Reduces risk of forced liquidation
- ✅ Allows portfolio to grow sustainably

### 5. Position Synchronization

**Safety Check**: Before generating signals, sync position state with portfolio

```python
if contracts_held > 0:
    position_state = 1  # IN POSITION (can add more or exit)
else:
    position_state = 0  # FLAT (can start new position after cooldown)
```

This prevents desync bugs where the indicator thinks it's in a position when it's not.

---

## Complete Trading Rules

### Rule 1: Regime Detection (Priority #1)

```
STEP 1: Check for Chaos Regime
  IF ATR > 1.5 × Mean ATR OR BB Width % > 5.0%:
    regime = 4 (Chaos)
    IF in position: EXIT immediately
    RETURN (no further checks)

STEP 2: Check for Strong Uptrend
  IF EMA12 > EMA26 > EMA50
     AND MACD > Signal AND Histogram > 0
     AND Close > EMA26
     AND ATR ≤ 1.2 × Mean ATR:
    regime = 1 (Uptrend)
    RETURN

STEP 3: Check for Strong Downtrend
  IF EMA12 < EMA26 < EMA50
     AND MACD < Signal AND Histogram < 0
     AND Close < EMA26
     AND ATR ≤ 1.2 × Mean ATR:
    regime = 2 (Downtrend)
    RETURN

STEP 4: Default to Ranging
  regime = 3 (Sideways)
```

---

### Rule 2: Signal Generation Priority

**Signal generation follows strict priority order**:

```
PRIORITY 1: Check Chaos Regime
  IF regime = 4 AND position > 0:
    SELL ALL immediately (capital preservation)
    RETURN

PRIORITY 2: Check Exit Conditions (if in position)
  IF position > 0:
    Check exit conditions based on current regime
    IF exit triggered:
      SELL ALL (take profit or cut loss)
      Set last_exit_bar
      RETURN

PRIORITY 3: Check Buy Conditions (add to position or start new)
  IF not in cooldown AND under 70% limit:
    Check entry conditions based on current regime
    IF entry triggered:
      BUY 50 contracts (add to position)
      RETURN

DEFAULT: HOLD (no action)
```

---

### Rule 3: Entry Logic (Position Accumulation)

**Before checking conditions**:
```python
# Check 70% allocation limit
proposed_position_value = (contracts_held + 50) × price
proposed_allocation = proposed_position_value / portfolio_value
can_add = proposed_allocation <= 0.70 AND cash >= 50 × price

# Check cooldown (only if flat)
in_cooldown = (bar_index - last_exit_bar < 3) AND (contracts_held == 0)

IF not can_add OR in_cooldown:
  CANNOT BUY (skip entry logic)
```

**Entry Scoring** (if can_add AND not in_cooldown):
```
IF regime = 1 (Uptrend) - BUY DIPS:
  Score = 0
  IF EMA12 > EMA26: Score += 1
  IF MACD > Signal: Score += 1
  IF RSI < 40: Score += 1
  IF Volume > 1.2 × VolumeEMA: Score += 1
  IF Close ≤ BB_Lower + 0.2 × BBRange: Score += 1

  IF Score ≥ 3:
    BUY 50 contracts (ADD to existing position)
    Confidence = (40 - RSI) / 40
    Update average entry price

IF regime = 3 (Ranging) - BUY DIPS:
  Score = 0
  IF Close ≤ BB_Lower + 0.3 × BBRange: Score += 1
  IF RSI < 40: Score += 1
  IF Volume > 1.1 × VolumeEMA: Score += 1
  IF Close > Low: Score += 1

  IF Score ≥ 2:
    BUY 50 contracts (ADD to existing position)
    Confidence = |Middle - Close| / BBRange
    Update average entry price

IF regime = 2 (Downtrend):
  NO ENTRIES (wait for better conditions)

IF regime = 4 (Chaos):
  NO ENTRIES (capital preservation mode)
```

---

### Rule 4: Exit Logic (Close ALL Positions)

**Exit only checks if `contracts_held > 0`**:

```
IF regime = 1 (Uptrend) AND in position:
  Score = 0
  IF RSI > 65: Score += 1
  IF MACD < Signal AND Histogram < 0: Score += 1
  IF Close < EMA26: Score += 1

  IF Score ≥ 2:
    SELL ALL contracts (take profit)
    Set last_exit_bar = current_bar
    contracts_held = 0

IF regime = 2 (Downtrend) AND in position:
  Score = 0
  IF EMA12 < EMA26: Score += 1
  IF MACD < Signal: Score += 1
  IF Close < BB_Middle: Score += 1

  IF Score ≥ 1:
    SELL ALL contracts (aggressive exit, cut loss)
    Set last_exit_bar = current_bar
    contracts_held = 0

IF regime = 3 (Ranging) AND in position:
  Score = 0
  IF Close ≥ BB_Upper - 0.2 × BBRange: Score += 1
  IF RSI > 65: Score += 1
  IF Volume > 1.1 × VolumeEMA: Score += 1
  IF Close < High AND (High - Close) > 0.002 × Close: Score += 1

  IF Score ≥ 3:
    SELL ALL contracts (take profit at overbought)
    Set last_exit_bar = current_bar
    contracts_held = 0

IF regime = 4 (Chaos) AND in position:
  SELL ALL contracts immediately (emergency exit)
  Confidence = 1.0
  Set last_exit_bar = current_bar
  contracts_held = 0
```

**Note**: Exits always close the ENTIRE position (no partial exits). This simplifies P&L and ensures clean entries/exits.

---

## Reproduction Steps

### Step 1: Set Up Technical Indicators

Implement all 7 indicators using **online algorithms** (EMA-based, no rolling windows):

1. **Triple EMA**: Use alpha values 0.1538, 0.0741, 0.0392
2. **MACD**: Calculate from EMA12 and EMA26, signal line with alpha 0.2000
3. **RSI**: Use gain/loss EMAs with alpha 0.1333
4. **Bollinger Bands**: Welford's online variance, 20-period, 2σ
5. **ATR**: Use true range with alpha 0.1333
6. **BB Width %**: Calculate from BB upper and lower
7. **Volume EMA**: Use alpha 0.0952

---

### Step 2: Initialize State Variables

```python
# State persistence (must survive restarts)
bar_index = 0
initialized = False
position_state = 0
contracts_held = 0
last_exit_bar = -999
cash = 1000000.0
portfolio_value = 1000000.0

# Indicator state (EMAs maintain their values)
ema_12 = 0.0
ema_26 = 0.0
ema_50 = 0.0
macd = 0.0
macd_signal = 0.0
rsi = 50.0
gain_ema = 0.0
loss_ema = 0.0
atr = 0.0
volume_ema = 0.0
bb_mean = 0.0
bb_m2 = 0.0
# ... etc
```

---

### Step 3: Process Each Bar

```python
FOR each 15-minute bar:
  # 1. Extract OHLCV data
  open, high, low, close, volume = get_bar_data()

  # 2. First bar: Initialize all indicators
  IF not initialized:
    initialize_all_indicators(close, volume)
    initialized = True
    CONTINUE to next bar

  # 3. Update all indicators
  update_emas(close)
  update_macd()
  update_rsi(close)
  update_bollinger_bands(close)
  update_atr(high, low, close)
  update_volume_ema(volume)

  # 4. Detect market regime
  regime = detect_regime()

  # 5. Calculate current allocation and check limits
  position_value = contracts_held * close
  portfolio_value = cash + position_value
  current_allocation = position_value / portfolio_value

  proposed_position_value = (contracts_held + 50) * close
  proposed_allocation = proposed_position_value / portfolio_value
  can_add = proposed_allocation <= 0.70 AND cash >= 50 * close

  # 6. Generate trading signal
  signal, confidence = generate_signal(regime, contracts_held, can_add)

  # 7. Execute trade if signal generated
  IF signal == 1 (BUY):
    # ADD 50 contracts to position
    total_cost_before = contracts_held * entry_price
    new_cost = 50 * close
    contracts_held += 50
    entry_price = (total_cost_before + new_cost) / contracts_held
    cash -= new_cost

  ELIF signal == -1 (SELL):
    # CLOSE ALL positions
    cash += contracts_held * close
    contracts_held = 0
    entry_price = 0
    last_exit_bar = bar_index

  # 8. Update portfolio value
  position_value = contracts_held * close
  portfolio_value = cash + position_value
  allocation_pct = (position_value / portfolio_value) * 100

  # 9. Increment bar counter
  bar_index += 1
```

---

### Step 4: Implement Regime Detection

```python
FUNCTION detect_regime():
  # Priority 1: Chaos
  IF atr > mean_atr * 1.5 OR bb_width_pct > 5.0:
    RETURN 4

  # Priority 2: Uptrend
  IF ema_12 > ema_26 > ema_50
     AND macd > macd_signal AND macd_histogram > 0
     AND close > ema_26
     AND atr <= mean_atr * 1.2:
    RETURN 1

  # Priority 3: Downtrend
  IF ema_12 < ema_26 < ema_50
     AND macd < macd_signal AND macd_histogram < 0
     AND close < ema_26
     AND atr <= mean_atr * 1.2:
    RETURN 2

  # Default: Ranging
  RETURN 3
```

---

### Step 5: Implement Signal Generation

```python
FUNCTION generate_signal(regime, position_state):
  # Check cooldown
  bars_since_exit = bar_index - last_exit_bar
  in_cooldown = bars_since_exit < 3

  # Chaos: Exit if in position
  IF regime == 4:
    IF position_state == 1:
      RETURN (-1, 1.0)  # SELL with max confidence
    ELSE:
      RETURN (0, 0.0)  # HOLD

  # Uptrend: Buy pullbacks, exit on weakness
  IF regime == 1:
    IF position_state == 0 AND not in_cooldown:
      IF check_uptrend_buy():  # Score >= 3/5
        confidence = (40 - rsi) / 40
        RETURN (1, confidence)  # BUY

    ELIF position_state == 1:
      IF check_uptrend_exit():  # Score >= 2/3
        RETURN (-1, 0.8)  # SELL

  # Downtrend: Exit only
  IF regime == 2:
    IF position_state == 1:
      IF check_downtrend_exit():  # Score >= 1/3
        RETURN (-1, 0.8)  # SELL

  # Ranging: Mean reversion
  IF regime == 3:
    IF position_state == 0 AND not in_cooldown:
      IF check_ranging_buy():  # Score >= 2/4
        bb_range = bb_upper - bb_lower
        confidence = |bb_middle - close| / bb_range
        RETURN (1, confidence)  # BUY

    ELIF position_state == 1:
      IF check_ranging_sell():  # Score >= 3/4
        bb_range = bb_upper - bb_lower
        confidence = |close - bb_middle| / bb_range
        RETURN (-1, confidence)  # SELL

  # Default: No signal
  RETURN (0, 0.0)  # HOLD
```

---

### Step 6: Backtest & Validation

**Required Tests**:

1. **Quick Test** (7 days):
   ```bash
   Start: 2024-10-25
   End: 2024-11-01
   Purpose: Verify signals generate correctly
   ```

2. **Replay Consistency Test**:
   ```bash
   Run: test_resuming_mode.py
   Purpose: Ensure deterministic behavior (no random values)
   ```

3. **Full Backtest** (3+ months):
   ```bash
   Start: 2025-01-01
   End: 2025-04-01
   Purpose: Evaluate performance and P&L
   ```

---

### Step 7: Performance Analysis

Use `trading_simulation.ipynb` to analyze:

- **Portfolio value curve**
- **Cumulative P&L**
- **Win rate and trade distribution**
- **Drawdown periods**
- **Regime distribution** (time spent in each regime)
- **Signal quality** (RSI/MACD/Volume at entry/exit)

---

## Key Differences from Traditional Strategies

| Aspect | Traditional | This Strategy |
|--------|------------|---------------|
| **Entry Logic** | All conditions required (AND) | Scoring system (3/5 or 2/4) |
| **RSI Thresholds** | 30/70 (extreme) | 40/60 (relaxed) |
| **Volume Filter** | 1.5-2.0x (strict) | 1.1-1.2x (relaxed) |
| **Position Sizing** | Percentage-based | Fixed 10 contracts |
| **Short Positions** | Allowed | Not allowed (long-only) |
| **Exit Strategy** | Same as entry | Stricter than entry |
| **Cooldown** | None | 3-bar mandatory |
| **Regime Adaptation** | Single strategy | 4 regime-specific strategies |

---

## Common Questions

### Q1: Why is this better than strict AND logic?

**A**: Traditional strategies require ALL conditions to be true:
```
BUY = (EMA aligned) AND (RSI < 30) AND (Volume > 2x) AND ...
```

This generates **very few trades** because all conditions rarely align.

Our scoring system allows **partial confirmation**:
```
BUY = (Score >= 3 out of 5 conditions)
```

This generates **5-10x more trades** while maintaining quality.

---

### Q2: Why are exits stricter than entries?

**A**: To avoid premature exits and let winners run:

- **Entry**: RSI < 40 → Many opportunities
- **Exit**: RSI > 65 → Wait for genuine overbought

This asymmetry:
- ✅ Captures more trend movement
- ✅ Reduces whipsaw losses
- ✅ Improves profit factor

---

### Q3: Why long-only? Why not short in downtrends?

**A**: Simplicity and risk management:

1. **Portfolio only supports longs** (no short mechanism)
2. **Commodities have upward bias** (contango, inflation)
3. **Shorting has unlimited loss potential**
4. **Easier to understand and debug**

For shorting, you'd need:
- Separate short portfolio tracking
- Different risk management
- Margin requirements
- Borrowing costs

---

### Q4: Why 50 contracts per signal with 70% max allocation?

**A**: Position accumulation strategy:

**Current Approach**:
```python
contracts_per_signal = 50  # Fixed per buy signal
max_allocation = 0.70      # Can accumulate up to 70%
reserve = 0.30             # Keep 30% cash
```

**How It Works**:
```
Example at ¥780 price:
- First buy: 50 contracts = ¥39,000 (3.9% allocation)
- Second buy: 50 more = ¥39,000 (now 100 contracts, 7.8%)
- Continue buying dips up to ¥700,000 (70% of ¥1M)
- Max contracts at ¥780: ~897 contracts (17-18 buy signals)
```

**Benefits**:
- ✅ Accumulate into winning positions (average down)
- ✅ 30% reserve for deeper dips
- ✅ Large positions when right = bigger profits
- ✅ Flexible (don't need to time entry perfectly)

**Drawbacks**:
- ❌ Can accumulate into losers (catching falling knife)
- ❌ Larger drawdowns on reversals
- ❌ All-or-nothing exits (no scaling out)

---

### Q5: What happens during low-liquidity periods?

**A**: Volume filter protects against false signals:

```
Required: Volume > 1.1x to 1.2x average
```

If volume is too low:
- Signals don't generate (score too low)
- Existing positions held (no exit signal)
- Strategy waits for better conditions

---

### Q6: Can I adjust the parameters?

**A**: Yes! Key tunable parameters:

**Aggressiveness**:
```python
cooldown_bars = 3  # Reduce to 1-2 for more trades
```

**Entry Thresholds**:
```python
# Uptrend
score_required = 3  # Reduce to 2 for more entries
rsi_oversold = 40   # Increase to 45 for more entries

# Ranging
score_required = 2  # Reduce to 1 for more entries
```

**Exit Thresholds**:
```python
# Uptrend
exit_score_required = 2  # Increase to 3 for longer holds
rsi_overbought = 65      # Increase to 70 for longer holds

# Ranging
exit_score_required = 3  # Increase to 4 for longer holds
```

**Volume**:
```python
volume_multiplier_uptrend = 1.2  # Reduce to 1.1 for more signals
volume_multiplier_ranging = 1.1  # Reduce to 1.05 for more signals
```

---

## Summary

This is a **relaxed, adaptive, long-only** trading strategy with **position accumulation** that:

✅ Uses 7 technical indicators for robust signal generation
✅ Adapts to 4 market regimes automatically
✅ Uses scoring system (not strict AND logic) for more trades
✅ **Accumulates positions** (adds 50 contracts per signal)
✅ **70% max allocation** with 30% cash reserve
✅ **Buy the dip strategy** (average down on pullbacks)
✅ **Sell all on exits** (take profit or cut loss completely)
✅ Has stricter exits than entries to let winners run
✅ Includes 3-bar cooldown after full exit
✅ Tracks average entry price for P&L calculation
✅ Preserves capital during extreme volatility

**Expected Trade Frequency**: 5-10x more than traditional strict strategies (more with accumulation)
**Position Sizing**: 50 contracts per signal, can accumulate 17-18 positions at ¥780 price
**Win Rate Target**: 35-55% (typical for trend/mean reversion hybrid with pyramiding)
**Risk Profile**: Moderate-High (long-only, position accumulation, 70% max exposure)

**Key Risk**: Accumulation can lead to larger drawdowns if market reverses after building position. The 30% cash reserve provides buffer for deeper dips but doesn't protect against extended downtrends.

**Key Advantage**: When right, accumulated position captures full trend move with larger size = significantly higher profits. Average entry price improves by buying dips.

---

**Last Updated**: 2025-11-05
**Version**: 2.0 (Position Accumulation)
**Status**: Code updated, ready for testing
