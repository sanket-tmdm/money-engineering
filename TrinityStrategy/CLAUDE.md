# CLAUDE.md - Trinity Strategy Phase 1

This file provides guidance to Claude Code when working on the TrinityStrategy project.

## Project Overview

**Project**: TrinityStrategy (Phase 1 - Scout Indicators)
**Type**: Tier 1 Indicator - Multi-Scout System
**Markets**: DCE (Dalian), SHFE (Shanghai)
**Securities**:
- DCE: i (Iron Ore - Trending market)
- SHFE: cu (Copper - Ranging market)
- SHFE: sc (Crude Oil - Volatile/Wild card)
**Granularities**: 900s (15 minutes)

### Description

Implements the "Trinity" adaptive trading system's three independent Scout indicators:

1. **WOS_TrendScout**: ADX + Directional Movement Indicator
   - Purpose: Identifies market regime - "Tricky Pitch" (ranging) vs "Flat Pitch" (trending)
   - Outputs: `adx_value`, `di_plus`, `di_minus`
   - Threshold: ADX > 25 = strong trend, ADX < 20 = ranging

2. **WOS_TensionScout**: Stateless Bollinger Bands
   - Purpose: Measures "batsman's stretch" - volatility and overbought/oversold
   - Innovation: Uses Welford's online variance (NOT traditional rolling window)
   - Outputs: `upper_band`, `middle_band`, `lower_band`

3. **WOS_CrowdScout**: VWMA Oscillator
   - Purpose: Detects "crowd roar" - volume conviction
   - Algorithm: VWMA - EMA(Price)
   - Outputs: `conviction_oscillator` (> 0 bullish, < 0 bearish)

### Architecture Philosophy

Following the "Captain's Playbook" analogy (trinity-strategy.md):
1. **Identify the Pitch** (TrendScout): Is it ranging or trending?
2. **Check the Batsman** (TensionScout): Is price stretched?
3. **Listen to the Crowd** (CrowdScout): Is volume confirming?

## Implementation Status

- [x] Basic project structure created
- [x] All three Scout classes implemented
- [x] Multi-commodity manager implemented
- [x] Configuration files (uin.json, uout.json) configured
- [ ] Quick test passing
- [ ] Visual validation completed
- [ ] Replay consistency test passing
- [ ] Parameters optimized
- [ ] Ready for Phase 2 (Captain Strategy)

## Key Implementation Details

### Input Configuration (uin.json)

Imports:
- **SampleQuote** (OHLCV data) from global namespace
- Markets: DCE, SHFE
- Securities: i (Iron Ore), cu (Copper), sc (Crude Oil)
- Granularities: 900s (15 minutes)

### Output Configuration (uout.json)

Exports to private namespace (9 fields total):
- `_preserved_field` - Framework required
- `bar_index` - Bar counter

**TrendScout outputs:**
- `adx_value` - ADX trend strength (0-100)
- `di_plus` - Positive directional indicator
- `di_minus` - Negative directional indicator

**TensionScout outputs:**
- `upper_band` - Bollinger upper band
- `middle_band` - Bollinger middle band (20-EMA)
- `lower_band` - Bollinger lower band

**CrowdScout outputs:**
- `conviction_oscillator` - VWMA - EMA oscillator

### Algorithm Details

#### 1. WOS_TrendScout (ADX Calculation)

**Online EMA-based ADX** (O(1) memory):
```
TR = max(H-L, |H-prev_C|, |L-prev_C|)
+DM = max(H-prev_H, 0) if H-prev_H > prev_L-L
-DM = max(prev_L-L, 0) if prev_L-L > H-prev_H

TR_EMA = EMA(TR, α=2/15)
+DM_EMA = EMA(+DM, α=2/15)
-DM_EMA = EMA(-DM, α=2/15)

DI+ = 100 × (+DM_EMA / TR_EMA)
DI- = 100 × (-DM_EMA / TR_EMA)
DX = 100 × |DI+ - DI-| / (DI+ + DI-)
ADX = EMA(DX, α=2/15)
```

