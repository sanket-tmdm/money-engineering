# Iron Ore Tier-1 Indicator System Guide

**Document**: IRON_ORE_INDICATOR_GUIDE.md
**Version**: 1.0
**Last Updated**: 2025-11-04
**Purpose**: Complete workflow for building a tier-1 indicator with buy/sell signals, backtesting, and P&L visualization
**Scope**: Iron ore (DCE/i<00>) following WOS framework patterns
**Framework Reference**: wos/ directory (12 chapters)

---

## Chapter 1: System Overview

### 1.1 Purpose

Build a production-ready tier-1 indicator for iron ore futures (DCE/i<00>) that:
- Generates buy/sell signals using technical analysis
- Backtests signals against 1 year of historical data
- Evaluates performance over recent 3 months
- Visualizes P&L curve and trading metrics

### 1.2 Architecture

```
┌────────────────────────────────────────────┐
│  Raw Market Data (SampleQuote)            │
│  - DCE/i<00> logical contract              │
│  - OHLCV at 15-minute granularity          │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Iron Ore Indicator (Tier 1)               │
│  - Multi-period EMA crossover              │
│  - RSI mean reversion                      │
│  - Volume confirmation                     │
│  - Signal strength calculation             │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Outputs                                   │
│  - signal: {-1, 0, 1}                      │
│  - confidence: [0.0, 1.0]                  │
│  - indicator values for analysis           │
└────────────────────────────────────────────┘
```

### 1.3 Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| 1. Setup | 30 min | Configure uin.json, uout.json, project structure |
| 2. Implementation | 2-3 hours | Write indicator logic following WOS patterns |
| 3. Testing | 1 hour | Quick test → Replay consistency → Full backtest |
| 4. Visualization | 1 hour | Create analysis scripts and generate P&L curves |
| 5. Optimization | Variable | Parameter tuning based on backtest results |

**Total**: ~4-6 hours for complete system

---

## Chapter 2: Project Setup

### 2.1 Directory Structure

```
IronOreIndicator/
├── IronOreIndicator.py      # Main indicator implementation
├── uin.json                  # Input configuration
├── uout.json                 # Output configuration
├── test_resuming_mode.py     # Replay consistency test
├── ironore_viz.py            # Visualization script
├── .devcontainer/            # VS Code dev container config
│   └── devcontainer.json
├── .vscode/                  # VS Code debug configurations
│   └── launch.json
├── CLAUDE.md                 # Development notes
└── README.md                 # Project documentation
```

### 2.2 Configuration Files

#### uin.json - Input Universe

**Purpose**: Define data sources and market scope

```json
{
  "global": {
    "imports": {
      "SampleQuote": {
        "fields": ["open", "high", "low", "close", "volume", "turnover"],
        "granularities": [900],
        "revision": 4294967295,
        "markets": ["DCE"],
        "security_categories": [[1, 2, 3]],
        "securities": [["i"]]
      }
    }
  }
}
```

**Key Points**:
- `granularities: [900]` = 15-minute bars
- `markets: ["DCE"]` = Dalian Commodity Exchange
- `securities: [["i"]]` = Iron ore (lowercase for DCE)
- `"turnover"` not `"amount"` for volume-weighted data

**Reference**: wos/02-uin-and-uout.md for configuration patterns

#### uout.json - Output Universe

**Purpose**: Define indicator output fields and types

```json
{
  "private": {
    "markets": ["DCE"],
    "security_categories": [[1, 2, 3]],
    "securities": [["i"]],
    "sample_granularities": {
      "type": "min",
      "cycles": [900],
      "cycle_lengths": [0]
    },
    "export": {
      "XXX": {
        "fields": [
          "_preserved_field",
          "bar_index",
          "ema_fast",
          "ema_slow",
          "rsi",
          "signal",
          "confidence"
        ],
        "defs": [
          {"field_type": "int64", "precision": 0, "display_name": "Preserved", "sample_type": 0, "multiple": 1},
          {"field_type": "integer", "precision": 0, "display_name": "Bar Index", "sample_type": 0, "multiple": 1},
          {"field_type": "double", "precision": 6, "display_name": "EMA Fast", "sample_type": 0, "multiple": 1},
          {"field_type": "double", "precision": 6, "display_name": "EMA Slow", "sample_type": 0, "multiple": 1},
          {"field_type": "double", "precision": 6, "display_name": "RSI", "sample_type": 0, "multiple": 1},
          {"field_type": "integer", "precision": 0, "display_name": "Signal", "sample_type": 0, "multiple": 1},
          {"field_type": "double", "precision": 6, "display_name": "Confidence", "sample_type": 0, "multiple": 1}
        ],
        "revision": -1
      }
    }
  }
}
```

