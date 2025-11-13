# Trinity Strategy Implementation - Project Overview

**Date**: November 13, 2025
**Project**: Trinity Strategy (Tier-1 Indicators + Tier-2 Composite Strategy)
**Framework**: WOS Trading Framework
**Environment**: VS Code with Debugpy, Python 3.10

---

## Project Architecture

### Phase-1: TrinityStrategy (Tier-1 Indicators)

**File**: `/workspaces/money-engineering/TrinityStrategy/TrinityStrategy.py`
**Type**: Multi-indicator system (3 independent Scouts)
**Export Namespace**: Private (`pc.namespace_private`)

**Three Scout Indicators**:
1. **WOS_TrendScout**: ADX + Directional Movement (regime detection)
   - Outputs: `adx_value`, `di_plus`, `di_minus`
   - Purpose: Identify trending vs ranging markets

2. **WOS_TensionScout**: Bollinger Bands with online variance
   - Outputs: `upper_band`, `middle_band`, `lower_band`
   - Purpose: Measure volatility and overbought/oversold

3. **WOS_CrowdScout**: VWMA Oscillator
   - Outputs: `conviction_oscillator`
   - Purpose: Detect volume confirmation

**Markets & Securities**:
- **DCE**: i (Iron Ore), j (Coke), m (Soybean Meal), y (Soybean Oil)
- **SHFE**: cu (Copper), sc (Crude Oil), al (Aluminum), rb (Rebar), au (Gold), ru (Rubber)
- **CZCE**: TA (PTA), MA (Methanol)
- **Total**: 12 commodities

**Granularity**: 900s (15 minutes)

**Export Configuration** (`uout.json`):
- Exports 9 fields to private namespace
- Fields: `_preserved_field`, `bar_index`, and 8 Scout outputs
- Each commodity exports its own data stream

---

### Phase-2: TrinityCaptain (Tier-2 Composite Strategy)

**File**: `/workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/WOS_Captain.py`
**Type**: Fund manager with 12 independent baskets
**Strategy Name**: `TrinityCaptain`

**Architecture**:
- **12 Trading Baskets**: One per commodity
- **Risk Parity Sizing**: Position sizes inversely proportional to volatility
- **Regime-Adaptive**: Different logic for trending (RIVER) vs ranging (LAKE) markets
- **Risk Management**: Portfolio and per-basket drawdown limits

**Data Sources (Dual Import)**:
1. **Global Namespace**: SampleQuote (OHLCV data)
   - Fields: open, high, low, close, volume, turnover
2. **Private Namespace**: TrinityStrategy (Scout indicators)
   - Fields: All 9 fields from Phase-1 export

**Trading Logic**:
- **RIVER Mode** (ADX > threshold): Trend-following, hold overnight
- **LAKE Mode** (ADX < threshold): Mean-reversion, intraday only (exit at 14:55)
- **DEAD ZONE** (ADX between thresholds): Flat, avoid whipsaws

**Risk Limits**:
- Portfolio DD > 10%: Reduce all positions by 50%
- Portfolio DD > 20%: Flatten all positions
- Basket DD > 15%: Close that specific basket

---

## Technical Implementation Details

### Tier-1 to Tier-2 Data Flow

```
TrinityStrategy (Tier-1)
├── Processes OHLCV bars (SampleQuote)
├── Calculates Scout indicators
├── Exports to private namespace
└── Publishes data per commodity

        ↓

TrinityCaptain (Tier-2)
├── Imports SampleQuote (global namespace)
├── Imports TrinityStrategy (private namespace)
├── Combines both data sources
└── Generates trading signals per basket
```

### Key Framework Patterns Used

1. **Multi-commodity Management**: Separate parser instances per commodity
2. **Dual Namespace Imports**: Both global (OHLCV) and private (indicators)
3. **Basket-based Portfolio**: Each commodity trades independently
4. **State Persistence**: Using `_preserved_field` for framework state
5. **Contract Rolling**: Automatic handling of futures contract expiry

---

## Development Setup

**Launch Configurations** (`.vscode/launch.json`):
- **Phase-1**: TrinityStrategy - Quick Test (7 days)
- **Phase-2**: Captain - Quick Test (7 days)
- **Phase-2**: Captain - Full Backtest (1 year)
- **Phase-2**: Captain - Multi-Year (3 years)

**Test Parameters**:
- Start: 20241025000000 (Oct 25, 2024)
- End: 20241101000000 (Nov 1, 2024)
- Granularity: 900s
- Category: 1 (Indicators and Tier-2)
- Multiproc: 1 (parallel execution)

---

## Issues Encountered

This journal documents **6 major issues** encountered during Phase-2 implementation:

1. ❌ **Incompatible struct value** (Initial attempt - _preserved_field)
2. ⏸️ **Category=2 debugger hang**
3. ⚠️ **Missing revision field**
4. ⛔ **Duplicate strategy name**
5. ✅ **Contract code mismatch** (Actual root cause - FIXED)
6. ❓ **Visualization data fetch failure** (UNRESOLVED)

Each issue is documented in detail in the following files.

---

**Next**: [01-preserved-field-issue.md](./01-preserved-field-issue.md)
