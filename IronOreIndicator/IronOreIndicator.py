#!/usr/bin/env python3
# coding=utf-8
"""
IronOreIndicator - Multi-Indicator Confirmation System

Strategy: EMA Crossover + RSI Mean Reversion + Volume Confirmation
- Fast EMA (10-period) vs Slow EMA (20-period) for trend detection
- RSI (14-period) for oversold/overbought conditions
- Volume EMA (20-period) for liquidity confirmation

Market: DCE (Dalian Commodity Exchange)
Instrument: i<00> (Iron Ore logical contract)
Granularity: 900 seconds (15 minutes)
"""

import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3
from typing import List

# Framework globals (REQUIRED)
use_raw = True
overwrite = False  # Set to False for production
granularity = 900
schema = None
max_workers = 1
worker_no = None
exports = {}
imports = {}
metas = {}
logger = pcu3.vanilla_logger()


class SampleQuote(pcts3.sv_object):
    """Parse SampleQuote (OHLCV) data from global namespace"""

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


class IronOreIndicator(pcts3.sv_object):
    """
    Iron Ore Multi-Indicator Confirmation System

    Generates buy/sell signals based on:
    1. EMA Crossover (fast vs slow)
    2. RSI Mean Reversion (oversold/overbought)
    3. Volume Confirmation (above average)

    All algorithms use online computation for bounded memory (O(1))
    """

    def __init__(self):
        super().__init__()

        # Metadata - CONSTANTS (never change after initialization)
        self.meta_name = "IronOreIndicator"
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'i<00>'
        self.revision = (1 << 32) - 1

        # State variables (automatically persisted by framework)
        self.bar_index = 0
        self.timetag = None
        self.initialized = False

        # EMA state
        self.ema_fast = 0.0      # 10-period EMA
        self.ema_slow = 0.0      # 20-period EMA
        self.volume_ema = 0.0    # 20-period volume EMA

        # RSI state (online algorithm)
        self.rsi = 50.0          # RSI value (0-100)
        self.gain_ema = 0.0      # EMA of gains for RSI
        self.loss_ema = 0.0      # EMA of losses for RSI
        self.prev_close = 0.0    # Previous close for RSI calculation

        # Signal outputs
        self.signal = 0          # -1 (sell), 0 (neutral), 1 (buy)
        self.confidence = 0.0    # Signal confidence [0.0, 1.0]
        self.indicator_value = 0.0  # Main indicator output (RSI)

        # EMA parameters (alpha = 2 / (period + 1))
        self.alpha_fast = 2.0 / 11.0    # 10-period: 2/(10+1) = 0.1818
        self.alpha_slow = 2.0 / 21.0    # 20-period: 2/(20+1) = 0.0952
        self.alpha_rsi = 2.0 / 15.0     # 14-period: 2/(14+1) = 0.1333
        self.alpha_vol = 2.0 / 21.0     # 20-period: 2/(20+1) = 0.0952

        # Volume confirmation threshold
        self.volume_multiplier = 1.2    # Require 1.2x average volume

        # Dependency sv_objects
        self.sq = SampleQuote()

        # Control persistence
        self.persistent = True

    def initialize(self, imports, metas):
        """Initialize metadata schemas for all sv_objects"""
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)

        # Initialize dependencies
        self.sq.load_def_from_dict(metas)
        self.sq.set_global_imports(imports)

    def on_bar(self, bar: pc.StructValue) -> List[pc.StructValue]:
        """
        Process incoming market data bars

        Args:
            bar: StructValue containing market data

        Returns:
            List of StructValue outputs (empty list if no output this cycle)
        """
        ret = []  # ALWAYS return list

        # Extract metadata
        market = bar.get_market()
        code = bar.get_stock_code()
        tm = bar.get_time_tag()
        ns = bar.get_namespace()
        meta_id = bar.get_meta_id()

        # Filter for our market/instrument
        if market != self.market:
            return ret

        # Route to appropriate sv_object
        if self.sq.namespace == ns and self.sq.meta_id == meta_id:
            # Filter for logical contracts only (ending in <00>)
            if code.endswith(b'<00>'):
                # Set metadata before from_sv
                self.sq.market = market
                self.sq.code = code
                self.sq.granularity = bar.get_granularity()

                # Parse data into sv_object
                self.sq.from_sv(bar)

                # Handle cycle boundaries
                if self.timetag is None:
                    self.timetag = tm

                if self.timetag < tm:
                    # New cycle - process previous cycle's data
                    self._on_cycle_pass(tm)

                    # Serialize state if ready
                    if self.ready_to_serialize():
                        ret.append(self.copy_to_sv())

                    # Update for next cycle
                    self.timetag = tm
                    self.bar_index += 1

        return ret  # ALWAYS return list

    def _on_cycle_pass(self, time_tag):
        """
        Process end of cycle - calculate indicators and generate signals

        Uses online algorithms for bounded memory:
        - EMA: O(1) update
        - RSI: O(1) update via gain/loss EMAs
        - Volume EMA: O(1) update

        Args:
            time_tag: Current cycle timestamp
        """
        # Extract OHLCV data
        close = float(self.sq.close)
        volume = float(self.sq.volume)
        high = float(self.sq.high)
        low = float(self.sq.low)

        # Initialize on first bar
        if not self.initialized:
            self._initialize_state(close, volume)
            return

        # --- Update EMAs (online algorithm) ---
        self.ema_fast = self.alpha_fast * close + (1 - self.alpha_fast) * self.ema_fast
        self.ema_slow = self.alpha_slow * close + (1 - self.alpha_slow) * self.ema_slow
        self.volume_ema = self.alpha_vol * volume + (1 - self.alpha_vol) * self.volume_ema

        # --- Update RSI (online algorithm) ---
        change = close - self.prev_close
        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        # Update gain/loss EMAs
        self.gain_ema = self.alpha_rsi * gain + (1 - self.alpha_rsi) * self.gain_ema
        self.loss_ema = self.alpha_rsi * loss + (1 - self.alpha_rsi) * self.loss_ema

        # Calculate RSI
        if self.loss_ema > 0:
            rs = self.gain_ema / self.loss_ema
            self.rsi = 100.0 - (100.0 / (1.0 + rs))
        else:
            self.rsi = 100.0  # No losses = max RSI

        # Update indicator value (using RSI as main indicator)
        self.indicator_value = self.rsi

        # --- Generate Signal ---
        self._generate_signal(volume)

        # Update previous close for next iteration
        self.prev_close = close

        # Log signal generation
        if self.signal != 0:
            logger.info(
                f"Bar {self.bar_index}: Signal={self.signal}, "
                f"Confidence={self.confidence:.3f}, "
                f"RSI={self.rsi:.2f}, "
                f"EMA_fast={self.ema_fast:.2f}, "
                f"EMA_slow={self.ema_slow:.2f}"
            )

    def _initialize_state(self, close, volume):
        """
        Initialize indicator state on first bar

        Args:
            close: First closing price
            volume: First volume
        """
        self.ema_fast = close
        self.ema_slow = close
        self.volume_ema = volume
        self.rsi = 50.0
        self.gain_ema = 0.0
        self.loss_ema = 0.0
        self.prev_close = close
        self.signal = 0
        self.confidence = 0.0
        self.indicator_value = 50.0  # Initialize with neutral RSI
        self.initialized = True

        logger.info(
            f"Initialized: close={close:.2f}, volume={volume:.2f}"
        )

    def _generate_signal(self, volume):
        """
        Generate trading signal based on multi-indicator confirmation

        Signal Logic:
        - BUY: Uptrend + Oversold + High Volume
        - SELL: Downtrend + Overbought + High Volume
        - NEUTRAL: Otherwise

        Args:
            volume: Current bar volume
        """
        # Check trend direction (EMA crossover)
        uptrend = self.ema_fast > self.ema_slow
        downtrend = self.ema_fast < self.ema_slow

        # Check mean reversion (RSI)
        oversold = self.rsi < 30.0
        overbought = self.rsi > 70.0

        # Check volume confirmation
        high_volume = volume > (self.volume_ema * self.volume_multiplier)

        # Generate signal with confidence
        if uptrend and oversold and high_volume:
            # BUY signal
            self.signal = 1
            self.confidence = (30.0 - self.rsi) / 30.0  # Confidence increases as RSI decreases below 30
        elif downtrend and overbought and high_volume:
            # SELL signal
            self.signal = -1
            self.confidence = (self.rsi - 70.0) / 30.0  # Confidence increases as RSI increases above 70
        else:
            # NEUTRAL
            self.signal = 0
            self.confidence = 0.0

    def ready_to_serialize(self) -> bool:
        """
        Determine if state should be serialized

        Returns:
            True if bar_index > 0 and initialized
        """
        return self.bar_index > 0 and self.initialized


# Global instance
indicator = IronOreIndicator()


# Framework callbacks (REQUIRED)

async def on_init():
    """Initialize indicator with metadata schemas"""
    global indicator, imports, metas, worker_no
    if worker_no != 0 and metas and imports:
        indicator.initialize(imports, metas)
        logger.info("IronOreIndicator initialized")


async def on_bar(bar: pc.StructValue):
    """Process incoming bars"""
    global indicator, worker_no
    if worker_no != 1:
        return []
    return indicator.on_bar(bar)


async def on_ready():
    """Called when framework is ready"""
    logger.info("IronOreIndicator ready")


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


async def on_historical(params, records):
    """Called on historical data"""
    pass
