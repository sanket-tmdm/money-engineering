# Trinity Strategy Documentation

This directory contains comprehensive documentation for the Trinity Strategy implementation.

## Phase-1: Scout Indicators (Tier-1) - COMPLETED

Phase-1 implements three independent Scout indicators that analyze market conditions:

1. **WOS_TrendScout**: ADX + Directional Movement (regime detection)
2. **WOS_TensionScout**: Stateless Bollinger Bands (volatility/stretch)
3. **WOS_CrowdScout**: VWMA Oscillator (volume conviction)

**Status**: Implemented, tested, tuned, and validated
**Implementation**: `/workspaces/money-engineering/TrinityStrategy/TrinityStrategy.py`
**Documentation**: `/workspaces/money-engineering/TrinityStrategy/CLAUDE.md`

## Phase-2: Captain Strategy (Tier-2) - IN PROGRESS

Phase-2 implements the WOS_CaptainStrategy composite strategy that consumes Scout outputs and generates trading signals.

### Key Documents

| Document | Size | Purpose | Status |
|----------|------|---------|--------|
| **[Phase-2-Captain-Implementation.md](./Phase-2-Captain-Implementation.md)** | 68KB | Complete implementation guide | ✅ Complete |
| **[Phase-2-Summary.md](./Phase-2-Summary.md)** | 5KB | Quick reference checklist | ✅ Complete |
| **[Phase-2.md](./Phase-2.md)** | 9KB | Original design notes | ✅ Complete |

### Phase-2-Captain-Implementation.md (Main Guide)

**Comprehensive 68KB guide covering**:

1. **Overview** - Phase-2 goals, architecture, WOS positioning
2. **12-Basket Architecture** - Why one basket per commodity, benefits, allocation strategy
3. **Data Sources** - SampleQuote vs Tier-1 outputs, two-parser design
4. **Risk Management** - Position sizing, per-basket DD, portfolio DD limits
5. **Regime Logic** - River/Lake/Dead Zone detailed explanation with code
6. **Intraday Exit Logic** - Why Lake mode exits at 14:55, session handling
7. **File Structure** - All new files to be created
8. **Implementation Architecture** - Classes, parsers, callbacks, routing logic
9. **Testing Workflow** - 4-stage testing process
10. **Success Criteria** - Functional and performance validation
11. **Expected Performance** - Per-regime, per-commodity metrics
12. **Troubleshooting** - Common issues and solutions

**Total**: 2,153 lines with extensive code examples

### Phase-2-Summary.md (Quick Reference)

**Quick-start guide covering**:
- Files to create checklist
- 10-step implementation sequence
- Critical components overview
- MANDATORY callbacks (on_reference, etc.)
- Testing sequence
- Expected performance targets
- Common issues table
- Key insights (Why 12 baskets? Why SampleQuote + ScoutParser? Why intraday-only Lake?)

**Use this for**: Quick refresher, implementation checklist

### Phase-2.md (Original Design)

**Early design notes covering**:
- Trinity playbook concept
- Parameter tuning results
- Risk parity sizing calculations
- Initial Captain logic sketch
- Execution plan

**Historical reference** - superseded by Phase-2-Captain-Implementation.md

## Supporting Documentation

| Document | Purpose |
|----------|---------|
| **[next_plan.md](./next_plan.md)** | Development roadmap |
| **[price_viz.md](./price_viz.md)** | Visualization notes |

## Navigation Guide

### For Implementation
1. Start with: **[Phase-2-Summary.md](./Phase-2-Summary.md)** (quick overview)
2. Detailed reference: **[Phase-2-Captain-Implementation.md](./Phase-2-Captain-Implementation.md)** (full guide)
3. Historical context: **[Phase-2.md](./Phase-2.md)** (original notes)

### For Understanding
- **Why 12 baskets?** → Phase-2-Captain-Implementation.md § 2.1
- **Why two parsers?** → Phase-2-Captain-Implementation.md § 3
- **Why Lake mode intraday-only?** → Phase-2-Captain-Implementation.md § 6.1
- **Regime logic details** → Phase-2-Captain-Implementation.md § 5
- **Risk management design** → Phase-2-Captain-Implementation.md § 4

### For Troubleshooting
- **basket.price = 0** → Phase-2-Captain-Implementation.md § 12.1
- **No signals generated** → Phase-2-Captain-Implementation.md § 12.1
- **Lake not exiting at 14:55** → Phase-2-Captain-Implementation.md § 12.1
- **Non-deterministic results** → Phase-2-Captain-Implementation.md § 12.1

### For Testing
- **Testing workflow** → Phase-2-Captain-Implementation.md § 9
- **Success criteria** → Phase-2-Captain-Implementation.md § 10
- **Expected performance** → Phase-2-Captain-Implementation.md § 11

## Project Structure

