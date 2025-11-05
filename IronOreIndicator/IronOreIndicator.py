#!/usr/bin/env python3
# coding=utf-8
"""
IronOreIndicatorRelaxed - Short-Term Position Accumulation Strategy

SHORT-TERM TRADING STRATEGY with 7-Indicator Market Regime Detection:
- Triple EMA (12/26/50) - Trend identification & MA crossover signals
- MACD (12/26/9) - Momentum confirmation & reversal detection
- RSI (14) - Mean reversion signals (relaxed: 40/60)
- Bollinger Bands (20, 2σ) - Price extremes & volatility
- ATR (14) - Volatility measurement
- BB Width - Volatility confirmation
- Volume EMA (20) - Liquidity confirmation (1.1x-1.2x)

Market Regimes & Trading Logic:
1. Strong Uptrend - BUY dips (3/5), SELL quickly (2/4) - Short holds
2. Strong Downtrend - BUY on REVERSALS (3/6), SELL aggressively (1/3)
3. Sideways/Ranging - BUY dips (2/4), SELL quickly (2/4) - Quick scalps
4. High Volatility Chaos - BUY on RECOVERY (3/5), SELL if in position

Key Features:
- LONG ONLY with POSITION ACCUMULATION
- 70% MAX ALLOCATION (30% cash reserve)
- SHORT-TERM FOCUSED (quick profit taking)
- BUY THE DIP + REVERSALS (add 50 contracts per signal)
- SELL ALL on exits (take profits quickly)
- MA CROSSOVER reversal detection
- PRICE ACTION patterns (bar position, bounces)
- 1-bar cooldown (aggressive re-entry)
- Average entry price tracking
"""