**Parameters:**
- Period: 14 (standard ADX)
- Alpha: 2/15 = 0.1333

#### 2. WOS_TensionScout (Stateless Bollinger Bands)

**Welford's Online Variance with EMA Decay**:
```
delta = price - ema_mean
ema_mean += α × delta
ema_var += α × (delta² - ema_var)
std_dev = √ema_var

Middle = ema_mean
Upper = Middle + 2×std_dev
Lower = Middle - 2×std_dev
```

**Parameters:**
- Period: 20 (20-EMA)
- Alpha: 2/21 = 0.0952
- Std Dev Multiplier: 2

**Key Innovation**: No rolling window! Uses online variance algorithm for O(1) memory.

#### 3. WOS_CrowdScout (VWMA Oscillator)

**Volume-Weighted Moving Average Oscillator**:
```
PV_EMA = EMA(Price × Volume, α=2/11)
V_EMA = EMA(Volume, α=2/11)
Price_EMA = EMA(Price, α=2/11)

VWMA = PV_EMA / V_EMA
Conviction = VWMA - Price_EMA
```

**Parameters:**
- Period: 10 (10-EMA)
- Alpha: 2/11 = 0.1818

**Interpretation:**
- Conviction > 0: Bullish (volume supporting higher prices)
- Conviction < 0: Bearish (volume supporting lower prices)

### State Management

**Per-Commodity State** (WOS Doctrine 1: Multiple Indicator Objects):
- Each commodity (i, cu, sc) has its own set of three Scouts
- Total: 9 Scout instances (3 commodities × 3 Scouts)
- No state contamination between commodities

**TrinityCommodityManager**:
- Manages one commodity's three Scouts
- Routes OHLCV data to all three Scouts
- Aggregates outputs into unified StructValue
- Handles cycle boundaries and serialization

**TrinityMultiCommodityManager**:
- Top-level manager for all three commodities
- Routes bars to appropriate commodity manager
- Filters for logical contracts (`<00>`)

## Critical Framework Rules

### ✅ Always Follow These Doctrines

1. **Multiple Indicator Objects** (DOCTRINE 1): Separate Scout instances per commodity
2. **No Fallback Logic** (DOCTRINE 2): Trust dependency data (no `if close is None`)
3. **Always Return List** (DOCTRINE 3): Framework callbacks return lists
4. **Logical Contract Filtering** (DOCTRINE 4): Only process contracts ending in `<00>`
5. **Online Algorithms** (WOS Ch 05): EMA, Welford's variance - no rolling windows
6. **Stateless Design**: All state in sv_object, deterministic calculations

## Development Workflow

### Running Tests

**Quick Test (7 days) - Persists data to server:**

1. Press `F5` in VS Code
2. Select: **"TrinityStrategy - Quick Test (7 days)"**
3. Wait for test to complete:
   ```
   [2025-11-11 XX:XX:XX][vanilla_logger][][DEBUG][...] Bar X: ADX=...
   ...
   pid=XXXXX, CMD_TC_FINISH_BACKTEST worker=0
   ON FINISHED
   ```
4. **IMPORTANT**: Manually stop debugger by pressing `Shift+F5` or clicking the red stop button
   - This is normal framework behavior when using `--is-managed 1`
   - Data has been uploaded to server even though debugger keeps running
   - All working indicators (IronOre, Copper, Soybean) work the same way

**Full Backtest (3 months):**
- Select: **"TrinityStrategy - Full Backtest (3 months)"**
- Same stop procedure after "ON FINISHED"

**Test Dates:**
- Quick Test: Oct 25 - Nov 1, 2024 (7 days)
- Full Backtest: Jan 1 - Apr 1, 2025 (3 months)

