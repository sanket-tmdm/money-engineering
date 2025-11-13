# Phase-2 Captain Implementation - Quick Reference

## Overview
**Phase-2** implements the WOS_CaptainStrategy - a Tier-2 composite strategy that consumes Phase-1 Scout indicators and generates trading signals for 12 commodities.

## Key Documents
- **[Phase-2-Captain-Implementation.md](./Phase-2-Captain-Implementation.md)** - Complete 68KB implementation guide (2,153 lines)
- **[Phase-2.md](./Phase-2.md)** - Original design notes

## Quick Start Checklist

### Files to Create
- [ ] `WOS_CaptainStrategy.py` (~600 lines)
- [ ] `trinity_playbook.py` (~50 lines)
- [ ] `uin_captain.json` (~60 lines)
- [ ] `uout_captain.json` (~30 lines)
- [ ] `WOS_CaptainStrategy_viz.ipynb` (visualization)
- [ ] `.vscode/launch.json` (add Captain test configs)

### Implementation Steps
1. Create `trinity_playbook.py` from tuning results
2. Implement two parsers (SampleQuote, ScoutParser)
3. Initialize 12 baskets in `__init__()`
4. Implement `on_bar()` with routing logic
5. Implement `_on_cycle_pass()` with signal generation
6. Implement regime logic (River/Lake/Dead Zone)
7. Implement intraday exit logic (14:55 Lake mode)
8. Add MANDATORY callbacks (on_reference, on_tradeday_begin/end)
9. Add risk management (DD limits)
10. Test with Quick Test (7 days)

### Critical Components

**12-Basket Architecture**
- One basket per commodity
- Equal capital, volatility-weighted position sizing
- Independent regime detection per basket
- Isolated risk per basket

**Two-Parser Design**
- SampleQuote: Close price (from global namespace)
- ScoutParser: ADX, Bands, Conviction (from private namespace)
- Both needed for complete signal logic

**Three Regimes**
- **River** (ADX > 39-43): Trend-following, hold overnight
- **Lake** (ADX < 25-27): Mean-reversion, intraday only
- **Dead Zone** (between): Hold, avoid whipsaws

**Intraday Exit Rule**
- Lake mode MUST exit by 14:55
- Avoids overnight gap risk in ranging markets
- River mode holds overnight (trend persistence)

**Risk Management**
- Position sizing: Volatility-based (gold 5.38×, copper 0.026×)
- Per-basket DD: 15% limit
- Portfolio DD: 20% limit

### MANDATORY Callbacks

```python
async def on_reference(market, tradeday, data, timetag, timestring):
    """CRITICAL: Populates basket.target_instrument"""
    strategy.on_reference(bytes(market, 'utf-8'), tradeday, data)

async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    """Triggers contract rolling"""
    strategy.on_tradeday_begin(bytes(market, 'utf-8'), tradeday)

async def on_tradeday_end(market, tradeday, timetag, timestring):
    """EOD settlement"""
    strategy.on_tradeday_end(bytes(market, 'utf-8'), tradeday)
```

**Without these**: basket.target_instrument stays empty → no market data routing → trading fails

### Testing Sequence
1. **Quick Test** (7 days) - Verify implementation works
2. **Visual Validation** - Inspect signals via Jupyter notebook
3. **Full Backtest** (1 year) - Generate performance metrics
4. **Replay Consistency** - Ensure deterministic behavior

### Expected Performance
- Annual Return: 15-35% (target 25%)
- Sharpe Ratio: 1.5-2.5 (target 2.0)
- Max Drawdown: 8-15% (target 10%)
- Win Rate: 50-60% (target 55%)

## Common Issues

| Issue | Root Cause | Solution |
|-------|------------|----------|
| basket.price = 0 | on_reference() not implemented | Add callback forwarding |
| No signals | Missing data or thresholds too strict | Check uin.json, adjust thresholds |
| Lake not exiting | _is_near_eod() not triggering | Verify timetag format |
| Non-deterministic | State leakage or dict iteration | Clear cycle data, sort keys |

## Key Insights

### Why 12 Baskets?
- Different volatilities (cu: 1060 vs au: 5.1)
- Different regimes (simultaneous River/Lake/Dead)
- Independent contract rolling
- Isolated risk per commodity
- Risk parity capital allocation

### Why SampleQuote AND ScoutParser?
- Phase-1 doesn't export close price
- Need close for Bollinger Band comparison
- Scout outputs from private namespace
- SampleQuote from global namespace
- Two separate import sources required

### Why Lake Mode Intraday Only?
- Ranging markets have no directional bias
- Overnight gaps are random vs position
- Expected value = 0, but high variance
- Intraday mean-reversion has edge
- River mode holds overnight (trend persistence)

## Documentation Structure

The full guide covers:
1. Overview (architecture, goals, WOS positioning)
2. 12-Basket Architecture (why, how, allocation)
3. Data Sources (SampleQuote vs ScoutParser)
4. Risk Management (3-tier system)
5. Regime Logic (River/Lake/Dead Zone detailed)
6. Intraday Exit Logic (why 14:55, session handling)
7. File Structure (all new files)
8. Implementation Architecture (class design, parsers, callbacks)
9. Testing Workflow (4-stage process)
10. Success Criteria (functional + performance)
11. Expected Performance (per-regime, per-commodity)
12. Troubleshooting (common issues + solutions)

**Total**: 68KB, 2,153 lines, 12 sections with code examples

## Next Steps
1. Read full implementation guide
2. Create trinity_playbook.py
3. Start implementing WOS_CaptainStrategy.py
4. Follow testing workflow
5. Iterate based on results

**Good luck implementing Phase-2!**
