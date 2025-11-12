# CLAUDE.md

This file provides guidance to Claude Code when working on the IronOreIndicator project.

## Project Overview

**Project**: IronOreIndicator
**Type**: Tier 1 Indicator (Signal Generator)
**Markets**: DCE (Dalian Commodity Exchange)
**Securities**: DCE: i (Iron Ore logical contract i<00>)
**Granularities**: 900s (15 minutes)

### Description

A multi-indicator confirmation system that combines three technical indicators to generate trading signals for iron ore futures:

1. **EMA Crossover** (Fast EMA vs Slow EMA) - Trend detection
2. **RSI** (Relative Strength Index) - Mean reversion / overbought-oversold conditions
3. **Volume Confirmation** - Liquidity validation

Signals are only generated when all three indicators align, providing high-confidence entry/exit points.

## Implementation Status

- [x] Basic structure created
- [x] Indicator logic implemented
- [x] Quick test passing
- [ ] Replay consistency test passing
- [x] Visualization notebook created
- [ ] Parameters optimized
- [ ] Full backtest completed
- [ ] Ready for production

## Key Implementation Details

### Input Configuration (uin.json)

Configured to import:
- **SampleQuote** (OHLCV data) from DCE market
- **Granularity**: 900s (15 minutes)
- **Security**: i (iron ore)

### Output Configuration (uout.json)

Exports to private namespace:
- `_preserved_field` - Framework required field
- `bar_index` - Bar counter (int)
- `indicator_value` - RSI value (double, 0-100)
- `signal` - Trading signal (int: -1, 0, 1)

### Algorithm Description

**Multi-Indicator Confirmation System**

The indicator uses three independent signals that must align for trade execution:

#### 1. EMA Crossover (Trend Detection)
- **Fast EMA**: 10-period (alpha = 0.1818)
- **Slow EMA**: 20-period (alpha = 0.0952)
- **Uptrend**: Fast EMA > Slow EMA
- **Downtrend**: Fast EMA < Slow EMA

#### 2. RSI Mean Reversion
- **Period**: 14-bar EMA (alpha = 0.1333)
- **Oversold**: RSI < 30 (potential buy)
- **Overbought**: RSI > 70 (potential sell)
- **Neutral**: 30 ≤ RSI ≤ 70

#### 3. Volume Confirmation
- **Volume EMA**: 20-period (alpha = 0.0952)
- **Threshold**: 1.2x average volume
- **Purpose**: Filter low-liquidity false signals

#### Signal Generation Logic

```python
BUY Signal (signal = 1):
  - Uptrend (fast EMA > slow EMA)
  - AND Oversold (RSI < 30)
  - AND High volume (volume > 1.2 × volume_ema)
  - Confidence: (30 - RSI) / 30

SELL Signal (signal = -1):
  - Downtrend (fast EMA < slow EMA)
  - AND Overbought (RSI > 70)
  - AND High volume (volume > 1.2 × volume_ema)
  - Confidence: (RSI - 70) / 30

NEUTRAL (signal = 0):
  - All other conditions
```

### Parameters

All indicators use **online algorithms** (EMA) for O(1) memory complexity:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `alpha_fast` | 0.1818 | Fast EMA smoothing (10-period) |
| `alpha_slow` | 0.0952 | Slow EMA smoothing (20-period) |
| `alpha_rsi` | 0.1333 | RSI gain/loss EMA (14-period) |
| `alpha_vol` | 0.0952 | Volume EMA smoothing (20-period) |
| `volume_multiplier` | 1.2 | Volume confirmation threshold |
| `rsi_oversold` | 30.0 | RSI oversold threshold |
| `rsi_overbought` | 70.0 | RSI overbought threshold |

### State Management

The indicator maintains the following state (auto-persisted via `sv_object`):

**Counters & Metadata:**
- `bar_index` (int) - Bar counter
- `timetag` (int) - Current cycle timestamp
- `initialized` (bool) - Initialization flag

**EMA State:**
- `ema_fast` (float) - Fast EMA value
- `ema_slow` (float) - Slow EMA value
- `volume_ema` (float) - Volume EMA value

**RSI State:**
- `rsi` (float) - Current RSI value (0-100)
- `gain_ema` (float) - EMA of price gains
- `loss_ema` (float) - EMA of price losses
- `prev_close` (float) - Previous close price

