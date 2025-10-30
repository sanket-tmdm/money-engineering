# Chapter 12: Complete Example Project

**Learning objectives:**
- Build a complete trading system from scratch
- Apply all learned concepts
- Follow best practices throughout
- Deploy to production
- Monitor and maintain

**Previous:** [11 - Fine-tune and Iterate](11-fine-tune-and-iterate.md)

---

## Overview

This chapter walks through building a complete 3-tier trading system from idea to production deployment.

## Project: Mean Reversion System

### Strategy Concept

Trade mean reversion in commodity futures:
- **Tier 1**: RSI-based mean reversion indicator
- **Tier 2**: Portfolio manager for multiple commodities
- **Tier 3**: Execution with risk management

### Phase 1: Tier 1 Indicator

**File**: `MeanReversionIndicator.py`

```python
#!/usr/bin/env python3
"""RSI Mean Reversion Indicator"""

import math
from collections import deque
import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3

# Globals
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

class SampleQuote(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.open = self.high = self.low = self.close = None
        self.volume = self.turnover = None

class MeanReversionIndicator(pcts3.sv_object):
    """RSI-based mean reversion indicator."""

    def __init__(self, commodity, market):
        super().__init__()
        self.meta_name = "MeanReversion"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900
        self.market = market
        self.code = commodity + b'<00>'

        # RSI calculation
        self.rsi = 50.0
        self.gain_ema = 0.0
        self.loss_ema = 0.0
        self.alpha = 2.0 / 15.0  # 14-period RSI

        # State
        self.bar_index = 0
        self.timetag = None
        self.prev_close = 0.0
        self.signal = 0
        self.confidence = 0.0
        self.initialized = False

        # Data parser
        self.quote = SampleQuote()
        self.persistent = True

    def initialize(self, imports, metas):
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)
        self.quote.load_def_from_dict(metas)
        self.quote.set_global_imports(imports)

    def on_bar(self, bar: pc.StructValue):
        market = bar.get_market()
        code = bar.get_stock_code()

        if not (market == self.market and 
                code.startswith(self.code[:-4]) and
                code.endswith(b'<00>')):
            return []

        if bar.get_namespace() == self.quote.namespace and \
           bar.get_meta_id() == self.quote.meta_id:
            self.quote.market = market
            self.quote.code = code
            self.quote.granularity = bar.get_granularity()
            self.quote.from_sv(bar)
        else:
            return []

        tm = bar.get_time_tag()

        if self.timetag is None:
            self.timetag = tm

        if self.timetag < tm:
            self._on_cycle_pass()

            results = []
            if self.bar_index > 0 and self.initialized:
                results.append(self.copy_to_sv())

            self.timetag = tm
            self.bar_index += 1
            return results

        return []

    def _on_cycle_pass(self):
        close = float(self.quote.close)

        if not self.initialized:
            self.prev_close = close
            self.initialized = True
            return

        # Calculate RSI
        change = close - self.prev_close
        gain = max(change, 0)
        loss = max(-change, 0)

        self.gain_ema = self.alpha * gain + (1 - self.alpha) * self.gain_ema
        self.loss_ema = self.alpha * loss + (1 - self.alpha) * self.loss_ema

        if self.loss_ema > 0:
            rs = self.gain_ema / self.loss_ema
            self.rsi = 100 - (100 / (1 + rs))
        else:
            self.rsi = 100

        # Generate mean reversion signal
        if self.rsi < 30:
            self.signal = 1  # Oversold - buy
            self.confidence = (30 - self.rsi) / 30
        elif self.rsi > 70:
            self.signal = -1  # Overbought - sell
            self.confidence = (self.rsi - 70) / 30
        else:
            self.signal = 0
            self.confidence = 0.0

        self.prev_close = close

# Manager for multiple commodities
class IndicatorManager:
    def __init__(self):
        self.indicators = {}
        commodities = {
            b'SHFE': [b'cu', b'al', b'zn'],
            b'DCE': [b'i', b'j']
        }

        for market, codes in commodities.items():
            for code in codes:
                key = (market, code)
                self.indicators[key] = MeanReversionIndicator(code, market)

    def initialize(self, imports, metas):
        for indicator in self.indicators.values():
            indicator.initialize(imports, metas)

    def on_bar(self, bar):
        results = []
        for indicator in self.indicators.values():
            results.extend(indicator.on_bar(bar))
        return results

manager = IndicatorManager()

async def on_init():
    global manager, imports, metas, worker_no
    if worker_no != 0 and metas and imports:
        manager.initialize(imports, metas)

async def on_ready():
    pass

async def on_bar(bar):
    global manager, worker_no
    if worker_no != 1:
        return []
    return manager.on_bar(bar)

# Other callbacks...
async def on_market_open(market, tradeday, time_tag, time_string):
    pass
async def on_market_close(market, tradeday, timetag, timestring):
    pass
async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    pass
async def on_tradeday_end(market, tradeday, timetag, timestring):
    pass
async def on_reference(market, tradeday, data, timetag, timestring):
    pass
async def on_historical(params, records):
    pass
```

### Phase 2: Test and Validate

```bash
# Quick test
python calculator3_test.py --testcase ./ --algoname MeanReversion \
    --sourcefile MeanReversionIndicator.py \
    --start 20250703000000 --end 20250710000000 \
    --granularity 900 --category 1

# Replay consistency
python test_resuming_mode.py

# Full backtest
python calculator3_test.py --testcase ./ --algoname MeanReversion \
    --sourcefile MeanReversionIndicator.py \
    --start 20230101000000 --end 20250925000000 \
    --granularity 900 --category 1
```

### Phase 3: Visualize and Optimize

```python
# Create visualization script
import svr3
import pandas as pd
import matplotlib.pyplot as plt

def analyze_indicator():
    client = svr3.Client("10.99.100.116", 8080, "TOKEN")
    data = client.fetch(
        namespace="private",
        strategy="MeanReversion",
        market="SHFE",
        code="cu<00>",
        granularity=900,
        start="20250701000000",
        end="20250710000000"
    )

    df = pd.DataFrame(data)

    # Plot RSI and signals
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    ax1.plot(df['timestamp'], df['rsi'])
    ax1.axhline(y=30, color='g', linestyle='--')
    ax1.axhline(y=70, color='r', linestyle='--')
    ax1.set_title('RSI')

    ax2.scatter(df['timestamp'], df['signal'], c=df['signal'], cmap='RdYlGn')
    ax2.set_title('Signals')

    plt.savefig('analysis.png')

analyze_indicator()
```

### Phase 4: Tier 2 Composite

Build portfolio manager (see Chapter 8 for template).

### Phase 5: Production Deployment

```bash
# Final checks
1. Replay consistency test passes
2. Full backtest performance acceptable  
3. Code review completed
4. Risk parameters validated
5. Monitoring set up

# Deploy
Deploy to production server
Enable monitoring and alerts
Start with small capital
Monitor closely for first week
Gradually increase allocation
```

## Summary

Complete workflow:
1. Design Tier 1 indicator
2. Implement with all best practices
3. Test (quick, replay, full backtest)
4. Visualize and optimize
5. Build Tier 2 composite
6. Build Tier 3 executor (if live trading)
7. Validate thoroughly
8. Deploy to production
9. Monitor and maintain

**Congratulations!** You've learned the complete Wolverine framework for building production trading systems.

---

**Previous:** [11 - Fine-tune and Iterate](11-fine-tune-and-iterate.md) | **Return to:** [01 - Overview](01-overview.md)