**Critical Requirements**:
1. `"_preserved_field"` MUST be first field with type int64
2. Export name MUST be `"XXX"` (framework replaces)
3. Array lengths must match: markets, security_categories, securities
4. Field names must match Python class attributes exactly

**Reference**: wos/02-uin-and-uout.md, lines 209-319

---

## Chapter 3: Indicator Implementation

### 3.1 Core Algorithm

**Strategy**: EMA crossover + RSI mean reversion + Volume confirmation

**Pseudocode**:
```
1. Calculate EMAs (fast=10, slow=20 periods)
2. Calculate RSI (14-period)
3. Calculate volume moving average
4. Generate signal:
   If (EMA_fast > EMA_slow) AND (RSI < 30) AND (volume > avg_volume):
      signal = 1 (BUY), confidence = (30 - RSI) / 30
   Elif (EMA_fast < EMA_slow) AND (RSI > 70) AND (volume > avg_volume):
      signal = -1 (SELL), confidence = (RSI - 70) / 30
   Else:
      signal = 0 (NEUTRAL), confidence = 0.0
5. Output results at cycle boundary
```

**Design Principles** (WOS Framework):
1. **Stateless**: Use online algorithms (EMA, Welford's variance)
2. **Bounded memory**: Fixed-size deques for recent data
3. **Deterministic**: No random, time-based, or external state
4. **Replay consistent**: from_sv() inverse of copy_to_sv()

**Reference**: wos/05-stateless-design.md for online algorithms

### 3.2 Module Structure

**File**: IronOreIndicator.py

**Required Components**:
1. Framework globals (use_raw, overwrite, granularity, etc.)
2. SampleQuote parser class (sv_object)
3. IronOreIndicator class (sv_object)
4. Framework callbacks (on_init, on_bar, etc.)

**Pattern**:
```python
# Framework globals (REQUIRED)
use_raw = True
overwrite = False
granularity = 900
schema = None
max_workers = 1
worker_no = None
exports = {}
imports = {}
metas = {}
logger = pcu3.vanilla_logger()

# SampleQuote parser
class SampleQuote(pcts3.sv_object):
    # ... (parse OHLCV data)

# Main indicator
class IronOreIndicator(pcts3.sv_object):
    # ... (indicator logic)

# Framework callbacks
async def on_init():
    # ... (initialize with metas/imports)
async def on_bar(bar):
    # ... (process bars, return list)
```

**Reference**: wos/03-programming-basics-and-cli.md, lines 91-176

### 3.3 State Management

**Instance Variables** (automatically persisted):
```python
# Metadata (constants - set once)
self.meta_name = "IronOreIndicator"
self.namespace = pc.namespace_private
self.revision = (1 << 32) - 1
self.granularity = 900
self.market = b'DCE'
self.code = b'i<00>'

# State (automatically persisted)
self.bar_index = 0
self.timetag = None
self.ema_fast = 0.0
self.ema_slow = 0.0
self.rsi = 50.0
self.gain_ema = 0.0
self.loss_ema = 0.0
self.volume_ema = 0.0
self.signal = 0
self.confidence = 0.0
self.prev_close = 0.0
self.initialized = False
```

**Online Algorithm Parameters**:
```python
self.alpha_fast = 2.0 / 11.0   # 10-period EMA
self.alpha_slow = 2.0 / 21.0   # 20-period EMA
self.alpha_rsi = 2.0 / 15.0    # 14-period RSI
self.alpha_vol = 2.0 / 21.0    # 20-period volume EMA
```

**Reference**: wos/04-structvalue-and-sv_object.md, wos/05-stateless-design.md

### 3.4 Cycle Boundary Handling

**Pattern**:
```python
def on_bar(self, bar: pc.StructValue):
    # 1. Filter for correct instrument
    if not (bar.get_market() == self.market and
            bar.get_stock_code().endswith(b'<00>')):
        return []

    # 2. Parse data
    # ... (parse SampleQuote)

    tm = bar.get_time_tag()

    # 3. Initialize timetag
    if self.timetag is None:
        self.timetag = tm

    # 4. Handle cycle boundary
    if self.timetag < tm:
        self._on_cycle_pass()  # Process end of cycle

        results = []
        if self.bar_index > 0 and self.initialized:
            results.append(self.copy_to_sv())  # Serialize output

        self.timetag = tm
        self.bar_index += 1
        return results  # ALWAYS return list

    return []
```

**Reference**: wos/07-tier1-indicator.md, lines 419-449

### 3.5 Signal Generation Logic

**Function**: `_on_cycle_pass()`

**Implementation Steps**:
1. Extract OHLCV from parsed quote
2. Update online EMAs (fast, slow)
3. Update RSI using online algorithm
4. Update volume EMA
5. Generate signal and confidence
6. Update prev_close for next cycle

**EMA Update** (online):
```python
self.ema_fast = self.alpha_fast * close + (1 - self.alpha_fast) * self.ema_fast
self.ema_slow = self.alpha_slow * close + (1 - self.alpha_slow) * self.ema_slow
```

**RSI Calculation** (online):
```python
change = close - self.prev_close
gain = max(change, 0)
loss = max(-change, 0)

self.gain_ema = self.alpha_rsi * gain + (1 - self.alpha_rsi) * self.gain_ema
self.loss_ema = self.alpha_rsi * loss + (1 - self.alpha_rsi) * self.loss_ema

rs = self.gain_ema / self.loss_ema if self.loss_ema > 0 else 999
self.rsi = 100 - (100 / (1 + rs))
```

**Signal Logic**:
```python
# Buy signal: Uptrend + Oversold + High volume
if (self.ema_fast > self.ema_slow and
    self.rsi < 30 and
    volume > self.volume_ema * 1.2):
    self.signal = 1
    self.confidence = (30 - self.rsi) / 30

# Sell signal: Downtrend + Overbought + High volume
elif (self.ema_fast < self.ema_slow and
      self.rsi > 70 and
      volume > self.volume_ema * 1.2):
    self.signal = -1
    self.confidence = (self.rsi - 70) / 30

else:
    self.signal = 0
    self.confidence = 0.0
```

**Reference**: wos/05-stateless-design.md (online algorithms), wos/07-tier1-indicator.md

---

## Chapter 4: Testing and Validation

### 4.1 Quick Test (7-Day)

**Purpose**: Fast iteration during development

**Command**:
```bash
python /home/wolverine/bin/running/calculator3_test.py \
    --testcase ${PWD}/ \
    --algoname IronOreIndicator \
    --sourcefile IronOreIndicator.py \
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

**Expected Output**:
- Indicator processes bars for DCE/i<00>
- Logs show signal generation
- Output files created in framework directory

**Debug**: Use VS Code launch.json configuration (see templates/)

**Reference**: wos/06-backtest.md, lines 18-38

### 4.2 Replay Consistency Test (MANDATORY)

**Purpose**: Verify stateless design and deterministic computation

**Command**:
```bash
python test_resuming_mode.py \
    --start 20241025000000 \
    --end 20241101000000 \
    --midpoint 20241028120000
```

**Test Logic**:
1. Run A: Process bars 0-end continuously
2. Run B: Process bars 0-midpoint, stop, resume, process midpoint-end
3. Compare outputs: MUST be identical

**Pass Criteria**:
- All output fields match exactly
- State consistency verified
- No divergence after midpoint

**If Fails**:
- Check for non-deterministic code (random, time-based)
- Verify all state persisted (no local variables)
- Ensure from_sv() inverse of copy_to_sv()

**Reference**: wos/06-backtest.md, lines 74-100; wos/05-stateless-design.md

### 4.3 Full Backtest (1 Year)

**Purpose**: Comprehensive validation across market conditions

**Time Range**: 2024-01-01 to 2024-12-31 (1 year of data)

**Command**:
```bash
python /home/wolverine/bin/running/calculator3_test.py \
    --testcase ${PWD}/ \
    --algoname IronOreIndicator \
    --sourcefile IronOreIndicator.py \
    --start 20240101000000 \
    --end 20241231235959 \
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

**Expected Results**:
- ~24,000 bars processed (15-min bars × 365 days)
- Signal count: 500-2000 signals (varies by parameters)
- Memory: Bounded (O(1) growth)
- Duration: 5-15 minutes

**Reference**: wos/06-backtest.md, lines 46-72

---

## Chapter 5: P&L Calculation and Backtesting

### 5.1 Backtesting Logic

**Time Range for P&L**: Recent 3 months (2024-10-01 to 2024-12-31)

**Backtesting Algorithm**:
```
1. Load indicator outputs for 3-month period
2. For each signal:
   a. Entry: signal ≠ 0 AND confidence > threshold
   b. Position: direction = signal, size = base_size × confidence
   c. Exit: signal reverses OR confidence drops
3. For each position:
   a. Entry price: close at signal bar
   b. Exit price: close at exit bar
   c. PnL = (exit_price - entry_price) × direction × size
4. Cumulative PnL curve: sum(PnL[0:i]) for i in range(len(positions))
```

**Assumptions**:
- Base position size: 1 contract
- No slippage or commissions (add later for realism)
- Instant fills at close prices
- No overnight holding restrictions

**Reference**: IronOreIndicator/ironoreindicator_viz.py for implementation

### 5.2 Performance Metrics

**Calculate**:
1. **Total PnL**: Sum of all position PnLs
2. **Win Rate**: Wins / Total Trades
3. **Average Win**: Mean of winning trades
4. **Average Loss**: Mean of losing trades
5. **Sharpe Ratio**: (Mean Returns) / (Std Returns) × √252
6. **Max Drawdown**: Max(Peak - Trough) over period

**Formula Table**:

| Metric | Formula | Target |
|--------|---------|--------|
| Total PnL | Σ(PnL_i) | > 0 |
| Win Rate | Wins / Total | > 0.50 |
| Profit Factor | Total Wins / Total Losses | > 1.5 |
| Sharpe Ratio | μ / σ × √252 | > 1.0 |
| Max Drawdown | Max(Peak - Trough) / Peak | < 0.20 |

---

## Chapter 6: Visualization

### 6.1 Data Fetching

**Purpose**: Retrieve indicator outputs from svr3 server

**Function**: `fetch_indicator_data()`

**Connection Sequence** (CRITICAL ORDER):
```python
1. reader = svr3.sv_reader(start, end, algoname, granularity, namespace, ...)
2. reader.token = TOKEN
3. await reader.login()
4. await reader.connect()
5. reader.ws_task = asyncio.create_task(reader.ws_loop())
6. await reader.shakehand()
7. ret = await reader.save_by_symbol()
8. data = ret[1][1]
```

**Configuration**:
```python
SVR_HOST = os.getenv("SVR_HOST", "10.99.100.116")
TOKEN = os.getenv("SVR_TOKEN")
RAILS_URL = f"https://{SVR_HOST}:4433/private-api/"
WS_URL = f"wss://{SVR_HOST}:4433/tm"  # Note: /tm not /ws
TM_MASTER = (SVR_HOST, 6102)  # Tuple format
NAMESPACE = "private"  # For custom indicators
```

**Time Format**: Integer YYYYMMDDHHMMSS
- Start: `20241001000000` (Oct 1, 2024)
- End: `20241231235959` (Dec 31, 2024)

**Reference**: wos/10-visualization.md, lines 76-192

### 6.2 P&L Curve Visualization

**Plot Components**:
1. **Cumulative P&L**: Line plot of cumulative returns
2. **Signal Overlay**: Scatter plot of buy/sell signals
3. **Drawdown**: Area plot of peak-to-trough drawdown
4. **Distribution**: Histogram of individual trade P&Ls

**Code Template**:
```python
def plot_pnl_curve(df, trades):
    fig, axes = plt.subplots(4, 1, figsize=(15, 12))

    # Plot 1: Cumulative P&L
    axes[0].plot(df['timestamp'], df['cumulative_pnl'])
    axes[0].set_title('Cumulative P&L')
    axes[0].set_ylabel('P&L (CNY)')
    axes[0].grid(True)

    # Plot 2: Buy/Sell Signals
    buy_signals = df[df['signal'] == 1]
    sell_signals = df[df['signal'] == -1]
    axes[1].scatter(buy_signals['timestamp'], buy_signals['close'],
                   color='green', label='Buy', marker='^')
    axes[1].scatter(sell_signals['timestamp'], sell_signals['close'],
                   color='red', label='Sell', marker='v')
    axes[1].plot(df['timestamp'], df['close'], alpha=0.5)
    axes[1].set_title('Price and Signals')
    axes[1].legend()
    axes[1].grid(True)

    # Plot 3: Drawdown
    axes[2].fill_between(df['timestamp'], 0, df['drawdown'],
                        color='red', alpha=0.3)
    axes[2].set_title('Drawdown')
    axes[2].set_ylabel('Drawdown %')
    axes[2].grid(True)

    # Plot 4: Trade P&L Distribution
    axes[3].hist(trades['pnl'], bins=50, edgecolor='black')
    axes[3].set_title('Trade P&L Distribution')
    axes[3].set_xlabel('P&L (CNY)')
    axes[3].set_ylabel('Count')
    axes[3].grid(True)

    plt.tight_layout()
    plt.savefig('pnl_analysis.png', dpi=150)
```

**Reference**: wos/10-visualization.md, templates/indicator_viz.py.template

### 6.3 Performance Summary

**Generate Table**:
```python
def print_performance_summary(metrics):
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2%}")
    print(f"Total P&L: ¥{metrics['total_pnl']:,.2f}")
    print(f"Avg Win: ¥{metrics['avg_win']:,.2f}")
    print(f"Avg Loss: ¥{metrics['avg_loss']:,.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print("="*60)
```

**Output to File**: performance_summary.txt

---

## Chapter 7: Complete Workflow

### 7.1 Step-by-Step Execution

**Phase 1: Setup** (30 minutes)
```bash
# 1. Create project directory
mkdir IronOreIndicator && cd IronOreIndicator

# 2. Create configuration files
# - uin.json (copy from Chapter 2.2)
# - uout.json (copy from Chapter 2.2)

# 3. Create .env file with credentials
cat > .env << EOF
SVR_HOST=10.99.100.116
SVR_TOKEN=your_token_here
EOF
```

**Phase 2: Implementation** (2-3 hours)
```bash
# 1. Create IronOreIndicator.py
# - Follow Chapter 3 patterns
# - Implement online algorithms
# - Handle cycle boundaries correctly

# 2. Create test_resuming_mode.py
# - Copy from templates/test_resuming_mode.py.template

# 3. Create VS Code configurations
# - .vscode/launch.json (copy from templates/)
```

**Phase 3: Testing** (1 hour)
```bash
# 1. Quick test (7-day)
python calculator3_test.py --start 20241025000000 --end 20241101000000 ...

# 2. Replay consistency test (MANDATORY)
python test_resuming_mode.py

# 3. Full backtest (1 year)
python calculator3_test.py --start 20240101000000 --end 20241231235959 ...
```

**Phase 4: Visualization** (1 hour)
```bash
# 1. Create visualization script
# - ironore_viz.py (copy from templates/indicator_viz.py.template)
# - Customize for iron ore specific analysis

# 2. Generate plots
python ironore_viz.py

# 3. Review outputs
# - pnl_analysis.png
# - performance_summary.txt
```

**Phase 5: Optimization** (variable)
```bash
# 1. Analyze results
# - Review Sharpe ratio, win rate, max drawdown
# - Identify parameter sensitivity

# 2. Tune parameters
# - Adjust EMA periods (fast, slow)
# - Adjust RSI thresholds (oversold, overbought)
# - Adjust confidence threshold

# 3. Re-test
# - Repeat Phase 3 with new parameters
# - Compare performance metrics
```

### 7.2 Success Criteria

**Indicator Ready for Production When**:
- [x] Replay consistency test passes
- [x] Full backtest completes without errors
- [x] Memory usage bounded (O(1) growth)
- [x] Sharpe ratio > 1.0
- [x] Win rate > 50%
- [x] Max drawdown < 20%
- [x] Code follows all WOS doctrines
- [x] Documentation complete (CLAUDE.md, README.md)

### 7.3 Common Issues and Solutions

**Issue 1: Replay Test Fails**

**Symptoms**: Different outputs after resume

**Solution**:
```python
# Check for:
1. Non-deterministic code (random, time-based)
2. Incomplete state persistence (local variables)
3. External dependencies (global state)
4. Asymmetric from_sv()/copy_to_sv()
```

**Issue 2: No Signals Generated**

**Symptoms**: Output shows signal=0 for all bars

**Solution**:
```python
# Check:
1. Threshold too restrictive (e.g., RSI < 10 instead of < 30)
2. Confidence calculation returns 0
3. Initialization not complete (self.initialized = False)
4. Volume filter too strict
```

**Issue 3: Memory Growth**

**Symptoms**: Memory increases during long backtest

**Solution**:
```python
# Use bounded collections:
from collections import deque
self.recent_prices = deque(maxlen=100)  # NOT []
```

**Reference**: wos/06-backtest.md, lines 214-293

---

## Chapter 8: File Templates and References

### 8.1 Quick Reference

**Template Files**:
- `templates/indicator.py.template` - Base indicator structure
- `templates/indicator_viz.py.template` - Visualization script
- `templates/test_resuming_mode.py.template` - Replay test
- `templates/launch.json.template` - VS Code debug config

**WOS Documentation**:
- `wos/01-overview.md` - Framework architecture
- `wos/02-uin-and-uout.md` - Configuration
- `wos/03-programming-basics-and-cli.md` - Base classes
- `wos/04-structvalue-and-sv_object.md` - Data serialization
- `wos/05-stateless-design.md` - Online algorithms
- `wos/06-backtest.md` - Testing procedures
- `wos/07-tier1-indicator.md` - Tier 1 patterns
- `wos/10-visualization.md` - Analysis and plotting

**Example Implementation**:
- `IronOreIndicator/IronOreIndicator.py` - Complete indicator
- `IronOreIndicator/ironoreindicator_viz.py` - Visualization script
- `IronOreIndicator/uin.json` - Input configuration
- `IronOreIndicator/uout.json` - Output configuration

### 8.2 Command Reference

**Quick Test**:
```bash
python calculator3_test.py \
  --testcase ${PWD}/ \
  --algoname IronOreIndicator \
  --sourcefile IronOreIndicator.py \
  --start 20241025000000 \
  --end 20241101000000 \
  --granularity 900 \
  --tm wss://10.99.100.116:4433/tm \
  --tm-master 10.99.100.116:6102 \
  --rails https://10.99.100.116:4433/private-api/ \
  --token ${SVR_TOKEN} \
  --category 1 \
  --is-managed 1 \
  --restore-length 864000000 \
  --multiproc 1
```

**Replay Test**:
```bash
python test_resuming_mode.py \
  --start 20241025000000 \
  --end 20241101000000 \
  --midpoint 20241028120000
```

**Full Backtest (1 Year)**:
```bash
# Change start to 20240101000000
# Change end to 20241231235959
```

---

## Summary

**Complete System in 8 Chapters**:

1. **System Overview** - Architecture and goals
2. **Project Setup** - Directory structure and configuration
3. **Indicator Implementation** - Core algorithm and WOS patterns
4. **Testing and Validation** - Quick test, replay consistency, full backtest
5. **P&L Calculation** - Backtesting logic and performance metrics
6. **Visualization** - Data fetching and plotting
7. **Complete Workflow** - Step-by-step execution guide
8. **File Templates** - Quick reference and commands

**Key Principles Applied**:
- ✅ Precise and concise documentation (REQUIREMENT_WRITING_GUIDE)
- ✅ Structured format (tables, lists, code blocks)
- ✅ References to WOS framework (single source of truth)
- ✅ Pseudocode for algorithms (not implementation)
- ✅ Complete workflow from setup to visualization
- ✅ Actionable guidance at every step

**Time to Production**: ~4-6 hours
**Documentation Density**: High (complete system in 8 concise chapters)
**Maintainability**: High (references WOS patterns, minimal duplication)

---

**Next Steps**: Execute Phase 1 (Setup) and begin implementation following Chapter 3 patterns.