**Output State:**
- `signal` (int) - Trading signal (-1, 0, 1)
- `confidence` (float) - Signal confidence [0.0, 1.0]
- `indicator_value` (float) - Main indicator (RSI)

## Critical Framework Rules

### ✅ Always Follow These Doctrines

1. **Multiple Indicator Objects**: Separate instances per commodity (currently one for i<00>)
2. **No Fallback Logic**: Trust dependency data format (no `if close is None`)
3. **Always Return List**: Framework callbacks return lists
4. **Logical Contract Filtering**: Only process contracts ending in `<00>`
5. **Code Format Convention**: DCE/SHFE lowercase, CZCE UPPERCASE
6. **Online Algorithms**: Use EMA, not rolling windows (bounded memory)
7. **Replay Consistency**: No `random`, no `datetime.now()`, no external state

## Development Workflow

### Running Tests

```bash
# Quick test (7 days: 2024-10-25 to 2024-11-01)
# Press F5 in VS Code, select "IronOreIndicator - Quick Test"
# OR
python3 calculator3_test.py --testcase . --algoname IronOreIndicator \
  --sourcefile IronOreIndicator.py --start 20241025000000 --end 20241101000000 \
  --granularity 900 --multiproc 1 --category 1

# Replay consistency (MANDATORY before production)
python test_resuming_mode.py

# Full backtest (multi-year)
# Press F5, select "IronOreIndicator - Full Backtest"
```

### Debugging

Set breakpoints in `IronOreIndicator.py`:
- **Line 122** (`on_bar()`): Check data arrival and filtering
- **Line 175** (`_on_cycle_pass()`): Check indicator calculations
- **Line 258** (`_generate_signal()`): Check signal generation logic
- **Line 295** (`ready_to_serialize()`): Check output control

### Visualization and P&L Analysis

**Jupyter Notebook**: `trading_simulation.ipynb`

This notebook:
1. Fetches indicator signals from svr3 server (private namespace)
2. Fetches price data (OHLCV) from svr3 server (global namespace)
3. Simulates trading with $1000 starting capital
4. Calculates P&L curve based on signals
5. Visualizes:
   - Portfolio value over time
   - Cumulative P&L
   - Position and signals
   - RSI indicator values
6. Exports results to CSV

**Running the notebook:**

```bash
# Set environment variables first
export SVR_HOST="10.99.100.116"
export SVR_TOKEN="your_token_here"

# Launch Jupyter
jupyter notebook trading_simulation.ipynb

# Or use VS Code with Jupyter extension
```

**Trading Simulation Logic:**

```python
Starting Capital: $1000

BUY Signal (signal=1):
  - If not in position: Buy contracts with available cash
  - Entry price recorded

SELL Signal (signal=-1):
  - If in position: Close position at current price
  - Calculate P&L: (exit_price - entry_price) × contracts

NEUTRAL Signal (signal=0):
  - Hold current position

Portfolio Value = Cash + (Position × Current Price)
```

## File Structure

```
IronOreIndicator/
├── IronOreIndicator.py          # Main indicator implementation
├── uin.json                     # Input configuration
├── uout.json                    # Output configuration
├── trading_simulation.ipynb     # P&L analysis notebook
├── test_resuming_mode.py        # Replay consistency test
├── .vscode/
│   └── launch.json             # Debug configurations
├── wos/                        # WOS framework documentation
│   ├── INDEX.md               # Quick reference
│   ├── 01-overview.md         # Framework overview
│   ├── 05-stateless-design.md # Online algorithms guide
│   ├── 06-backtest.md         # Testing guide
│   ├── 07-tier1-indicator.md  # Tier 1 development
│   └── 10-visualization.md    # Visualization guide
└── CLAUDE.md                   # This file
```

## Implementation Walkthrough

### Step 1: Configuration (uin.json, uout.json)

Define inputs and outputs following WOS conventions:
- uin.json: Import SampleQuote (OHLCV) from DCE
- uout.json: Export signal, indicator_value, bar_index

### Step 2: State Variables

Define all state in `__init__()`:
```python
# Metadata (constants)
self.meta_name = "IronOreIndicator"
self.namespace = pc.namespace_private
self.market = b'DCE'
self.code = b'i<00>'

# State (persisted)
self.ema_fast = 0.0
self.rsi = 50.0
self.signal = 0
```

