# IronOreIndicator - Quick Start Guide

## ✅ What's Ready

Your indicator system is now fully implemented and ready to run:

### 📁 Files

```
IronOreIndicator/
├── IronOreIndicator.py          ✅ Complete indicator implementation
├── uin.json                     ✅ Input configuration
├── uout.json                    ✅ Output configuration
├── test_resuming_mode.py        ✅ Replay consistency test
├── analysis.ipynb               ✅ P&L visualization notebook
├── .vscode/launch.json          ✅ VS Code debug configurations
├── .env                         ✅ Environment variables
├── REQUIREMENTS.md              📋 Complete specification
└── wos/                         📚 Framework documentation
```

---

## 🚀 How to Run

### Step 1: Run Backtest with Debugger

**In VS Code:**

1. **Open** the project folder: `IronOreIndicator/`
2. **Press** `F5` or click Run → Start Debugging
3. **Select** from dropdown:
   - **"IronOre - Quick Test (7 days)"** ← Start here (2-3 min)
   - **"IronOre - Full Backtest (3 months)"** ← For P&L analysis (5-10 min)

**What happens:**
- Connects to svr3 server
- Processes market data for DCE/i<00>
- Calculates EMA, RSI, volume indicators
- Generates buy/sell signals
- Saves results to svr3

**Expected output:**
```
IronOreIndicator initialized
IronOreIndicator ready
Initialized: close=XXX.XX, volume=XXX.XX
Bar 10: Signal=1, Confidence=0.XXX, RSI=XX.XX, ...
Bar 25: Signal=-1, Confidence=0.XXX, RSI=XX.XX, ...
...
Processing complete
```

### Step 2: Run Replay Consistency Test (OPTIONAL but RECOMMENDED)

**In VS Code:**

1. **Press** `F5`
2. **Select** "IronOre - Replay Consistency Test"

**Or command line:**
```bash
cd /workspaces/money-engineering/IronOreIndicator/
python test_resuming_mode.py
```

**Pass Criteria:**
- ✅ All runs complete successfully
- ✅ No errors in logs
- ✅ Deterministic output (stateless design)

### Step 3: Run Analysis Notebook

**After backtest completes:**

```bash
cd /workspaces/money-engineering/IronOreIndicator/
jupyter notebook analysis.ipynb
```

**In Jupyter:**
1. **Select kernel**: "Python 3 (IronOre)" (top-right)
2. **Run all cells**: Cell → Run All
3. **View results**:
   - Performance metrics table
   - 4-panel P&L visualization
   - Monthly breakdown
   - Signal analysis

**Expected outputs:**
- P&L curve
- Win rate, Sharpe ratio, max drawdown
- Trade distribution
- Signal confidence analysis

---

## 🎯 Indicator Strategy

**Multi-Indicator Confirmation:**

1. **EMA Crossover** (Trend Detection)
   - Fast EMA: 10 periods
   - Slow EMA: 20 periods
   - Uptrend: Fast > Slow
   - Downtrend: Fast < Slow

2. **RSI** (Mean Reversion)
   - Period: 14
   - Oversold: < 30
   - Overbought: > 70

3. **Volume Confirmation**
   - Volume EMA: 20 periods
   - Threshold: 1.2× average

**Signal Generation:**
- **BUY (signal=1)**: Uptrend + Oversold + High Volume
- **SELL (signal=-1)**: Downtrend + Overbought + High Volume
- **NEUTRAL (signal=0)**: Otherwise

**Confidence Calculation:**
- Buy: `confidence = (30 - RSI) / 30`
- Sell: `confidence = (RSI - 70) / 30`

---

## 🐛 Debugging Tips

### Set Breakpoints

1. **In `IronOreIndicator.py`**:
   - Line 163: `_on_cycle_pass()` - Check calculations
   - Line 258: `_generate_signal()` - Check signal logic
   - Line 226: Signal logging - See when signals fire

2. **Run with debugger** (F5)
3. **Step through code** (F10 = step over, F11 = step into)
4. **Inspect variables** in Debug panel

### Common Issues

**Issue: No signals generated**
- Check RSI thresholds (< 30 or > 70)
- Check volume multiplier (1.2x)
- Check EMA crossover direction
- Add logging to see values

**Issue: Memory growth**
- All algorithms use O(1) memory
- No unbounded lists
- Check with long backtest

**Issue: Non-deterministic results**
- No random() calls
- No time.time() usage
- No external state
- Run replay test to verify

---

## 📊 Performance Targets

From REQUIREMENTS.md Section 8.2:

- [ ] **Sharpe Ratio** > 1.0
- [ ] **Win Rate** > 50%
- [ ] **Profit Factor** > 1.5
- [ ] **Max Drawdown** < 20%
- [ ] **Total P&L** > 0 (for 3-month period)

---

## 🔧 Parameter Tuning

If performance targets not met, adjust in `IronOreIndicator.py`:

```python
# Line 99-102: EMA periods
self.alpha_fast = 2.0 / 11.0    # Try: 8-15 periods
self.alpha_slow = 2.0 / 21.0    # Try: 15-30 periods

# Line 101: RSI period
self.alpha_rsi = 2.0 / 15.0     # Try: 10-20 periods

# Line 105: Volume threshold
self.volume_multiplier = 1.2    # Try: 1.1-1.5

# Line 275-276: RSI thresholds
oversold = self.rsi < 30.0      # Try: 20-35
overbought = self.rsi > 70.0    # Try: 65-80
```

After changes:
1. Re-run backtest
2. Re-run notebook
3. Compare metrics

---

## 📝 Next Steps

1. ✅ **Run quick test** (7 days) to verify indicator works
2. ✅ **Check logs** for signal generation
3. ✅ **Run replay test** to verify stateless design
4. ✅ **Run full backtest** (3 months) for P&L analysis
5. ✅ **Run notebook** to generate P&L curve
6. ✅ **Review metrics** against acceptance criteria
7. 🎯 **Tune parameters** if needed (repeat 4-6)
8. 🚀 **Deploy** when targets met

---

## 📚 Documentation

- **REQUIREMENTS.md** - Complete specification
- **CLAUDE.md** - Development notes
- **README.md** - Project overview
- **wos/** - Framework documentation (12 chapters)

---

## ⚡ Quick Commands

```bash
# Run quick test
F5 → "IronOre - Quick Test (7 days)"

# Run full backtest
F5 → "IronOre - Full Backtest (3 months)"

# Run replay test
F5 → "IronOre - Replay Consistency Test"

# Run analysis
jupyter notebook analysis.ipynb
```

---

**You're all set! Press F5 to start debugging.** 🎉
