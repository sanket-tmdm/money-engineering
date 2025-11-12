# Intelligent Position Accumulation Strategy

**Reference Implementation:** `IronOreIndicator/IronOreIndicator.py`

## The Problem: Binary Signals Can't Accumulate

Traditional indicators output simple signals that prevent position building:

```python
# Traditional approach - LIMITATION
signal = 1   # Buy
signal = -1  # Sell
signal = 0   # Hold
```

**Result:**
```
Time    Signal    Position
T1      +1        50 contracts
T2      +1        50 contracts  ❌ Signal ignored - can't add
T3      +1        50 contracts  ❌ Missed accumulation
```

You're stuck at 50 contracts even with multiple confirming buy signals.

## The Solution: Intelligent Accumulation

Track **three separate values** to enable true position building:

```python
# New fields
self.signal_strength = 0.0      # 0.0-1.0 conviction level
self.desired_contracts = 0      # Target position size
self.contracts_to_add = 0       # How many to add this signal
```

**Result:**
```
Time    RSI    Score    Contracts_Add    Total
T1      42     3/5      50              50
T2      38     2/5      50              100  ✓ Added!
T3      33     3/5      100             200  ✓ Aggressive dip!
T4      48     2/5      50              250  ✓ Keep building!
```

## Key Innovation 1: Adaptive Buy Thresholds

**Initial Entry** (when flat):
- Requires **3/5** confirmation signals
- Higher bar for starting a position

**Add to Position** (already holding):
- Requires only **2/5** confirmation signals
- MUCH easier to accumulate once in

```python
if self.position_state == 1:
    # EASIER: Only need 2/5 to add to existing position
    required_score_entry = 2
else:
    # INITIAL: Need 3/5 for first entry
    required_score_entry = 3

buy_score = self._calculate_uptrend_buy_score()
if buy_score >= required_score_entry:
    self.signal = 1  # BUY
```

This is the **secret sauce** - once you're in a position, the threshold drops dramatically making accumulation natural.

## Key Innovation 2: Aggressive Dip Buying

Dynamically determine contract size based on dip strength:

```python
# Determine contracts to add based on RSI
if self.rsi < 35:
    # STRONG dip - aggressive buying
    self.contracts_to_add = 100
elif self.rsi < 45:
    # MEDIUM dip - standard buying
    self.contracts_to_add = 50
else:
    # NO dip - standard entry
    self.contracts_to_add = 50
```

**Example:**
- Normal conditions (RSI 48): Buy 50 contracts
- Medium dip (RSI 42): Buy 50 contracts
- **Strong dip (RSI 33): Buy 100 contracts** ← 2x buying power!

## Key Innovation 3: Signal Strength Calculation

Calculate conviction from multiple factors:

```python
def _calculate_signal_strength(self):
    """Multi-factor conviction (0.0-1.0)"""
    strength = 0.0
    count = 0

    # Factor 1: RSI distance (how oversold)
    if self.rsi < 50:
        rsi_strength = (50.0 - self.rsi) / 50.0
        strength += rsi_strength
        count += 1

    # Factor 2: MACD strength
    if self.macd > self.macd_signal:
        macd_strength = min(abs(self.macd_histogram) / 10.0, 1.0)
        strength += macd_strength
        count += 1

    # Factor 3: Trend alignment
    if self.ema_12 > self.ema_26:
        ema_distance = (self.ema_12 / self.ema_26 - 1.0) * 100
        trend_strength = min(abs(ema_distance) / 2.0, 1.0)
        strength += trend_strength
        count += 1

    # Factor 4: BB position
    bb_range = self.bb_upper - self.bb_lower
    if bb_range > 0:
        distance = abs(self.bb_middle - self.close)
        bb_strength = min(distance / bb_range, 1.0)
        strength += bb_strength
        count += 1

    # Average
    if count > 0:
        self.signal_strength = strength / count
```

## Key Innovation 4: Score-Based Buy Signals

Each regime calculates a buy score (0-5 or 0-6):