### Step 3: Data Processing (on_bar)

Route incoming bars to appropriate handlers:
```python
def on_bar(self, bar: pc.StructValue) -> List[pc.StructValue]:
    # Filter by market/code
    # Parse into sv_object with from_sv()
    # Handle cycle boundaries
    # Call _on_cycle_pass() at cycle end
    # Serialize with copy_to_sv()
    return ret  # Always return list
```

### Step 4: Indicator Logic (_on_cycle_pass)

Calculate indicators using online algorithms:
```python
# Update EMAs (O(1) memory)
self.ema_fast = alpha * close + (1 - alpha) * self.ema_fast

# Update RSI (online via gain/loss EMAs)
gain = max(close - prev_close, 0)
self.gain_ema = alpha * gain + (1 - alpha) * self.gain_ema
```

### Step 5: Signal Generation

Combine indicators for high-confidence signals:
```python
if uptrend and oversold and high_volume:
    self.signal = 1  # BUY
elif downtrend and overbought and high_volume:
    self.signal = -1  # SELL
else:
    self.signal = 0  # NEUTRAL
```

### Step 6: Testing

1. **Quick Test**: Verify basic functionality (7 days)
2. **Replay Test**: Ensure determinism (`test_resuming_mode.py`)
3. **Visualization**: Analyze signals in notebook
4. **Full Backtest**: Multi-year validation

### Step 7: Visualization & Analysis

Use `trading_simulation.ipynb`:
1. Set environment variables (`SVR_HOST`, `SVR_TOKEN`)
2. Run notebook cells sequentially
3. Review P&L curve and performance metrics
4. Iterate on parameters if needed

## Notes for Claude Code

When working on this project:

1. **Always check uin.json and uout.json** for configuration
2. **Follow the sv_object pattern** for state management
3. **Use online algorithms** (EMA, not rolling windows)
4. **Ensure replay consistency** (no random values, no system time)
5. **Filter for logical contracts** (`code.endswith(b'<00>')`)
6. **Return lists** from all framework callbacks
7. **Trust dependency data** (no fallback values)
8. **Test incrementally**: Quick test → Replay test → Full backtest
9. **Visualize early**: Use notebook to understand signal behavior
10. **Document changes**: Update this file when making modifications

## Common Issues & Solutions

### Issue: AttributeError on serialization

**Problem**: `'IronOreIndicator' object has no attribute 'indicator_value'`

**Solution**: Ensure all fields in `uout.json` exist as attributes in `__init__()`:
```python
self.indicator_value = 0.0  # Must exist!
```

### Issue: No output generated

**Problem**: `ready_to_serialize()` returns False

**Solution**: Check initialization and bar_index:
```python
def ready_to_serialize(self) -> bool:
    return self.bar_index > 0 and self.initialized
```

### Issue: Replay test fails (non-determinism)

**Problem**: Different results on repeated runs

**Solution**: Remove all sources of randomness:
- No `random.random()`
- No `datetime.now()` or `time.time()`
- No external API calls
- Use EMA, not random sampling

## Resources

- **Framework Documentation**: `./wos/` (complete WOS knowledge base)
- **Visualization Guide**: `./wos/10-visualization.md`
- **Testing Guide**: `./wos/06-backtest.md`
- **Tier 1 Guide**: `./wos/07-tier1-indicator.md`
- **Stateless Design**: `./wos/05-stateless-design.md`
- **Quick Reference**: `./wos/INDEX.md`

## Next Steps

High Priority:
- [ ] Run replay consistency test (`test_resuming_mode.py`)
- [ ] Analyze P&L curve from trading simulation
- [ ] Optimize parameters based on analysis
- [ ] Run full backtest (multi-year)

Medium Priority:
- [ ] Add confidence thresholds for signal filtering
- [ ] Experiment with different RSI periods
- [ ] Add additional volume confirmation metrics
- [ ] Create standalone visualization script

Low Priority:
- [ ] Add logging for parameter tuning
- [ ] Document optimal parameter ranges
- [ ] Create parameter sweep analysis
- [ ] Build Tier 2 composite strategy

---

**Last Updated**: 2025-11-04

**Status**: Quick test passing, trading simulation working, ready for replay consistency test