```
TrinityStrategy/
├── docs/                               # This directory
│   ├── README.md                       # This file
│   ├── Phase-2-Captain-Implementation.md  # Main Phase-2 guide (68KB)
│   ├── Phase-2-Summary.md             # Quick reference (5KB)
│   └── Phase-2.md                     # Original design notes (9KB)
├── wos/                                # WOS framework documentation
│   ├── 08-tier2-composite.md          # Composite strategy guide
│   └── ...                            # Other WOS docs
├── TrinityStrategy.py                  # Phase-1 implementation (Scouts)
├── trinity_parameters.json             # Tuning results (12 commodities)
├── CLAUDE.md                          # Phase-1 documentation
└── [Phase-2 files to be created]      # WOS_CaptainStrategy.py, etc.
```

## Key Concepts

### Trinity Strategy Three-Tier Architecture

```
Tier-1 (Scouts) → Tier-2 (Captain) → Tier-3 (Execution)
     ↓                  ↓                  ↓
  Indicators      Decision Logic        Orders
     ↓                  ↓                  ↓
  TrinityStrategy  WOS_CaptainStrategy  (Future)
```

### The Captain's Playbook Analogy

Just as a cricket captain adapts strategy based on pitch conditions:

| Pitch Type | Market Regime | ADX | Strategy | Hold Overnight? |
|------------|---------------|-----|----------|-----------------|
| **Flat Pitch** | Strong trend | > 39-43 | Trend-following (River) | YES |
| **Tricky Pitch** | Ranging/choppy | < 25-27 | Mean-reversion (Lake) | NO (intraday only) |
| **Uncertain** | Transition | Between | Hold (Dead Zone) | N/A |

### Risk Management Layers

```
Layer 1: Position Sizing (Always active)
   → Volatility-based: Gold 5.38×, Copper 0.026×

Layer 2: Per-Basket DD Limit (15%)
   → If basket hits 15% drawdown → Close basket only

Layer 3: Portfolio DD Limit (20%)
   → If portfolio hits 20% drawdown → Close ALL baskets, risk-off mode
```

## Quick Start for Phase-2

1. **Read**: [Phase-2-Summary.md](./Phase-2-Summary.md) (5 minutes)
2. **Study**: [Phase-2-Captain-Implementation.md](./Phase-2-Captain-Implementation.md) § 1-8 (30 minutes)
3. **Create**: `trinity_playbook.py` using tuning results
4. **Implement**: `WOS_CaptainStrategy.py` following § 8 architecture
5. **Test**: Quick test (7 days) following § 9 workflow
6. **Validate**: Visual validation with Jupyter notebook
7. **Backtest**: Full year (2024) for performance metrics
8. **Verify**: Replay consistency test

## Resources

### Framework Documentation
- **WOS Tier-2 Guide**: `/workspaces/money-engineering/TrinityStrategy/wos/08-tier2-composite.md`
- **Composite Strategy Base**: `/home/wolverine/bin/running/composite_strategyc3.py`
- **Strategy Base**: `/home/wolverine/bin/running/strategyc3.py`

### Trinity Strategy Docs
- **Phase-1 Guide**: `/workspaces/money-engineering/TrinityStrategy/CLAUDE.md`
- **Design Spec**: `/workspaces/money-engineering/TrinityStrategy/trinity_strategy.md`
- **Tuning Results**: `/workspaces/money-engineering/TrinityStrategy/trinity_parameters.json`

### Testing Tools
- **Backtest Script**: `/home/wolverine/bin/running/calculator3_test.py`
- **Launch Configs**: `/workspaces/money-engineering/TrinityStrategy/.vscode/launch.json`

## Status Summary

| Phase | Component | Status | Documentation | Testing |
|-------|-----------|--------|---------------|---------|
| **Phase-1** | Scout Indicators | ✅ Complete | CLAUDE.md | ✅ Validated |
| **Phase-2** | Captain Strategy | 🔄 In Progress | This directory | ⏳ Pending |
| **Phase-3** | Execution | ⏳ Future | N/A | ⏳ Pending |

## Change Log

### 2025-11-13
- Created comprehensive Phase-2-Captain-Implementation.md (68KB, 2,153 lines)
- Created Phase-2-Summary.md quick reference
- Created this README.md for navigation
- Documented all Phase-2 implementation details
- Covered all requested topics (12 baskets, risk management, regime logic, troubleshooting)

### 2025-11-12
- Completed Phase-1 tuning for all 12 commodities
- Generated trinity_parameters.json
- Created initial Phase-2.md design notes

### 2025-11-10
- Implemented and validated Phase-1 Scout indicators
- Completed CLAUDE.md documentation

---

**Questions?** Start with Phase-2-Summary.md, then dive into Phase-2-Captain-Implementation.md for details.

**Ready to implement?** Follow the checklist in Phase-2-Summary.md.

**Need help?** Check the Troubleshooting section (Phase-2-Captain-Implementation.md § 12).
