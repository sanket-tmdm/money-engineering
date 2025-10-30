# Chapter 5: Singularity (Stateless Design)

**Learning objectives:**
- Understand stateless design principles
- Implement strategies that can resume from any point
- Use online algorithms for bounded memory
- Achieve replay consistency
- Master state persistence patterns

**Previous:** [04 - StructValue and sv_object](04-structvalue-and-sv_object.md) | **Next:** [06 - Backtest and Testing](06-backtest.md)

---

## Overview

"Singularity" in Wolverine refers to the property that a strategy produces identical results regardless of when it's stopped and resumed. A strategy with proper singularity can be:

- Stopped at any bar
- Reloaded from persisted state
- Resume processing
- **Produce exactly the same outputs** as if it had never stopped

This chapter explains how to design stateless strategies that achieve perfect replay consistency.

## Why Singularity Matters

### The Problem Without Singularity

```python
# ❌ BAD - Depends on unbounded history
class BadStrategy(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        # Storing ALL historical data
        self.price_history = []  # Grows forever!

    def on_bar(self, bar):
        price = float(bar.close)
        self.price_history.append(price)

        # Calculate average of ALL prices
        avg = sum(self.price_history) / len(self.price_history)

        # Problem: After restart, price_history is empty!
        # Results will be different!
```

**Issues:**
1. **Memory grows unbounded** (will crash eventually)
2. **State too large** to persist efficiently
3. **Inconsistent results** after restart
4. **Cannot replay** from arbitrary points

### The Solution: Stateless Design

```python
# ✅ GOOD - Uses online algorithm
class GoodStrategy(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        # Only store current state
        self.ema = 0.0  # Exponential moving average
        self.alpha = 0.1  # Decay factor
        self.initialized = False

    def on_bar(self, bar):
        price = float(bar.close)

        # Initialize on first bar
        if not self.initialized:
            self.ema = price
            self.initialized = True
            return

        # Online update - O(1) memory
        self.ema = self.alpha * price + (1 - self.alpha) * self.ema

        # Same result regardless of restart point!
```

**Benefits:**
1. **Constant memory** (O(1))
2. **Small state** (fast persistence)
3. **Consistent results** (always same output)
4. **Can resume** from any point

## Stateless Design Principles

### Principle 1: Bounded Memory

**Use fixed-size data structures:**

```python
from collections import deque

class BoundedStrategy(pcts3.sv_object):
    def __init__(self):
        super().__init__()

        # ✅ GOOD - Fixed maximum size
        self.recent_prices = deque(maxlen=100)
        self.swing_points = deque(maxlen=50)
        self.volume_buffer = deque(maxlen=20)

        # ✅ GOOD - Single values
        self.ema_fast = 0.0
        self.ema_slow = 0.0
        self.atr = 0.0

        # ❌ BAD - Unbounded
        # self.all_prices = []  # WRONG!
        # self.all_volumes = []  # WRONG!
```

### Principle 2: Online Algorithms

**Update state incrementally without history:**

```python
class OnlineStrategy(pcts3.sv_object):
    """Uses online algorithms for O(1) memory."""

    def __init__(self):
        super().__init__()

        # EMA components (Welford's online algorithm)
        self.ema_mean = 0.0
        self.ema_var = 0.0
        self.alpha = 0.05

        # ADX components
        self.tr_ema = 0.0
        self.dm_plus_ema = 0.0
        self.dm_minus_ema = 0.0

        self.bar_count = 0

    def update_ema(self, value):
        """Online EMA update - no history needed."""
        self.ema_mean = self.alpha * value + (1 - self.alpha) * self.ema_mean

    def update_variance(self, value):
        """Welford's online variance algorithm."""
        delta = value - self.ema_mean
        self.ema_mean += self.alpha * delta
        self.ema_var += self.alpha * (delta * delta - self.ema_var)

    def update_atr(self, high, low, prev_close):
        """Online ATR calculation."""
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = max(tr1, tr2, tr3)

        # Online EMA of TR
        self.tr_ema = self.alpha * tr + (1 - self.alpha) * self.tr_ema
```

### Principle 3: No External Dependencies

**Self-contained state:**

