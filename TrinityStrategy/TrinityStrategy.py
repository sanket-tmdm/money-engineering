#!/usr/bin/env python3
# coding=utf-8
"""
Trinity Strategy - Phase 1: Scout Indicators

Implements the three-tier "Trinity" adaptive trading system's Tier-1 indicators:
- WOS_TrendScout: ADX + Directional Movement (regime detection)
- WOS_TensionScout: Stateless Bollinger Bands (volatility/stretch)
- WOS_CrowdScout: VWMA Oscillator (volume conviction)

Following the WOS "Captain's Playbook" philosophy from trinity-strategy.md:
1. Identify the "Pitch" (Market Regime): Tricky (Ranging) or Flat (Trending)?
2. Switch the Playbook: Mean-Reversion vs Trend-Following
3. Confirm with Volume: Crowd conviction validation

Architecture: WOS Tier-1 indicators with online algorithms (O(1) memory)
"""

import math
import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3
from typing import List

# Framework configuration
use_raw = True
overwrite = False  # Production mode: persist data to server
granularity = 900  # Primary granularity (15 minutes)
max_workers = 1
worker_no = None
exports = {}
imports = {}
metas = {}
logger = pcu3.vanilla_logger()


class SampleQuote(pcts3.sv_object):
    """Market data (OHLCV) from global namespace"""

    def __init__(self):
        super().__init__()

        # Metadata - CONSTANTS
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # OHLCV fields (automatically populated by from_sv)
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = None
        self.turnover = None


class WOS_TrendScout(pcts3.sv_object):
    """
    Scout 1: TrendScout - ADX-based Trend Strength Indicator

    Purpose: Identifies market regime - "Tricky Pitch" (ranging) vs "Flat Pitch" (trending)

    Measures trend strength using Average Directional Index (ADX) and
    directional movement indicators (DI+, DI-) with online algorithms.

    Outputs:
        - adx_value: Trend strength (0-100, >25 = strong trend, <20 = ranging)
        - di_plus: Positive directional indicator
        - di_minus: Negative directional indicator

    Algorithm: Online EMA-based ADX calculation with O(1) memory
    Reference: trinity-strategy.md § 3.1
    """

    def __init__(self, market: bytes, code: bytes):
        super().__init__()

        # Metadata - CONSTANTS
        self.meta_name = "WOS_TrendScout"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900
        self.market = market
        self.code = code

        # State variables (automatically persisted)
        self.bar_index = 0

        # Previous OHLC values for directional movement calculation
        self.prev_high = 0.0
        self.prev_low = 0.0
        self.prev_close = 0.0

        # Online EMA state for ADX components
        self.tr_ema = 0.0          # True Range EMA
        self.dm_plus_ema = 0.0     # +DM (Positive Directional Movement) EMA
        self.dm_minus_ema = 0.0    # -DM (Negative Directional Movement) EMA
        self.dx_ema = 0.0          # DX EMA (becomes ADX)

        # Output fields
        self.adx_value = 0.0
        self.di_plus = 0.0
        self.di_minus = 0.0

        # Algorithm parameters
        self.period = 14                    # Standard ADX period
        self.alpha = 2.0 / (self.period + 1.0)  # EMA smoothing factor
        self.initialized = False

        # Control state persistence
        self.persistent = True

    def calculate_indicators(self, high: float, low: float, close: float):
        """
        Calculate ADX and directional indicators using online algorithms

        Mathematical Process:
        1. Calculate True Range (TR) and Directional Movements (+DM, -DM)
        2. Apply EMA smoothing to TR, +DM, -DM
        3. Calculate DI+ and DI- from smoothed values
        4. Calculate DX from DI+ and DI-
        5. Apply EMA smoothing to DX to get ADX

        Args:
            high: Current bar high
            low: Current bar low
            close: Current bar close
        """
        # First bar initialization
        if not self.initialized:
            self.prev_high = high
            self.prev_low = low
            self.prev_close = close

            # Initialize EMA states with first TR value
            first_tr = high - low
            self.tr_ema = first_tr
            self.dm_plus_ema = 0.0
            self.dm_minus_ema = 0.0
            self.dx_ema = 0.0

            # Initialize outputs to zero
            self.adx_value = 0.0
            self.di_plus = 0.0
            self.di_minus = 0.0

            self.initialized = True
            return

        # Step 1: Calculate True Range (TR)
        # TR = max(high - low, |high - prev_close|, |low - prev_close|)
        tr1 = high - low
        tr2 = abs(high - self.prev_close)
        tr3 = abs(low - self.prev_close)
        tr = max(tr1, tr2, tr3)

        # Step 2: Calculate Directional Movements (+DM and -DM)
        # +DM measures upward movement, -DM measures downward movement
        high_move = high - self.prev_high
        low_move = self.prev_low - low

        # +DM: Positive only if upward movement dominates downward
        if high_move > low_move and high_move > 0:
            dm_plus = high_move
        else:
            dm_plus = 0.0

        # -DM: Positive only if downward movement dominates upward
        if low_move > high_move and low_move > 0:
            dm_minus = low_move
        else:
            dm_minus = 0.0

        # Step 3: Apply online EMA smoothing
        # EMA formula: new_ema = alpha * value + (1 - alpha) * old_ema
        self.tr_ema = self.alpha * tr + (1.0 - self.alpha) * self.tr_ema
        self.dm_plus_ema = self.alpha * dm_plus + (1.0 - self.alpha) * self.dm_plus_ema
        self.dm_minus_ema = self.alpha * dm_minus + (1.0 - self.alpha) * self.dm_minus_ema

        # Step 4: Calculate Directional Indicators (DI+ and DI-)
        # DI+ = 100 * (+DM_EMA / TR_EMA)
        # DI- = 100 * (-DM_EMA / TR_EMA)
        if self.tr_ema > 0:
            self.di_plus = 100.0 * (self.dm_plus_ema / self.tr_ema)
            self.di_minus = 100.0 * (self.dm_minus_ema / self.tr_ema)
        else:
            self.di_plus = 0.0
            self.di_minus = 0.0

        # Step 5: Calculate DX (Directional Index)
        # DX = 100 * |DI+ - DI-| / (DI+ + DI-)
        di_sum = self.di_plus + self.di_minus
        if di_sum > 0:
            dx = 100.0 * abs(self.di_plus - self.di_minus) / di_sum
        else:
            dx = 0.0

        # Step 6: Apply EMA smoothing to DX to get ADX
        # ADX = EMA of DX
        self.dx_ema = self.alpha * dx + (1.0 - self.alpha) * self.dx_ema
        self.adx_value = self.dx_ema

        # Update previous values for next calculation
        self.prev_high = high
        self.prev_low = low
        self.prev_close = close

        self.bar_index += 1