**Manual command (if needed):**
```bash
python /home/wolverine/bin/running/calculator3_test.py \
    --testcase . \
    --algoname TrinityStrategy \
    --sourcefile TrinityStrategy.py \
    --start 20241025000000 \
    --end 20241101000000 \
    --granularity 900 \
    --tm wss://10.99.100.116:4433/tm \
    --tm-master 10.99.100.116:6102 \
    --rails https://10.99.100.116:4433/private-api/ \
    --token YOUR_TOKEN \
    --category 1 \
    --is-managed 1 \
    --restore-length 864000000 \
    --multiproc 1
```

### Debugging

Set breakpoints in TrinityStrategy.py:
- **Line 465** (`TrinityCommodityManager.on_bar()`): Check data arrival
- **Line 508** (`_on_cycle_pass()`): Check Scout execution
- **Line 524-526**: Check individual Scout calculations
- **Line 543** (`ready_to_serialize()`): Check output control

**Key Debug Points:**
```python
# In _on_cycle_pass():
print(f"ADX={self.adx_value}, DI+={self.di_plus}, DI-={self.di_minus}")
print(f"BB: Upper={self.upper_band}, Mid={self.middle_band}, Lower={self.lower_band}")
print(f"Conviction={self.conviction_oscillator}")
```

### Phase 1 Validation (trinity-strategy.md § 5.2)

**Goal**: Visually confirm TrendScout ADX correctly identifies market regimes

**Test Procedure**:
1. Run 7-day quick test (generate outputs)
2. Use `svr3.sv_reader` to fetch and visualize data
3. Plot all Scout outputs for Iron Ore
4. Verify ADX behavior:
   - LOW (<20) during choppy/ranging periods
   - HIGH (>25) during strong trends

**Expected Results**:
- TrendScout: ADX rises in trending markets, falls in ranging markets
- TensionScout: Bands widen in volatile periods, narrow in calm periods
- CrowdScout: Oscillator confirms price moves with volume

### Visualization Script

**Jupyter Notebook**: `TrinityStrategy_viz.ipynb`

**Prerequisites:**
1. Run Quick Test or Full Backtest first (data must be on server)
2. Wait for "ON FINISHED" message
3. Stop debugger with Shift+F5

**To Visualize:**
1. Open `TrinityStrategy_viz.ipynb` in VS Code
2. Select Python 3.10.12 kernel (top-right)
3. Update Cell 3 if needed:
   - TOKEN is already configured
   - START_DATE = 20241025000000 (matches Quick Test)
   - END_DATE = 20241101000000
   - COMMODITY = 'i<00>' (Iron Ore, or change to 'cu<00>' or 'sc<00>')
4. Run all cells (Click "Run All")

**Output Plots:**
- **Panel 1**: TrendScout - ADX, DI+, DI- (regime detection)
- **Panel 2**: TensionScout - Bollinger Bands (volatility)
- **Panel 3**: CrowdScout - Conviction Oscillator (volume confirmation)
- Plus: Distribution histograms, correlation matrix, statistics

**Files Generated:**
- `TrinityStrategy_scouts_DATES.png`
- `TrinityStrategy_distributions_DATES.png`
- `TrinityStrategy_correlation_DATES.png`

## File Structure

```
TrinityStrategy/
├── .devcontainer/
│   └── devcontainer.json          # Docker container config
├── .vscode/
│   └── launch.json                # Debug configurations (3 test modes)
├── wos/ (symlink)                 # WOS framework documentation
├── TrinityStrategy.py             # Main implementation (ALL 3 SCOUTS)
├── TrinityStrategy_viz.ipynb      # Jupyter notebook for visualization
├── trinitystrategy_viz.py         # Python script version (optional)
├── uin.json                       # Input: SampleQuote for i, cu, sc
├── uout.json                      # Output: 9 Scout fields
├── test_resuming_mode.py          # Replay consistency test
├── CLAUDE.md                      # This file
├── README.md                      # Project readme
└── trinity_strategy.md            # Design specification
```

## Testing Checklist

### Phase 1 Testing (Current Phase)