import math
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

    Generates regime-aware buy/sell signals using multi-layer confirmation
    """

    def __init__(self):
        super().__init__()

        # Metadata - CONSTANTS (never change after initialization)
        self.meta_name = "IronOreIndicatorRelaxed"
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'i<00>'
        self.revision = (1 << 32) - 1

        # State variables (automatically persisted by framework)
        self.bar_index = 0
        self.timetag = None
        self.initialized = False

        # Alpha parameters (smoothing factors)
        self.alpha_12 = 2.0 / 13.0   # 0.1538
        self.alpha_26 = 2.0 / 27.0   # 0.0741
        self.alpha_50 = 2.0 / 51.0   # 0.0392
        self.alpha_9 = 2.0 / 10.0    # 0.2000
        self.alpha_14 = 2.0 / 15.0   # 0.1333
        self.alpha_20 = 2.0 / 21.0   # 0.0952

        # Current bar OHLCV
        self.open = 0.0
        self.high = 0.0
        self.low = 0.0
        self.close = 0.0
        self.volume = 0.0

        # Triple EMA states
        self.ema_12 = 0.0
        self.ema_26 = 0.0
        self.ema_50 = 0.0

        # MACD states
        self.macd = 0.0
        self.macd_signal = 0.0
        self.macd_histogram = 0.0

        # RSI states (online algorithm via gain/loss EMAs)
        self.rsi = 50.0
        self.gain_ema = 0.0
        self.loss_ema = 0.0
        self.prev_close = 0.0

        # Bollinger Band states (Welford's online variance)
        self.bb_n = 0
        self.bb_mean = 0.0
        self.bb_m2 = 0.0  # Sum of squared differences
        self.bb_variance = 0.0
        self.bb_std_dev = 0.0
        self.bb_upper = 0.0
        self.bb_middle = 0.0
        self.bb_lower = 0.0
        self.bb_width = 0.0
        self.bb_width_pct = 0.0

        # ATR states
        self.atr = 0.0
        self.mean_atr = 0.0
        self.atr_count = 0
        self.prev_close_atr = 0.0

        # Volume EMA
        self.volume_ema = 0.0

        # Regime tracking
        self.regime = 3  # Default to ranging
        self.regime_prev = 3

        # Signal outputs
        self.signal = 0          # -1 (sell), 0 (neutral), 1 (buy)
        self.confidence = 0.0    # Signal confidence [0.0, 1.0]
        self.position_state = 0  # 0 = flat, 1 = in position
        self.last_exit_bar = -999  # Track last exit to prevent immediate re-entry
        self.cooldown_bars = 1   # Minimum bars to wait after exit (short-term focused)

        # Portfolio tracking (simulation with $1,000,000 initial capital)
        self.initial_capital = 1000000.0  # Starting capital (CNY)
        self.cash = 1000000.0             # Current cash
        self.contracts_held = 0           # Number of contracts in position
        self.entry_price = 0.0            # Average entry price for current position
        self.portfolio_value = 1000000.0  # PV = cash + position_value
        self.contracts_per_trade = 50     # Contracts per signal (increased from 10)
        self.max_allocation = 0.70        # Max 70% of portfolio can be invested
        self.reserve_allocation = 0.30    # Keep 30% in reserve

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

        # Filter for our market
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
        Process cycle - calculate indicators and generate signals

        Pipeline:
        1. Extract OHLCV data
        2. Initialize on first bar
        3. Update all indicators (online algorithms)
        4. Detect market regime
        5. Generate trading signal
        6. Log signal if generated
        """

        # Extract OHLCV data
        self.open = float(self.sq.open)
        self.high = float(self.sq.high)
        self.low = float(self.sq.low)
        self.close = float(self.sq.close)
        self.volume = float(self.sq.volume)

        # Initialize on first bar
        if not self.initialized:
            self._initialize_state()
            return

        # Update indicators (order matters for dependencies)
        self._update_emas(self.close)
        self._update_macd()
        self._update_rsi(self.close)
        self._update_bollinger_bands(self.close)
        self._update_atr(self.high, self.low, self.close)
        self._update_volume_ema(self.volume)

        # Detect regime
        self._detect_regime()

        # Generate signal
        self._generate_signal()

        # Update portfolio based on signal and current prices
        self._update_portfolio()

        # Log regime every 100 bars (for debugging stuck issues)
        if self.bar_index % 100 == 0 or self.signal != 0:
            position_value = self.contracts_held * self.close
            allocation_pct = (position_value / self.portfolio_value * 100) if self.portfolio_value > 0 else 0
            logger.info(
                f"[Bar {self.bar_index}] Regime={self.regime}, "
                f"RSI={self.rsi:.2f}, "
                f"MACD={self.macd:.4f}, "
                f"EMA12={self.ema_12:.2f}, "
                f"EMA26={self.ema_26:.2f}, "
                f"Contracts={self.contracts_held}, "
                f"Allocation={allocation_pct:.1f}%, "
                f"Signal={self.signal}"
            )

        # Log signal generation with allocation info
        if self.signal != 0:
            position_value = self.contracts_held * self.close
            allocation_pct = (position_value / self.portfolio_value * 100) if self.portfolio_value > 0 else 0
            avg_entry = self.entry_price if self.contracts_held > 0 else 0
            unrealized_pnl = (self.close - avg_entry) * self.contracts_held if self.contracts_held > 0 else 0

            logger.info(
                f"Bar {self.bar_index}: Signal={self.signal}, "
                f"Confidence={self.confidence:.3f}, "
                f"Regime={self.regime}, "
                f"RSI={self.rsi:.2f}, "
                f"MACD={self.macd:.4f}, "
                f"Close={self.close:.2f}, "
                f"PV=¥{self.portfolio_value:,.2f}, "
                f"Cash=¥{self.cash:,.2f}, "
                f"Contracts={self.contracts_held}, "
                f"Allocation={allocation_pct:.1f}%, "
                f"AvgEntry={avg_entry:.2f}, "
                f"UnrealizedPnL=¥{unrealized_pnl:,.2f}"
            )

    def _initialize_state(self):
        """Initialize indicator state on first bar"""

        # Initialize EMAs
        self.ema_12 = self.close
        self.ema_26 = self.close
        self.ema_50 = self.close

        # Initialize MACD
        self.macd = 0.0
        self.macd_signal = 0.0
        self.macd_histogram = 0.0

        # Initialize RSI
        self.rsi = 50.0
        self.gain_ema = 0.0
        self.loss_ema = 0.0
        self.prev_close = self.close

        # Initialize Bollinger Bands
        self.bb_n = 1
        self.bb_mean = self.close
        self.bb_m2 = 0.0
        self.bb_variance = 0.0
        self.bb_std_dev = 0.0
        self.bb_upper = self.close
        self.bb_middle = self.close
        self.bb_lower = self.close
        self.bb_width = 0.0
        self.bb_width_pct = 0.0

        # Initialize ATR
        self.atr = self.high - self.low if self.high > self.low else 1.0
        self.mean_atr = self.atr
        self.atr_count = 1
        self.prev_close_atr = self.close

        # Initialize Volume
        self.volume_ema = self.volume

        # Initialize signals
        self.signal = 0
        self.confidence = 0.0
        self.regime = 3

        self.initialized = True

        logger.info(
            f"Initialized: close={self.close:.2f}, "
            f"volume={self.volume:.2f}, "
            f"atr={self.atr:.2f}"
        )

    def _update_emas(self, close):
        """Update triple EMA (online algorithm)"""
        self.ema_12 = self.alpha_12 * close + (1 - self.alpha_12) * self.ema_12
        self.ema_26 = self.alpha_26 * close + (1 - self.alpha_26) * self.ema_26
        self.ema_50 = self.alpha_50 * close + (1 - self.alpha_50) * self.ema_50

    def _update_macd(self):
        """Update MACD and signal line"""
        # MACD line (already have EMA 12 and 26)
        self.macd = self.ema_12 - self.ema_26

        # Signal line (9-period EMA of MACD)
        self.macd_signal = (self.alpha_9 * self.macd +
                            (1 - self.alpha_9) * self.macd_signal)

        # Histogram
        self.macd_histogram = self.macd - self.macd_signal

    def _update_rsi(self, close):
        """Update RSI (online algorithm via gain/loss EMAs)"""

        # Price change
        change = close - self.prev_close
        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        # Update gain/loss EMAs
        self.gain_ema = self.alpha_14 * gain + (1 - self.alpha_14) * self.gain_ema
        self.loss_ema = self.alpha_14 * loss + (1 - self.alpha_14) * self.loss_ema

        # Calculate RSI
        if self.loss_ema > 0:
            rs = self.gain_ema / self.loss_ema
            self.rsi = 100.0 - (100.0 / (1.0 + rs))
        else:
            self.rsi = 100.0  # No losses = max RSI

        # Update previous close for next iteration
        self.prev_close = close

    def _update_bollinger_bands(self, close):
        """Update Bollinger Bands using Welford's online variance algorithm"""

        self.bb_n += 1
        n = min(self.bb_n, 20)  # Cap at period

        # Welford's algorithm for mean and variance
        delta = close - self.bb_mean
        self.bb_mean += delta / n
        delta2 = close - self.bb_mean
        self.bb_m2 += delta * delta2

        # Calculate variance and std dev
        if n > 1:
            self.bb_variance = self.bb_m2 / (n - 1)
            self.bb_std_dev = math.sqrt(self.bb_variance)
        else:
            self.bb_variance = 0.0
            self.bb_std_dev = 0.0

        # Calculate bands
        self.bb_middle = self.bb_mean
        self.bb_upper = self.bb_mean + (2.0 * self.bb_std_dev)
        self.bb_lower = self.bb_mean - (2.0 * self.bb_std_dev)
        self.bb_width = self.bb_upper - self.bb_lower

        # Width percentage
        if self.bb_middle > 0:
            self.bb_width_pct = (self.bb_width / self.bb_middle) * 100.0
        else:
            self.bb_width_pct = 0.0

    def _update_atr(self, high, low, close):
        """Update ATR (online algorithm)"""

        # True Range
        tr1 = high - low
        tr2 = abs(high - self.prev_close_atr) if self.prev_close_atr > 0 else 0
        tr3 = abs(low - self.prev_close_atr) if self.prev_close_atr > 0 else 0
        tr = max(tr1, tr2, tr3)

        # ATR (EMA of True Range)
        self.atr = self.alpha_14 * tr + (1 - self.alpha_14) * self.atr

        # Update mean ATR (online mean)
        self.atr_count += 1
        delta = self.atr - self.mean_atr
        self.mean_atr += delta / min(self.atr_count, 100)

        # Update previous close
        self.prev_close_atr = close

    def _update_volume_ema(self, volume):
        """Update volume EMA"""
        self.volume_ema = (self.alpha_20 * volume +
                           (1 - self.alpha_20) * self.volume_ema)

    def _detect_regime(self):
        """
        Detect current market regime (1/2/3/4)

        1 = Strong Uptrend
        2 = Strong Downtrend
        3 = Sideways/Ranging
        4 = High Volatility Chaos
        """

        # 1. Check for chaos FIRST (highest priority)
        if self._is_high_volatility_chaos():
            self.regime = 4
            return

        # 2. Check for strong trends
        if self._is_strong_uptrend():
            self.regime = 1
            return

        if self._is_strong_downtrend():
            self.regime = 2
            return

        # 3. Default to ranging (everything else)
        self.regime = 3

    def _is_strong_uptrend(self):
        """Check Strong Uptrend criteria"""
        if self.mean_atr == 0:
            return False

        trend_aligned = (self.ema_12 > self.ema_26 > self.ema_50)
        momentum_bullish = (self.macd > self.macd_signal) and (self.macd_histogram > 0)
        price_above = self.close > self.ema_26
        volatility_normal = self.atr <= (self.mean_atr * 1.2)

        return trend_aligned and momentum_bullish and price_above and volatility_normal

    def _is_strong_downtrend(self):
        """Check Strong Downtrend criteria"""
        if self.mean_atr == 0:
            return False

        trend_aligned = (self.ema_12 < self.ema_26 < self.ema_50)
        momentum_bearish = (self.macd < self.macd_signal) and (self.macd_histogram < 0)
        price_below = self.close < self.ema_26
        volatility_normal = self.atr <= (self.mean_atr * 1.2)

        return trend_aligned and momentum_bearish and price_below and volatility_normal

    def _is_high_volatility_chaos(self):
        """Check High Volatility Chaos criteria"""
        if self.mean_atr == 0:
            return False

        extreme_volatility = self.atr > (self.mean_atr * 1.5)
        bb_expansion = self.bb_width_pct > 5.0

        return extreme_volatility or bb_expansion

    def _generate_signal(self):
        """
        Master signal generation logic - LONG ONLY WITH POSITION ACCUMULATION
        Sets: self.signal, self.confidence

        Signal=1: ADD 50 contracts (up to 70% portfolio limit)
        Signal=-1: CLOSE ALL positions (take profit or cut loss)
        Signal=0: HOLD current state
        """

        # Sync position_state with actual portfolio state
        if self.contracts_held > 0:
            self.position_state = 1
        else:
            self.position_state = 0

        # Calculate current allocation percentage
        current_position_value = self.contracts_held * self.close
        self.portfolio_value = self.cash + current_position_value
        current_allocation = current_position_value / self.portfolio_value if self.portfolio_value > 0 else 0

        # Calculate if we can add 50 more contracts (70% limit check)
        proposed_position_value = (self.contracts_held + self.contracts_per_trade) * self.close
        proposed_allocation = proposed_position_value / self.portfolio_value if self.portfolio_value > 0 else 0
        can_add_position = proposed_allocation <= self.max_allocation and self.cash >= (self.contracts_per_trade * self.close)

        # Priority 1: Check chaos regime (force exits if in position)
        if self.regime == 4:
            if self.position_state == 1:
                self.signal = -1
                self.confidence = 1.0
                self.last_exit_bar = self.bar_index
                return
            # If flat, allow buying if chaos is calming down
            # Fall through to check entry conditions

        # Check cooldown period (only after FULL exit to flat)
        bars_since_exit = self.bar_index - self.last_exit_bar
        in_cooldown = (bars_since_exit < self.cooldown_bars) and (self.position_state == 0)

        # Priority 2: Check EXIT conditions FIRST (any regime)
        if self.position_state == 1:
            # Check for exits in any regime
            should_exit = False

            if self.regime == 1:  # Uptrend exit
                if self._check_uptrend_exit():
                    should_exit = True

            elif self.regime == 2:  # Downtrend - aggressive exit
                if self._check_downtrend_exit():
                    should_exit = True

            elif self.regime == 3:  # Ranging exit (take profit)
                if self._check_ranging_sell():
                    should_exit = True

            if should_exit:
                self.signal = -1
                self.confidence = 0.8
                self.last_exit_bar = self.bar_index
                return

        # Priority 3: Check BUY conditions (ADD to position or START position)
        # Can buy if: (1) not in cooldown AND (2) under 70% allocation limit

        # Debug logging for blocked buys (only every 50 bars if flat)
        if self.position_state == 0 and self.bar_index % 50 == 0:
            if in_cooldown:
                logger.debug(f"Bar {self.bar_index}: Cannot buy - in cooldown (last_exit={self.last_exit_bar})")
            elif not can_add_position:
                logger.debug(f"Bar {self.bar_index}: Cannot buy - allocation limit (current={current_allocation:.1%}, proposed={proposed_allocation:.1%})")
            elif self.regime == 2:
                logger.debug(f"Bar {self.bar_index}: Cannot buy - regime 2, checking reversal signals")
            elif self.regime == 4:
                logger.debug(f"Bar {self.bar_index}: Cannot buy - regime 4, checking recovery signals")

        if not in_cooldown and can_add_position:

            if self.regime == 1:  # Strong Uptrend - buy dips
                if self._check_uptrend_buy():
                    self.signal = 1
                    # Confidence based on relaxed RSI (40 instead of 30)
                    self.confidence = max(0.0, min(1.0, (40.0 - self.rsi) / 40.0))
                    return

            elif self.regime == 3:  # Sideways/Ranging - buy dips
                if self._check_ranging_buy():
                    self.signal = 1
                    bb_range = self.bb_upper - self.bb_lower
                    if bb_range > 0:
                        distance = self.bb_middle - self.close
                        self.confidence = max(0.0, min(abs(distance) / bb_range, 1.0))
                    else:
                        self.confidence = 0.5
                    return

            # Regime 2 (Downtrend) - allow reversal buys
            elif self.regime == 2:
                # Allow re-entry in downtrend if showing reversal signs
                if self._check_downtrend_reversal_buy():
                    self.signal = 1
                    self.confidence = 0.6  # Lower confidence for downtrend buys
                    return

            # Regime 4 (Chaos) - allow buying if volatility calming down
            elif self.regime == 4:
                # Allow cautious buys when chaos is settling
                if self._check_chaos_recovery_buy():
                    self.signal = 1
                    self.confidence = 0.5  # Low confidence for chaos buys
                    return

        # Default: No signal (HOLD)
        self.signal = 0
        self.confidence = 0.0

    def _check_uptrend_buy(self):
        """Generate BUY in uptrend regime (relaxed conditions)"""
        # Score-based confirmation (need 3 out of 5 points)
        score = 0

        # 1. Trend aligned (partial alignment ok)
        if self.ema_12 > self.ema_26:
            score += 1

        # 2. Momentum bullish
        if self.macd > self.macd_signal:
            score += 1

        # 3. RSI shows pullback (relaxed from 30 to 40)
        if self.rsi < 40:
            score += 1

        # 4. Volume confirmation (relaxed from 1.5x to 1.2x)
        if self.volume > (self.volume_ema * 1.2):
            score += 1

        # 5. Price near lower band (within 20% of band width)
        bb_range = self.bb_upper - self.bb_lower
        if bb_range > 0 and self.close <= (self.bb_lower + bb_range * 0.2):
            score += 1

        return score >= 3

    def _check_uptrend_exit(self):
        """Exit long position in uptrend - take profits on weakness"""
        # Short-term focused - take profits faster (need 2 out of 4)
        exit_score = 0

        # 1. RSI overbought
        if self.rsi > 60:  # Relaxed from 65 for faster profit taking
            exit_score += 1

        # 2. MACD momentum turning down
        if self.macd < self.macd_signal:  # Bearish cross
            exit_score += 1

        # 3. Price below short-term EMA
        if self.close < self.ema_12:  # Below short-term trend
            exit_score += 1

        # 4. Price showing weakness (close in lower 40% of bar)
        if self.high > self.low:
            bar_position = (self.close - self.low) / (self.high - self.low)
            if bar_position < 0.4:  # Weak close
                exit_score += 1

        return exit_score >= 2

    def _check_downtrend_exit(self):
        """Exit long position in downtrend - close longs in bearish conditions"""
        # In downtrend, exit longs aggressively with just 1 confirmation
        exit_score = 0

        if self.ema_12 < self.ema_26:  # Bearish trend
            exit_score += 1

        if self.macd < self.macd_signal:  # Bearish momentum
            exit_score += 1

        if self.close < self.bb_middle:  # Price weakness
            exit_score += 1

        return exit_score >= 1  # Exit on any downtrend signal

    def _check_downtrend_reversal_buy(self):
        """
        Allow buys in downtrend if showing reversal signals
        Short-term focused - catch quick bounces
        """
        # Relaxed conditions - need 3 out of 6 for reversal trade
        score = 0

        # 1. EMA12 crossing above EMA26 (golden cross starting)
        if self.ema_12 > self.ema_26:  # Trend reversing
            score += 1

        # 2. MACD showing bullish momentum (crossing or above signal)
        if self.macd > self.macd_signal:  # Bullish momentum
            score += 1

        # 3. RSI oversold and recovering (under 40)
        if self.rsi < 40:  # Oversold, ready to bounce
            score += 1

        # 4. Price near or at lower BB (oversold)
        bb_range = self.bb_upper - self.bb_lower
        if bb_range > 0 and self.close <= (self.bb_lower + bb_range * 0.3):
            score += 1

        # 5. Volume confirmation (showing interest)
        if self.volume > (self.volume_ema * 1.1):
            score += 1

        # 6. Price action showing bounce (close in upper 50% of bar)
        if self.high > self.low:
            bar_position = (self.close - self.low) / (self.high - self.low)
            if bar_position > 0.5:  # Close in upper half
                score += 1

        return score >= 3  # Relaxed: need 3/6 for downtrend buy

    def _check_chaos_recovery_buy(self):
        """
        Allow buys in chaos regime if volatility is calming and showing opportunity
        Short-term scalping - catch quick moves
        """
        # Need 3 out of 5 conditions to buy in chaos
        score = 0

        # 1. Volatility decreasing (ATR trending down)
        if self.atr < self.mean_atr * 1.3:  # Still high but calming
            score += 1

        # 2. Price showing direction (EMA12 vs EMA26)
        if self.ema_12 > self.ema_26:  # Bullish bias
            score += 1

        # 3. RSI in tradable zone (not extreme)
        if 25 < self.rsi < 45:  # Slightly oversold but not extreme
            score += 1

        # 4. MACD showing momentum
        if self.macd > self.macd_signal:  # Bullish momentum
            score += 1

        # 5. Price action - close in upper part of bar
        if self.high > self.low:
            bar_position = (self.close - self.low) / (self.high - self.low)
            if bar_position > 0.6:  # Strong close
                score += 1

        return score >= 3  # Need 3/5 to buy in chaos

    def _check_ranging_buy(self):
        """Generate BUY in ranging regime (relaxed conditions)"""
        # Score-based mean reversion (need 2 out of 4 points)
        score = 0

        # 1. Near lower band (within 30% of band width)
        bb_range = self.bb_upper - self.bb_lower
        if bb_range > 0 and self.close <= (self.bb_lower + bb_range * 0.3):
            score += 1

        # 2. RSI shows oversold (relaxed from 30 to 40)
        if self.rsi < 40:
            score += 1

        # 3. Volume confirmation (relaxed from 1.2x to 1.1x)
        if self.volume > (self.volume_ema * 1.1):
            score += 1

        # 4. Price showing bounce potential
        if self.close > self.low:
            score += 1

        return score >= 2

    def _check_ranging_sell(self):
        """Exit long in ranging regime - take quick profits"""
        # Score-based exit (need 2 out of 4 for faster profit taking)
        score = 0

        # 1. Price near upper band (within 30% - relaxed for faster exits)
        bb_range = self.bb_upper - self.bb_lower
        if bb_range > 0 and self.close >= (self.bb_upper - bb_range * 0.3):
            score += 1

        # 2. RSI overbought (relaxed threshold)
        if self.rsi > 60:  # Relaxed from 65
            score += 1

        # 3. MACD turning down
        if self.macd < self.macd_signal:
            score += 1

        # 4. Price action showing weakness
        if self.high > self.low:
            bar_position = (self.close - self.low) / (self.high - self.low)
            if bar_position < 0.5:  # Close below midpoint
                score += 1

        return score >= 2  # Relaxed: need 2/4 to exit faster

    def _update_portfolio(self):
        """
        Update portfolio value based on current signal and position.
        Supports position accumulation up to 70% of portfolio.
        """

        # Calculate current position value
        if self.contracts_held > 0:
            position_value = self.contracts_held * self.close
        else:
            position_value = 0.0

        # Process signal to update portfolio
        if self.signal == 1:
            # BUY signal - ADD to position (50 contracts)
            # Check if we have enough cash and allocation room
            cost = self.contracts_per_trade * self.close
            if self.cash >= cost:
                # Calculate new average entry price
                total_cost_before = self.contracts_held * self.entry_price
                new_cost = self.contracts_per_trade * self.close
                new_contracts_total = self.contracts_held + self.contracts_per_trade

                if new_contracts_total > 0:
                    self.entry_price = (total_cost_before + new_cost) / new_contracts_total

                # Add contracts and deduct cash
                self.contracts_held += self.contracts_per_trade
                self.cash -= cost

        elif self.signal == -1 and self.contracts_held > 0:
            # SELL signal - CLOSE ALL positions (take profit or cut loss)
            self.cash += self.contracts_held * self.close
            self.contracts_held = 0
            self.entry_price = 0.0

        # Calculate final portfolio value
        if self.contracts_held > 0:
            position_value = self.contracts_held * self.close
        else:
            position_value = 0.0

        self.portfolio_value = self.cash + position_value

    def ready_to_serialize(self) -> bool:
        """Determine if state should be serialized"""
        return self.bar_index > 0 and self.initialized


# Global instance
indicator = IronOreIndicator()


# Framework callbacks (REQUIRED)

async def on_init():
    """Initialize indicator with metadata schemas"""
    global indicator, imports, metas, worker_no
    if worker_no != 0 and metas and imports:
        indicator.initialize(imports, metas)
        logger.info("IronOreIndicatorRelaxed initialized")


async def on_bar(bar: pc.StructValue):
    """Process incoming bars"""
    global indicator, worker_no
    if worker_no != 1:
        return []
    return indicator.on_bar(bar)


async def on_ready():
    """Called when framework is ready"""
    logger.info("IronOreIndicatorRelaxed ready")


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