class WOS_TensionScout(pcts3.sv_object):
    """
    Scout 2: TensionScout - Stateless Bollinger Bands using Welford's Online Variance

    Purpose: Measures "batsman's stretch" - price volatility and overbought/oversold conditions

    Mathematical Specification:
    - Middle Band = 20-period EMA of close price
    - Standard Deviation = Welford's Online Variance with EMA decay (NOT rolling window)
    - Upper Band = Middle + (2 × Online_Std_Dev)
    - Lower Band = Middle - (2 × Online_Std_Dev)

    Key Innovation: This is NOT traditional Bollinger Bands. Uses online algorithms
    for O(1) memory with perfect replay consistency.

    Reference: trinity-strategy.md § 3.2
    """

    def __init__(self, market: bytes, code: bytes):
        super().__init__()

        # Metadata - CONSTANTS
        self.meta_name = "WOS_TensionScout"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900
        self.market = market
        self.code = code

        # State variables (automatically persisted)
        self.bar_index = 0

        # Online variance state (Welford's algorithm with EMA decay)
        self.ema_mean = 0.0      # Running mean (EMA of price)
        self.ema_var = 0.0       # Running variance (EMA-based)

        # Output fields
        self.middle_band = 0.0   # 20-period EMA
        self.upper_band = 0.0    # Middle + 2×std_dev
        self.lower_band = 0.0    # Middle - 2×std_dev

        # Algorithm parameters (constants)
        self.alpha = 2.0 / 21.0  # 20-period EMA smoothing factor
        self.num_std = 2.0       # Number of standard deviations for bands

        # Initialization flag
        self.initialized = False

        # Control state persistence
        self.persistent = True

    def calculate_bands(self, close: float):
        """
        Calculate Bollinger Bands using Welford's Online Variance Algorithm

        This is the KEY innovation: no rolling window, no history storage.
        Uses exponential moving average for both mean and variance.

        Welford's Algorithm with EMA decay:
        1. delta = value - ema_mean
        2. ema_mean += alpha × delta
        3. ema_var += alpha × (delta² - ema_var)
        4. std_dev = sqrt(ema_var)

        Args:
            close: Current bar's close price
        """
        # First bar: Initialize state
        if not self.initialized:
            self.ema_mean = close
            self.ema_var = 0.0  # Zero variance on first bar
            self.initialized = True
        else:
            # Welford's online variance update with EMA decay
            # Step 1: Calculate deviation from current mean
            delta = close - self.ema_mean

            # Step 2: Update mean using EMA
            self.ema_mean += self.alpha * delta

            # Step 3: Update variance using EMA
            # This is the key: variance of deviations, not sum of squares
            self.ema_var += self.alpha * (delta * delta - self.ema_var)

        # Calculate standard deviation from variance
        # Ensure non-negative before sqrt (numerical stability)
        std_dev = math.sqrt(max(self.ema_var, 0.0))

        # Output: Bollinger Bands
        # Middle band is the EMA of price
        self.middle_band = self.ema_mean

        # Upper/Lower bands are ±2 standard deviations from middle
        self.upper_band = self.middle_band + (self.num_std * std_dev)
        self.lower_band = self.middle_band - (self.num_std * std_dev)

        self.bar_index += 1