```python
def _calculate_uptrend_buy_score(self):
    """Calculate BUY score for uptrend (returns 0-5)"""
    score = 0

    # 1. Trend aligned
    if self.ema_12 > self.ema_26:
        score += 1

    # 2. Momentum bullish
    if self.macd > self.macd_signal:
        score += 1

    # 3. RSI shows dip (RELAXED: increased to 50)
    if self.rsi < 50:
        score += 1

    # 4. Volume confirmation (RELAXED: 1.1x)
    if self.volume > (self.volume_ema * 1.1):
        score += 1

    # 5. Price showing dip
    bb_range = self.bb_upper - self.bb_lower
    if bb_range > 0 and self.close <= (self.bb_lower + bb_range * 0.3):
        score += 1

    return score
```

**Thresholds:**
- Initial entry: `score >= 3` (60%)
- Add to position: `score >= 2` (40%)

## Key Innovation 5: Stricter Exits

Exit only on **clear reversals**, not minor weakness:

```python
def _check_uptrend_exit_strict(self):
    """STRICTER uptrend exit - need 3/4 signals"""
    exit_score = 0

    # 1. RSI very overbought (65+, not 60+)
    if self.rsi > 65:
        exit_score += 1

    # 2. MACD clear bearish cross (with histogram check)
    if self.macd < self.macd_signal and self.macd_histogram < -0.5:
        exit_score += 1

    # 3. Price breaks below BOTH EMAs
    if self.close < self.ema_12 and self.close < self.ema_26:
        exit_score += 1

    # 4. Price showing clear weakness (bottom 30%)
    if self.high > self.low:
        bar_position = (self.close - self.low) / (self.high - self.low)
        if bar_position < 0.3:
            exit_score += 1

    return exit_score >= 3  # Need 3/4 (75%) to exit
```

**Old behavior:** Exit on 2/4 (50%) → too sensitive
**New behavior:** Exit on 3/4 (75%) → hold through noise

## Complete Signal Flow

```python
def _generate_signal(self):
    # Step 1: Calculate signal strength (0.0-1.0)
    self._calculate_signal_strength()

    # Step 2: Determine contracts to add (50 or 100)
    if self.rsi < 35:
        self.contracts_to_add = 100  # Aggressive
    elif self.rsi < 45:
        self.contracts_to_add = 50   # Standard
    else:
        self.contracts_to_add = 50   # Normal

    # Step 3: Check position limits
    proposed_value = (self.contracts_held + self.contracts_to_add) * self.close
    can_add = proposed_value / self.portfolio_value <= 0.70

    # Step 4: Determine required score
    if self.position_state == 1:
        required_score = 2  # Easier when in position
    else:
        required_score = 3  # Stricter for initial entry

    # Step 5: Calculate buy score and compare
    if self.regime == 1:  # Uptrend
        buy_score = self._calculate_uptrend_buy_score()
        if buy_score >= required_score:
            self.signal = 1  # BUY

    # Step 6: Check exits (stricter)
    if self.position_state == 1:
        if self._check_uptrend_exit_strict():  # Need 3/4
            self.signal = -1  # SELL ALL
```

## Portfolio Update

```python
def _update_portfolio(self):
    if self.signal == 1:
        # Use dynamic contracts_to_add
        cost = self.contracts_to_add * self.close
        if self.cash >= cost:
            # Update average entry price
            total_before = self.contracts_held * self.entry_price
            new_cost = self.contracts_to_add * self.close
            new_total = self.contracts_held + self.contracts_to_add
            self.entry_price = (total_before + new_cost) / new_total

            # Add contracts
            self.contracts_held += self.contracts_to_add
            self.cash -= cost

    elif self.signal == -1:
        # Close ALL
        self.cash += self.contracts_held * self.close
        self.contracts_held = 0
        self.entry_price = 0.0
```

## Example Trading Scenario

Market in uptrend with multiple dips:

| Bar | Price | RSI | EMA12>26 | MACD>Sig | Vol>1.1x | Score | State | Threshold | Action | Contracts |
|-----|-------|-----|----------|----------|----------|-------|-------|-----------|--------|-----------|
| 1 | 650 | 48 | ✓ | ✓ | ✓ | 3/5 | Flat | 3/5 | BUY 50 | 50 |
| 2 | 645 | 42 | ✓ | ✓ | ✗ | 2/5 | Holding | 2/5 | BUY 50 | 100 |
| 3 | 640 | 34 | ✓ | ✓ | ✓ | 3/5 | Holding | 2/5 | **BUY 100** | **200** |
| 4 | 648 | 46 | ✓ | ✓ | ✗ | 2/5 | Holding | 2/5 | BUY 50 | 250 |
| 5 | 655 | 52 | ✓ | ✓ | ✗ | 2/5 | Holding | 2/5 | HOLD | 250 |
| 6 | 660 | 58 | ✓ | ✓ | ✗ | 2/5 | Holding | 2/5 | HOLD | 250 |
| 7 | 658 | 66 | ✗ | ✗ | ✗ | 2/4 | Holding | 3/4 | HOLD | 250 |
| 8 | 652 | 68 | ✗ | ✗ | ✗ | 3/4 | Holding | 3/4 | **SELL ALL** | 0 |