- [ ] **Quick Test**: Run 7-day test, verify no errors
- [ ] **Output Validation**: All 9 fields populated for all 3 commodities
- [ ] **Visual Validation**: Plot ADX and verify regime detection
- [ ] **Replay Consistency**: `test_resuming_mode.py` passes
- [ ] **Parameter Validation**: EMA periods match spec (14, 20, 10)

### Success Criteria

✅ **ADX Regime Detection**:
- Iron Ore trending periods: ADX > 25
- Copper ranging periods: ADX < 20
- Transitions visible and logical

✅ **Bollinger Bands**:
- Bands expand during volatile periods
- Bands contract during calm periods
- No negative band widths

✅ **Conviction Oscillator**:
- Oscillates around zero
- Positive during volume-supported rallies
- Negative during volume-supported selloffs

## Common Issues & Solutions

### Issue: No output generated

**Problem**: `ready_to_serialize()` returns False

**Solution**: Check all three Scouts are initialized:
```python
# In TrinityCommodityManager:
def ready_to_serialize(self) -> bool:
    return (self.bar_index > 0 and
            self.trend_scout.initialized and    # Check this
            self.tension_scout.initialized and   # And this
            self.crowd_scout.initialized)        # And this
```

### Issue: ADX always zero

**Problem**: TR_EMA is zero (division by zero protection)

**Solution**: Verify first bar initialization in `WOS_TrendScout`:
```python
if not self.initialized:
    first_tr = high - low
    self.tr_ema = first_tr  # Must be > 0
```

### Issue: Bollinger Bands too wide/narrow

**Problem**: Incorrect alpha parameter

**Solution**: Verify alpha = 2/(N+1) for N=20:
```python
self.alpha = 2.0 / 21.0  # = 0.0952
```

### Issue: Conviction oscillator NaN

**Problem**: Division by zero when volume is zero

**Solution**: Already handled in `calculate_conviction()`:
```python
if volume < 0.001:  # Skip zero volume bars
    return
```

## Next Steps

### Immediate (Phase 1 Completion)

1. **Run Quick Test**: Verify implementation works
2. **Check Diagnostics**: Use VS Code diagnostics tool
3. **Create Visualization**: Implement `trinitystrategy_viz.py`
4. **Visual Validation**: Confirm ADX regime detection
5. **Replay Test**: Ensure stateless design works

### Phase 2 (Captain Strategy)

Once Phase 1 is validated:
1. Create `WOS_CaptainStrategy` class (Tier 2)
2. Import Trinity Scout outputs
3. Implement regime-adaptive logic (trinity-strategy.md § 4)
4. Generate final trading signals

## Resources

- **Trinity Strategy Spec**: `../trinity-strategy.md`
- **WOS Documentation**: `./wos/` (complete knowledge base)
- **Stateless Design**: `./wos/05-stateless-design.md` (Welford's algorithm)
- **Tier 1 Guide**: `./wos/07-tier1-indicator.md`
- **Visualization**: `./wos/10-visualization.md`
- **Testing Guide**: `./wos/06-backtest.md`

## Notes for Claude Code

When working on this project:

1. **All three Scouts are in ONE file**: `TrinityStrategy.py`
2. **Each Scout is independent**: No inter-Scout dependencies
3. **Multi-commodity pattern**: One Scout set per commodity
4. **Online algorithms only**: No arrays, no rolling windows
5. **Stateless design**: Perfect replay consistency required
6. **Logical contracts only**: Filter `code.endswith(b'<00>')`
7. **Trust dependency data**: No fallback values
8. **Always return lists**: Framework requirement

## Parameter Reference

| Scout | Indicator | Period | Alpha | Purpose |
|-------|-----------|--------|-------|---------|
| Trend | ADX | 14 | 0.1333 | Regime detection |
| Tension | BB | 20 | 0.0952 | Volatility |
| Crowd | VWMA | 10 | 0.1818 | Volume conviction |

---

**Last Updated**: 2025-11-10
**Status**: Phase 1 implementation complete - Ready for testing
**Next**: Quick test validation and visual confirmation