class WOS_CrowdScout(pcts3.sv_object):
    """
    Scout 3: CrowdScout - Measures market conviction via VWMA Oscillator

    Purpose: Detects "crowd roar" - whether volume confirms price action (conviction)

    Algorithm:
        VWMA = EMA(Price × Volume) / EMA(Volume)
        Conviction Oscillator = VWMA₁₀ - EMA₁₀

    Output:
        > 0: Bullish Conviction (volume supporting upward moves)
        < 0: Bearish Conviction (volume supporting downward moves)

    Memory: O(1) - uses online EMA algorithms only
    Reference: trinity-strategy.md § 3.3
    """

    def __init__(self, market: bytes, code: bytes):
        super().__init__()

        # Metadata - CONSTANTS
        self.meta_name = "WOS_CrowdScout"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900
        self.market = market
        self.code = code

        # State variables (automatically persisted)
        self.bar_index = 0

        # VWMA components (online EMAs)
        self.pv_ema = 0.0      # EMA of (Price × Volume)
        self.v_ema = 0.0       # EMA of Volume
        self.price_ema = 0.0   # EMA of Price

        # Output field
        self.conviction_oscillator = 0.0

        # Algorithm parameters
        self.alpha = 2.0 / 11.0  # 10-period EMA: α = 2/(N+1)
        self.initialized = False

        # Control persistence
        self.persistent = True

    def calculate_conviction(self, close: float, volume: float):
        """
        Calculate VWMA and conviction oscillator

        Args:
            close: Current bar close price
            volume: Current bar volume
        """
        # Handle zero volume gracefully
        if volume < 0.001:  # Effectively zero
            # Skip update, maintain previous values
            return

        # Initialize on first bar
        if not self.initialized:
            self.pv_ema = close * volume
            self.v_ema = volume
            self.price_ema = close
            self.initialized = True
            # Oscillator is 0 on first bar (VWMA == EMA)
            self.conviction_oscillator = 0.0
            return

        # Update EMAs using online algorithm
        # EMA(t) = α × Value(t) + (1-α) × EMA(t-1)
        pv = close * volume
        self.pv_ema = self.alpha * pv + (1.0 - self.alpha) * self.pv_ema
        self.v_ema = self.alpha * volume + (1.0 - self.alpha) * self.v_ema
        self.price_ema = self.alpha * close + (1.0 - self.alpha) * self.price_ema

        # Calculate VWMA as ratio
        # VWMA = EMA(Price × Volume) / EMA(Volume)
        if self.v_ema > 0.001:  # Avoid division by zero
            vwma = self.pv_ema / self.v_ema
        else:
            # Fallback to price EMA if volume EMA is near zero
            vwma = self.price_ema

        # Calculate conviction oscillator
        # Oscillator = VWMA - EMA(Price)
        # Positive: Volume-weighted average > simple average → bullish conviction
        # Negative: Volume-weighted average < simple average → bearish conviction
        self.conviction_oscillator = vwma - self.price_ema

        self.bar_index += 1