```python
# ❌ BAD - External state
global_cache = {}  # WRONG!

class BadStrategy(pcts3.sv_object):
    def on_bar(self, bar):
        # Depends on external global
        if 'prices' not in global_cache:
            global_cache['prices'] = []
        global_cache['prices'].append(bar.close)

# ✅ GOOD - All state internal
class GoodStrategy(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.ema = 0.0  # All state in instance

    def on_bar(self, bar):
        price = float(bar.close)
        self.ema = 0.1 * price + 0.9 * self.ema
```

### Principle 4: Deterministic Computation

**Same input → Same output:**

```python
# ❌ BAD - Non-deterministic
import random
import time

class BadStrategy(pcts3.sv_object):
    def on_bar(self, bar):
        # Random introduces non-determinism
        noise = random.random()  # WRONG!
        signal = self.calculate_signal() + noise

        # Time-based decisions are non-deterministic
        if time.time() % 2 == 0:  # WRONG!
            return signal
        return 0

# ✅ GOOD - Deterministic
class GoodStrategy(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.pseudo_random_state = 12345  # Seed

    def on_bar(self, bar):
        price = float(bar.close)

        # Use bar_index for deterministic "randomness"
        if self.bar_index % 2 == 0:
            return self.calculate_signal(price)
        return 0
```

## Online Algorithms

### EMA (Exponential Moving Average)

**Standard EMA:**

```python
def update_ema(self, value, alpha=0.1):
    """
    Online EMA update.

    alpha = 2 / (period + 1)
    For 20-period EMA: alpha = 2 / 21 ≈ 0.095
    """
    if not self.initialized:
        self.ema = value
        self.initialized = True
    else:
        self.ema = alpha * value + (1 - alpha) * self.ema
```

### Welford's Online Variance

**Calculate mean and variance online:**

```python
class OnlineVariance:
    """Welford's algorithm for online mean and variance."""

    def __init__(self):
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0  # Sum of squared differences

    def update(self, value):
        """Add new value and update statistics."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self):
        """Current variance."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    @property
    def std_dev(self):
        """Current standard deviation."""
        return math.sqrt(self.variance)
```

**With EMA decay:**

```python
def update_ema_variance(self, value, alpha=0.05):
    """EMA-based variance (bounded memory)."""
    delta = value - self.ema_mean
    self.ema_mean += alpha * delta
    self.ema_var += alpha * (delta * delta - self.ema_var)

    # Volatility
    volatility = math.sqrt(max(self.ema_var, 0))
```

### Online Min/Max Tracking

**Track recent min/max with deque:**

```python
from collections import deque

class OnlineMinMax:
    """Track min/max over sliding window."""

    def __init__(self, window=20):
        self.window = window
        self.values = deque(maxlen=window)

    def update(self, value):
        """Add value and get current min/max."""
        self.values.append(value)
        return min(self.values), max(self.values)
```

### ATR (Average True Range)

**Online ATR calculation:**

```python
def update_atr(self, high, low, close, prev_close, alpha=0.1):
    """Online ATR using EMA."""
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - prev_close) if prev_close > 0 else 0
    tr3 = abs(low - prev_close) if prev_close > 0 else 0
    tr = max(tr1, tr2, tr3)

    # EMA of TR
    if self.atr == 0.0:
        self.atr = tr
    else:
        self.atr = alpha * tr + (1 - alpha) * self.atr
```

## State Persistence Patterns

### Pattern 1: Minimal State

```python
class MinimalState(pcts3.sv_object):
    """Store only what's necessary."""

    def __init__(self):
        super().__init__()

        # Metadata (constants)
        self.meta_name = "MinimalState"
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'SHFE'
        self.code = b'cu<00>'

        # Minimal state (automatically persisted)
        self.bar_index = 0
        self.ema = 0.0
        self.prev_close = 0.0

        # Control persistence
        self.persistent = True
```

### Pattern 2: Bounded Collections

```python
from collections import deque

class BoundedState(pcts3.sv_object):
    """Fixed-size collections for recent data."""

    def __init__(self):
        super().__init__()

        # Bounded collections (automatically persisted)
        self.recent_prices = deque(maxlen=100)
        self.swing_highs = deque(maxlen=50)
        self.swing_lows = deque(maxlen=50)

        # NOTE: deque is serialized as list
        # Maxlen is NOT preserved in serialization
        # Must restore maxlen after from_sv()
```

**Restoring deque after load:**