**Key observations:**
- Bar 1: Initial entry needs 3/5
- Bar 2: Add with only 2/5 (threshold dropped!)
- Bar 3: **Aggressive 100 contracts** on strong dip (RSI 34)
- Bar 4: Another 50 added with 2/5
- Bar 7: Exit score 2/4 - NOT enough (need 3/4)
- Bar 8: Exit score 3/4 - CLEAR reversal, exit all

**Total profit:** (652 - avg_entry) × 250 contracts

## Configuration in uout.json

Add new fields to track accumulation:

```json
{
  "fields": [
    "signal",
    "confidence",
    "signal_strength",     // NEW: 0.0-1.0 conviction
    "desired_contracts",   // NEW: Target position
    "contracts_to_add",    // NEW: 50 or 100
    "contracts_held",
    "portfolio_value"
  ],
  "defs": [
    {"field_type": "integer"},    // signal
    {"field_type": "double", "precision": 4},  // confidence
    {"field_type": "double", "precision": 4},  // signal_strength
    {"field_type": "integer"},    // desired_contracts
    {"field_type": "integer"},    // contracts_to_add
    {"field_type": "integer"},    // contracts_held
    {"field_type": "double", "precision": 2}   // portfolio_value
  ]
}
```

## Benefits of This Approach

### 1. Natural Accumulation
- Lower threshold (2/5) when already in position
- Multiple buys in same trend become natural
- Build to 200+ contracts easily

### 2. Aggressive on Strong Signals
- 100 contracts on RSI < 35 (vs always 50)
- Doubles down when conviction is highest
- Maximizes profit on best opportunities

### 3. Hold Through Noise
- Stricter exits (3/4 vs 2/4)
- Don't exit on minor pullbacks
- Let winners run longer

### 4. Visible Conviction
- `signal_strength` shows confidence
- `contracts_to_add` shows aggression level
- `desired_contracts` shows target position
- Easy to debug and optimize

### 5. Risk Management
- Still respects 70% allocation limit
- Always closes ALL on clear reversals
- No partial exits (simplifies tracking)

## Common Patterns

### Pattern 1: Dip Buying in Uptrend
```
Entry → Dip1 → Dip2 → Dip3 → Exit
50    → 100  → 150  → 250  → 0
```

### Pattern 2: Aggressive on Crashes
```
Entry → Crash (RSI 32) → Recovery → Exit
50    → 150            → 200      → 0
```

### Pattern 3: Build and Hold
```
Entry → Add → Add → Add → Hold... → Exit
50    → 100 → 150 → 200 → 200... → 0
```

## Testing the Implementation

```python
# Verify accumulation
assert indicator.contracts_held == 0  # Start flat
# ... simulate bars with dips ...
assert indicator.contracts_held == 50   # First entry
assert indicator.contracts_held == 100  # Added 50
assert indicator.contracts_held == 200  # Added 100 (strong dip)
assert indicator.contracts_held == 250  # Added 50
# ... reversal ...
assert indicator.contracts_held == 0    # Exit all
```

## Summary

**Core Changes from Traditional:**
1. **Adaptive thresholds**: 3/5 initial, 2/5 to add (was fixed 3/5)
2. **Aggressive sizing**: 100 contracts on RSI < 35 (was fixed 50)
3. **Stricter exits**: Need 3/4 signals (was 2/4)
4. **Signal strength**: Visible 0.0-1.0 conviction tracking
5. **Position tracking**: `desired_contracts` and `contracts_to_add` exposed

**Result:** True position accumulation that maximizes profits on strong trends while cutting losses on clear reversals.

**Files:**
- Implementation: `IronOreIndicator/IronOreIndicator.py`
- Configuration: `IronOreIndicator/uout.json`
- This guide: `STRATEGY_GUIDE.md`