class TrinityCommodityManager(pcts3.sv_object):
    """
    Manager for one commodity's Trinity Scouts

    Creates and manages one set of three Scouts (Trend, Tension, Crowd) for a single commodity.
    Routes incoming bars to all three Scouts and aggregates their outputs.

    Following WOS Doctrine 1: Multiple Indicator Objects (one per commodity)
    """

    def __init__(self, market: bytes, code: bytes):
        super().__init__()

        # Metadata
        self.meta_name = "TrinityStrategy"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900
        self.market = market
        self.code = code + b'<00>'  # Logical contract

        # State variables
        self.bar_index = 0
        self.timetag = None

        # Create the three Scouts for this commodity
        self.trend_scout = WOS_TrendScout(market, self.code)
        self.tension_scout = WOS_TensionScout(market, self.code)
        self.crowd_scout = WOS_CrowdScout(market, self.code)

        # Output fields (aggregated from all Scouts)
        # TrendScout outputs
        self.adx_value = 0.0
        self.di_plus = 0.0
        self.di_minus = 0.0

        # TensionScout outputs
        self.upper_band = 0.0
        self.middle_band = 0.0
        self.lower_band = 0.0

        # CrowdScout outputs
        self.conviction_oscillator = 0.0

        # Dependency
        self.sq = SampleQuote()

        # Control persistence
        self.persistent = True

        logger.info(f"Initialized TrinityCommodityManager for {market.decode()}:{code.decode()}")

    def initialize(self, imports, metas):
        """Initialize schemas for dependencies"""
        # CRITICAL: Manager must initialize its own schema to serialize outputs
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)

        # Initialize SampleQuote parser
        self.sq.load_def_from_dict(metas)
        self.sq.set_global_imports(imports)

        logger.info(f"[{self.market.decode()}:{self.code.decode()}] Schema initialized - "
                   f"meta_id={self.meta_id}, namespace={self.namespace}")

    def on_bar(self, bar: pc.StructValue) -> List[pc.StructValue]:
        """Process incoming market data bars"""
        ret = []

        # Extract metadata
        market = bar.get_market()
        code = bar.get_stock_code()
        tm = bar.get_time_tag()
        ns = bar.get_namespace()
        meta_id = bar.get_meta_id()

        # Filter for our instrument and logical contract only
        if market != self.market or code != self.code:
            return ret

        # Route SampleQuote data
        if self.sq.namespace == ns and self.sq.meta_id == meta_id:
            # Set metadata before from_sv
            self.sq.market = market
            self.sq.code = code
            self.sq.granularity = bar.get_granularity()

            # Parse data
            self.sq.from_sv(bar)

            # Handle cycle boundaries
            if self.timetag is None:
                self.timetag = tm

            if self.timetag < tm:
                # New cycle - process previous cycle's data
                self._on_cycle_pass()

                # Serialize state if ready
                if self.ready_to_serialize():
                    sv = self.copy_to_sv()
                    ret.append(sv)
                    if self.bar_index % 50 == 0:  # Log every 50th bar to reduce noise
                        logger.info(f"[{self.market.decode()}:{self.code.decode()}] Serializing bar {self.bar_index}: "
                                   f"adx={self.adx_value:.2f}, bb_mid={self.middle_band:.2f}, "
                                   f"conviction={self.conviction_oscillator:.4f}")

                # Update for next cycle
                self.timetag = tm
                self.bar_index += 1

        return ret

    def _on_cycle_pass(self):
        """
        Process end of cycle - run all three Scouts

        This is where the three independent "Scout reports" are generated:
        1. TrendScout: Identifies the market regime (trending vs ranging)
        2. TensionScout: Measures volatility and price stretch
        3. CrowdScout: Confirms with volume conviction
        """
        # Extract OHLCV data
        high = float(self.sq.high)
        low = float(self.sq.low)
        close = float(self.sq.close)
        volume = float(self.sq.volume)

        # Run all three Scouts
        self.trend_scout.calculate_indicators(high, low, close)
        self.tension_scout.calculate_bands(close)
        self.crowd_scout.calculate_conviction(close, volume)

        # Aggregate Scout outputs into this manager's output fields
        self.adx_value = self.trend_scout.adx_value
        self.di_plus = self.trend_scout.di_plus
        self.di_minus = self.trend_scout.di_minus

        self.upper_band = self.tension_scout.upper_band
        self.middle_band = self.tension_scout.middle_band
        self.lower_band = self.tension_scout.lower_band

        self.conviction_oscillator = self.crowd_scout.conviction_oscillator

        # Only log every 50th bar to reduce noise
        if self.bar_index % 50 == 0:
            logger.debug(f"[{self.market.decode()}:{self.code.decode()}] Bar {self.bar_index}: "
                        f"ADX={self.adx_value:.2f}, BB_mid={self.middle_band:.2f}, "
                        f"Conviction={self.conviction_oscillator:.4f}")

    def ready_to_serialize(self) -> bool:
        """Output after all Scouts are initialized"""
        return (self.bar_index > 0 and
                self.trend_scout.initialized and
                self.tension_scout.initialized and
                self.crowd_scout.initialized)