```python
def from_sv(self, sv):
    """Load state and restore deque constraints."""
    super().from_sv(sv)

    # Restore maxlen (not preserved in serialization)
    if not isinstance(self.recent_prices, deque):
        self.recent_prices = deque(self.recent_prices, maxlen=100)
    if not isinstance(self.swing_highs, deque):
        self.swing_highs = deque(self.swing_highs, maxlen=50)
    if not isinstance(self.swing_lows, deque):
        self.swing_lows = deque(self.swing_lows, maxlen=50)
```

### Pattern 3: Separate Persistent vs Transient

```python
class MixedState(pcts3.sv_object):
    """Separate persistent and transient state."""

    def __init__(self):
        super().__init__()

        # Persistent state (automatically saved)
        self.ema = 0.0
        self.signal = 0
        self.bar_index = 0

        # Transient state (not saved - use _ prefix)
        self._temp_buffer = []
        self._debug_info = {}
        self._cache = None

    def on_bar(self, bar):
        """Transient state rebuilt each run."""
        # Rebuild transient state
        self._temp_buffer = []
        self._cache = {}

        # Update persistent state
        self.ema = self.calculate_ema()
        self.bar_index += 1
```

## Replay Consistency

### What is Replay Consistency?

A strategy has replay consistency if:

```
Run A: Process bars 0-100 → State S100
Run B: Process bars 0-50, stop, reload, process 51-100 → State S100

State S100 from Run A == State S100 from Run B
```

**Testing replay consistency:**

```bash
python test_resuming_mode.py \
    --start 20250701203204 \
    --end 20250710203204 \
    --midpoint 20250705120000
```

This runs your strategy:
1. Continuously from start to end
2. From start to midpoint, then midpoint to end
3. Compares outputs - **must be identical**

### Achieving Replay Consistency

**Requirements:**

1. **Deterministic computation** (no random, no time-based)
2. **Complete state persistence** (all state in sv_object)
3. **Proper initialization** (from_sv restores exactly)
4. **No external dependencies** (no global state)
5. **Consistent ordering** (process bars in same order)

**Example with replay consistency:**

```python
class ReplayConsistent(pcts3.sv_object):
    """Guaranteed replay consistency."""

    def __init__(self):
        super().__init__()

        # All state persisted
        self.bar_index = 0
        self.ema = 0.0
        self.prev_close = 0.0
        self.signal = 0
        self.initialized = False

    def on_bar(self, bar):
        """Process bar deterministically."""
        close = float(bar.close)

        # Initialize
        if not self.initialized:
            self.ema = close
            self.prev_close = close
            self.initialized = True
            return

        # Deterministic update
        self.ema = 0.1 * close + 0.9 * self.ema

        # Deterministic signal
        if self.ema > self.prev_close * 1.01:
            self.signal = 1
        elif self.ema < self.prev_close * 0.99:
            self.signal = -1
        else:
            self.signal = 0

        # Update for next bar
        self.prev_close = close
        self.bar_index += 1

        # Output deterministically
        if self.bar_index % 12 == 0:  # Every 12 bars
            return [self.copy_to_sv()]
        return []
```

## Common Issues and Solutions

### Issue 1: Growing Memory

**Problem:**

```python
# ❌ Grows without bound
class Growing(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.all_prices = []

    def on_bar(self, bar):
        self.all_prices.append(bar.close)  # Never stops growing!
```

**Solution:**

```python
# ✅ Bounded memory
class Bounded(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.recent_prices = deque(maxlen=100)  # Fixed size

    def on_bar(self, bar):
        self.recent_prices.append(bar.close)  # Old values dropped
```

### Issue 2: Non-Determinism

**Problem:**

```python
# ❌ Random introduces non-determinism
import random

class NonDeterministic(pcts3.sv_object):
    def on_bar(self, bar):
        noise = random.random()  # Different each run!
        return self.signal + noise
```

**Solution:**

```python
# ✅ Deterministic pseudo-random
class Deterministic(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.random_state = 12345

    def on_bar(self, bar):
        # Deterministic "random" based on bar_index
        pseudo_rand = (self.bar_index * 9301 + 49297) % 233280
        normalized = pseudo_rand / 233280.0
        return self.signal + normalized * 0.01
```

### Issue 3: External State

**Problem:**

```python
# ❌ External global state
cached_data = {}

class ExternalState(pcts3.sv_object):
    def on_bar(self, bar):
        if 'ema' not in cached_data:  # External!
            cached_data['ema'] = 0.0
        cached_data['ema'] = 0.1 * bar.close + 0.9 * cached_data['ema']
```