class TrinityMultiCommodityManager:
    """
    Top-level manager for all commodities

    Creates and manages Trinity Scouts for multiple commodities:
    - Iron Ore (DCE:i) - Trending market
    - Copper (SHFE:cu) - Ranging market
    - Crude Oil (SHFE:sc) - Volatile/Wild card market

    Routes bars to appropriate commodity managers.
    """

    def __init__(self):
        # Create manager for each commodity
        self.managers = {
            (b'DCE', b'i'): TrinityCommodityManager(b'DCE', b'i'),
            (b'SHFE', b'cu'): TrinityCommodityManager(b'SHFE', b'cu'),
            (b'SHFE', b'sc'): TrinityCommodityManager(b'SHFE', b'sc'),
        }

        logger.info(f"Initialized TrinityMultiCommodityManager with {len(self.managers)} commodities")

    def initialize(self, imports, metas):
        """Initialize all commodity managers"""
        for manager in self.managers.values():
            manager.initialize(imports, metas)

    def on_bar(self, bar: pc.StructValue) -> List[pc.StructValue]:
        """Route bar to appropriate commodity manager"""
        results = []

        # Extract metadata
        market = bar.get_market()
        code_full = bar.get_stock_code()

        # Extract commodity code (before '<00>')
        if code_full.endswith(b'<00>'):
            # Logical contract - extract base commodity code
            code = code_full[:-4]  # Remove '<00>'
        else:
            # Not a logical contract - skip
            return results

        # Route to appropriate manager
        key = (market, code)
        if key in self.managers:
            outputs = self.managers[key].on_bar(bar)
            results.extend(outputs)

        return results


# Global manager
manager = TrinityMultiCommodityManager()


# Framework callbacks (REQUIRED)

async def on_init():
    """Initialize all commodity managers with schemas"""
    global manager, imports, metas, worker_no
    logger.info(f"on_init called: worker_no={worker_no}, has_metas={metas is not None}, has_imports={imports is not None}")
    if worker_no != 0 and metas and imports:
        manager.initialize(imports, metas)
        logger.info("Trinity Strategy Phase 1 initialized - All Scouts ready")
    else:
        logger.info(f"Initialization SKIPPED: worker_no={worker_no}")


async def on_bar(bar: pc.StructValue):
    """Process incoming bars"""
    global manager, worker_no
    if worker_no != 1:
        return []

    results = manager.on_bar(bar)
    # Removed verbose logging to reduce noise
    return results


async def on_ready():
    """Called when framework is ready"""
    logger.info("Trinity Strategy framework ready")


async def on_market_open(market, tradeday, time_tag, time_string):
    """Called on market open"""
    pass


async def on_market_close(market, tradeday, timetag, timestring):
    """Called on market close"""
    pass


async def on_reference(market, tradeday, data, timetag, timestring):
    """Called on reference data"""
    pass


async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    """Called at beginning of trade day"""
    pass


async def on_tradeday_end(market, tradeday, timetag, timestring):
    """Called at end of trade day"""
    pass