**Solution:**

```python
# ✅ All state internal
class InternalState(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.ema = 0.0  # Instance variable

    def on_bar(self, bar):
        self.ema = 0.1 * bar.close + 0.9 * self.ema
```

### Issue 4: Incomplete Persistence

**Problem:**

```python
# ❌ Critical state not persisted
class Incomplete(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.ema = 0.0
        # Previous close NOT persisted (no instance variable)

    def on_bar(self, bar):
        close = float(bar.close)
        prev_close = close  # Local variable - not saved!
        self.ema = 0.1 * (close - prev_close) + 0.9 * self.ema
```

**Solution:**

```python
# ✅ All critical state persisted
class Complete(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.ema = 0.0
        self.prev_close = 0.0  # Instance variable - saved!

    def on_bar(self, bar):
        close = float(bar.close)
        self.ema = 0.1 * (close - self.prev_close) + 0.9 * self.ema
        self.prev_close = close  # Update for next bar
```

## Practical Example: Stateless Indicator

Complete example with all principles:

```python
#!/usr/bin/env python3
# coding=utf-8
"""Stateless Indicator with Perfect Replay Consistency"""

import math
from collections import deque
import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3

# Framework globals
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
    """Parse market data."""
    def __init__(self):
        super().__init__()
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = None
        self.turnover = None

class StatelessIndicator(pcts3.sv_object):
    """
    Stateless indicator with replay consistency.

    Uses online algorithms and bounded memory for:
    - EMA calculations
    - Volatility tracking
    - Swing point detection
    - Signal generation
    """

    def __init__(self, market, code):
        super().__init__()

        # Metadata (constants)
        self.meta_name = "StatelessIndicator"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900
        self.market = market
        self.code = code

        # State (automatically persisted)
        self.bar_index = 0
        self.timetag = None

        # Online algorithm state
        self.ema_fast = 0.0
        self.ema_slow = 0.0
        self.ema_mean = 0.0
        self.ema_var = 0.0
        self.atr = 0.0

        # Bounded collections
        self.recent_highs = deque(maxlen=20)
        self.recent_lows = deque(maxlen=20)

        # Previous values for calculations
        self.prev_close = 0.0
        self.prev_high = 0.0
        self.prev_low = 0.0

        # Outputs
        self.signal = 0
        self.volatility = 0.0
        self.initialized = False

        # Data parser
        self.quote = SampleQuote()
        self.persistent = True

        # Algorithm parameters (constants)
        self.alpha_fast = 2.0 / 11.0  # 10-period EMA
        self.alpha_slow = 2.0 / 21.0  # 20-period EMA
        self.alpha_vol = 2.0 / 21.0   # Volatility decay

    def initialize(self, imports, metas):
        """Initialize metadata."""
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)
        self.quote.load_def_from_dict(metas)
        self.quote.set_global_imports(imports)

    def on_bar(self, bar: pc.StructValue):
        """Process bar with guaranteed replay consistency."""
        # Filter for our instrument
        if bar.get_market() != self.market or bar.get_stock_code() != self.code:
            return []

        # Parse quote data
        if bar.get_namespace() == self.quote.namespace and \
           bar.get_meta_id() == self.quote.meta_id:
            self.quote.market = self.market
            self.quote.code = self.code
            self.quote.granularity = bar.get_granularity()
            self.quote.from_sv(bar)
        else:
            return []

        tm = bar.get_time_tag()

        # Initialize timetag
        if self.timetag is None:
            self.timetag = tm

        # Handle cycle boundary
        if self.timetag < tm:
            self._on_cycle_pass()

            results = []
            if self.bar_index > 0:
                results.append(self.copy_to_sv())

            self.timetag = tm
            self.bar_index += 1
            return results

        return []

    def _on_cycle_pass(self):
        """Process end of cycle with online algorithms."""
        # Extract OHLCV
        close = float(self.quote.close)
        high = float(self.quote.high)
        low = float(self.quote.low)
        volume = float(self.quote.volume)

        # Initialize on first bar
        if not self.initialized:
            self._initialize_state(close, high, low)
            return

        # Update EMAs (online)
        self.ema_fast = self.alpha_fast * close + (1 - self.alpha_fast) * self.ema_fast
        self.ema_slow = self.alpha_slow * close + (1 - self.alpha_slow) * self.ema_slow

        # Update volatility (Welford's algorithm with EMA)
        log_return = math.log(close / self.prev_close) if self.prev_close > 0 else 0
        delta = log_return - self.ema_mean
        self.ema_mean += self.alpha_vol * delta
        self.ema_var += self.alpha_vol * (delta * delta - self.ema_var)
        self.volatility = math.sqrt(max(self.ema_var, 0)) * math.sqrt(252)

        # Update ATR (online)
        self._update_atr(high, low, self.prev_close)

        # Update bounded collections
        self.recent_highs.append(high)
        self.recent_lows.append(low)

        # Generate signal (deterministic)
        self._generate_signal()

        # Update previous values for next bar
        self.prev_close = close
        self.prev_high = high
        self.prev_low = low

        logger.info(f"Bar {self.bar_index}: EMA_fast={self.ema_fast:.2f}, "
                   f"EMA_slow={self.ema_slow:.2f}, Signal={self.signal}")

    def _initialize_state(self, close, high, low):
        """Initialize state on first bar."""
        self.ema_fast = close
        self.ema_slow = close
        self.ema_mean = 0.0
        self.ema_var = 0.01
        self.atr = high - low
        self.prev_close = close
        self.prev_high = high
        self.prev_low = low
        self.initialized = True

    def _update_atr(self, high, low, prev_close):
        """Update ATR using online algorithm."""
        tr1 = high - low
        tr2 = abs(high - prev_close) if prev_close > 0 else 0
        tr3 = abs(low - prev_close) if prev_close > 0 else 0
        tr = max(tr1, tr2, tr3)

        # Online EMA of TR
        self.atr = self.alpha_slow * tr + (1 - self.alpha_slow) * self.atr

    def _generate_signal(self):
        """Generate signal deterministically."""
        # EMA crossover
        ema_cross = 1 if self.ema_fast > self.ema_slow else -1

        # Volatility filter
        high_vol = self.volatility > 0.3

        # Support/resistance from recent highs/lows
        if len(self.recent_highs) >= 20 and len(self.recent_lows) >= 20:
            recent_high = max(self.recent_highs)
            recent_low = min(self.recent_lows)

            # Near resistance
            if self.prev_close > recent_high * 0.995:
                self.signal = -1 if not high_vol else 0
            # Near support
            elif self.prev_close < recent_low * 1.005:
                self.signal = 1 if not high_vol else 0
            else:
                self.signal = ema_cross if not high_vol else 0
        else:
            self.signal = 0

    def from_sv(self, sv):
        """Load state and restore deque constraints."""
        super().from_sv(sv)

        # Restore deque maxlen (not preserved in serialization)
        if not isinstance(self.recent_highs, deque):
            self.recent_highs = deque(self.recent_highs, maxlen=20)
        if not isinstance(self.recent_lows, deque):
            self.recent_lows = deque(self.recent_lows, maxlen=20)

# Global indicator
indicator = StatelessIndicator(b'SHFE', b'cu<00>')

# Framework callbacks
async def on_init():
    global indicator, imports, metas, worker_no
    if worker_no != 0 and metas and imports:
        indicator.initialize(imports, metas)

async def on_ready():
    pass

async def on_bar(bar: pc.StructValue):
    global indicator, worker_no
    if worker_no != 1:
        return []
    return indicator.on_bar(bar)

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

## Summary

This chapter covered:

1. **Singularity**: Strategies that produce identical results regardless of when stopped/resumed
2. **Stateless Design**: Using bounded memory and online algorithms
3. **State Persistence**: Minimal, complete state in sv_object
4. **Online Algorithms**: EMA, Welford's variance, ATR calculations
5. **Replay Consistency**: Testing and achieving deterministic results
6. **Common Issues**: Growing memory, non-determinism, external state

**Key Takeaways:**

- Use online algorithms for O(1) memory
- Store only necessary state
- Make computation deterministic
- No external dependencies
- Test with test_resuming_mode.py
- Use deque with maxlen for bounded collections
- Restore deque constraints after from_sv()

**Next Steps:**

In the next chapter, we'll explore backtesting - running your stateless strategies through historical data to validate performance and tune parameters.

---

**Previous:** [04 - StructValue and sv_object](04-structvalue-and-sv_object.md) | **Next:** [06 - Backtest and Testing](06-backtest.md)
