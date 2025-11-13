#!/usr/bin/env python3
# coding=utf-8
"""
WOS Captain Strategy - Trinity Phase 2
Regime-adaptive fund manager aggregating Tier-1 Scout signals.

Implements the "Trinity" three-regime trading system:
- RIVER MODE (Trending): Trend-following, hold overnight for big moves
- LAKE MODE (Ranging): Mean-reversion, INTRADAY ONLY to avoid gap risk
- DEAD ZONE: No trading, avoid whipsaws

Architecture:
- 12 baskets (one per commodity)
- Risk parity position sizing
- Portfolio and per-basket drawdown limits
- Dual parsers: SampleQuote (OHLCV) + ScoutParser (Tier-1 indicators)
"""

import composite_strategyc3 as csc3
import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3
from trinity_playbook import TRINITY_PLAYBOOK

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

# Configuration
BASKET_COUNT = 12
INITIAL_CASH = 10000000.0

# Risk Management Parameters
PORTFOLIO_DD_REDUCE = 0.10   # -10%: reduce size 50%
PORTFOLIO_DD_FLATTEN = 0.20  # -20%: flatten all
BASKET_DD_CLOSE = 0.15       # -15%: close basket


class SampleQuote(pcts3.sv_object):
    """OHLCV data parser (global namespace)"""

    def __init__(self):
        super().__init__()
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # OHLCV fields
        self.open = 0.0
        self.high = 0.0
        self.low = 0.0
        self.close = 0.0
        self.volume = 0.0
        self.turnover = 0.0


class ScoutParser(pcts3.sv_object):
    """Trinity Scout data parser (private namespace)"""

    def __init__(self):
        super().__init__()
        self.meta_name = "TrinityStrategy"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # Framework required field (must match export)
        self._preserved_field = 0

        # Scout outputs from Phase 1
        self.bar_index = 0
        self.adx_value = 0.0
        self.di_plus = 0.0
        self.di_minus = 0.0
        self.upper_band = 0.0
        self.middle_band = 0.0
        self.lower_band = 0.0
        self.conviction_oscillator = 0.0


class TrinityCaptain(csc3.composite_strategy):
    """Fund manager with regime-adaptive trading"""

    def __init__(self):
        # Initialize critical attributes FIRST (before super().__init__)
        self.bar_index_this_run = -1
        self.latest_sv = None

        # Commodity mapping (12 instruments)
        COMMODITIES = {
            b'DCE': [b'i', b'j', b'm', b'y'],
            b'SHFE': [b'cu', b'sc', b'al', b'rb', b'au', b'ru'],
            b'CZCE': [b'TA', b'MA']
        }

        # Create bidirectional mapping
        self.commodity_to_basket = {}
        self.basket_to_commodity = {}
        idx = 0
        for market, codes in COMMODITIES.items():
            for code in codes:
                self.commodity_to_basket[(market, code)] = idx
                self.basket_to_commodity[idx] = (market, code)
                idx += 1

        # Create parsers for each commodity
        self.quote_parsers = {}
        self.scout_parsers = {}
        for market, codes in COMMODITIES.items():
            for code in codes:
                key = (market, code)

                # Quote parser (OHLCV)
                qp = SampleQuote()
                qp.market = market
                # code set dynamically from bar
                self.quote_parsers[key] = qp

                # Scout parser (Tier-1 indicators)
                sp = ScoutParser()
                sp.market = market
                # code set dynamically from bar
                self.scout_parsers[key] = sp

        # Current data storage (accumulated during cycle)
        self.current_prices = {}
        self.current_scouts = {}

        # Initialize composite strategy with 12 baskets
        super().__init__(INITIAL_CASH, BASKET_COUNT)

        # Metadata
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'COMPOSITE'
        self.meta_name = "TrinityCaptain"
        self.revision = (1 << 32) - 1
        self.timetag_ = None

        # Output fields (exported via captain_uout.json)
        self.bar_index = 0
        self.active_positions = 0
        self.river_trades = 0
        self.lake_trades = 0
        self.dead_zone_count = 0
        self.peak_nv = INITIAL_CASH
        self.drawdown = 0.0
        self.portfolio_dd_events = 0
        self.basket_dd_events = 0

        # Basket peak tracking for per-basket DD limits
        self.basket_peaks = [INITIAL_CASH / BASKET_COUNT] * BASKET_COUNT

        # Allocate baskets (MANDATORY for market data routing)
        for basket_idx in range(BASKET_COUNT):
            market, code = self.basket_to_commodity[basket_idx]
            basket_capital = INITIAL_CASH / BASKET_COUNT
            # _allocate() creates basket structure
            # on_reference() will populate target_instrument later
            self._allocate(basket_idx, market, code + b'<00>', basket_capital, 1.0)

        logger.info(f"Initialized {BASKET_COUNT} baskets, capital per basket: {INITIAL_CASH/BASKET_COUNT:.2f}")

    def on_bar(self, bar: pc.StructValue):
        """Main bar processing - routes data and detects cycle boundaries"""

        market = bar.get_market()
        code = bar.get_stock_code()
        tm = bar.get_time_tag()
        ns = bar.get_namespace()
        meta_id = bar.get_meta_id()

        # Initialize timetag on first bar
        if self.timetag is None:
            self.timetag = tm

        # Cycle boundary detection: new timestamp arrived
        if self.timetag < tm:
            # Process previous cycle
            self._on_cycle_pass(tm)

            # Serialize output
            results = []
            if self.bar_index > 0:
                results.append(self.sv_copy())

            # Advance to new cycle
            self.timetag = tm
            self.bar_index += 1

            return results

        # Extract commodity code
        commodity = self.calc_commodity(code)
        key = (market, commodity)

        # Parse incoming data based on namespace
        if ns == pc.namespace_global:
            # Parse OHLCV data (SampleQuote)
            if key in self.quote_parsers:
                parser = self.quote_parsers[key]
                if meta_id == parser.meta_id:
                    parser.code = bar.get_stock_code()
                    parser.granularity = bar.get_granularity()
                    parser.from_sv(bar)
                    self.current_prices[key] = parser.close

        elif ns == pc.namespace_private:
            # Parse Scout data (TrinityStrategy)
            if key in self.scout_parsers:
                parser = self.scout_parsers[key]
                if meta_id == parser.meta_id:
                    parser.code = bar.get_stock_code()
                    parser.granularity = bar.get_granularity()
                    parser.from_sv(bar)
                    self.current_scouts[key] = parser

        # CRITICAL: Forward to baskets for market data routing
        # This allows baskets to receive their OHLCV data and update basket.price
        super().on_bar(bar)

        return []

    def _on_cycle_pass(self, time_tag):
        """Process end of cycle - generate trading signals"""

        # Call parent to update baskets
        super()._on_cycle_pass(time_tag)

        # Process trading signals for each basket
        for basket_idx in range(BASKET_COUNT):
            self._process_basket_signal(basket_idx, time_tag)

        # Update portfolio metrics
        self.active_positions = sum(1 for s in self.strategies if s.signal != 0)

        # Update peak and drawdown
        if self.nv > self.peak_nv:
            self.peak_nv = self.nv
        self.drawdown = (self.peak_nv - self.nv) / self.peak_nv if self.peak_nv > 0 else 0.0

        # Apply portfolio-level drawdown limits
        self._apply_portfolio_dd_limits()

        # Sync state (save to framework)
        self._save()
        self._sync()

        # Log progress
        logger.info(f"Bar {self.bar_index}: NV={self.nv:.4f}, PV={self.pv:.2f}, "
                   f"Active={self.active_positions}, DD={self.drawdown:.2%}")

    def _process_basket_signal(self, basket_idx, time_tag):
        """
        Process trading signal for one basket using Trinity regime logic.

        Regime Logic:
        - RIVER (ADX > river_threshold): Trend-following, hold overnight
        - LAKE (ADX < lake_threshold): Mean-reversion, INTRADAY ONLY
        - DEAD ZONE (between): No trading, avoid whipsaws
        """

        basket = self.strategies[basket_idx]
        market, commodity = self.basket_to_commodity[basket_idx]
        code_bytes = commodity + b'<00>'
        key = (market, commodity)

        # Need both price and scout data
        if key not in self.current_prices or key not in self.current_scouts:
            return

        price = self.current_prices[key]
        scout = self.current_scouts[key]

        # Get playbook rules for this commodity
        if code_bytes not in TRINITY_PLAYBOOK:
            logger.info(f"No playbook for {code_bytes.decode()}")
            return

        rules = TRINITY_PLAYBOOK[code_bytes]

        # Determine regime and generate signal
        signal = 0
        regime = "DEAD"

        # ===== RIVER MODE (Trending Market) =====
        # Logic: Trend is king. Hold overnight to catch big moves.
        if scout.adx_value > rules['river']:
            regime = "RIVER"

            # Bullish trend: DI+ dominant AND volume conviction positive
            if scout.di_plus > scout.di_minus and scout.conviction_oscillator > rules['bull']:
                signal = 1  # Long

            # Bearish trend: DI- dominant AND volume conviction negative
            elif scout.di_minus > scout.di_plus and scout.conviction_oscillator < rules['bear']:
                signal = -1  # Short

        # ===== LAKE MODE (Ranging Market) =====
        # Logic: Buy dips, sell rips. STRICT INTRADAY - no overnight risk.
        elif scout.adx_value < rules['lake']:
            regime = "LAKE"

            # Mean-reversion long: Price at lower band AND volume supports
            if price <= scout.lower_band and scout.conviction_oscillator > rules['bull']:
                signal = 1  # Buy dip

            # Mean-reversion short: Price at upper band AND volume supports
            elif price >= scout.upper_band and scout.conviction_oscillator < rules['bear']:
                signal = -1  # Sell rip

            # *** THE SAFETY NET: INTRADAY-ONLY EXIT ***
            # If near session close, FORCE EXIT all Lake positions
            # Prevents overnight gap risk in ranging markets
            if self._is_market_closing_soon(time_tag, market):
                signal = 0  # Flatten

        # ===== DEAD ZONE (ADX between thresholds) =====
        # Logic: Market indecisive. Stay flat to avoid whipsaws.
        else:
            regime = "DEAD"
            signal = 0  # No trading

        # Track regime statistics
        if regime == "RIVER" and signal != 0:
            self.river_trades += 1
        elif regime == "LAKE" and signal != 0:
            self.lake_trades += 1
        elif regime == "DEAD":
            self.dead_zone_count += 1

        # Execute if signal changed
        if signal != basket.signal:
            self._execute_basket_signal(basket_idx, signal, rules, regime, code_bytes)

        # Check basket drawdown limit
        self._check_basket_dd(basket_idx)

    def _execute_basket_signal(self, basket_idx, signal, rules, regime, code_bytes):
        """Execute signal for basket with risk parity sizing"""

        basket = self.strategies[basket_idx]
        leverage = rules['size']  # Risk parity: normalized by volatility

        if signal == 0:
            # Close position
            logger.info(f"CLOSE basket {basket_idx} ({code_bytes.decode()}): {regime}")
            basket._signal(basket.price, basket.timetag, 0)
        else:
            # Open/reverse position
            direction = "LONG" if signal == 1 else "SHORT"
            logger.info(f"{direction} basket {basket_idx} ({code_bytes.decode()}): "
                       f"{regime}, leverage={leverage:.2f}")

            # Adjust position size (risk parity)
            basket._fit_position(leverage)

            # Execute signal
            basket._signal(basket.price, basket.timetag, signal)

    def _is_market_closing_soon(self, timetag, market):
        """
        Check if we're near session close.

        Returns True if within 10 minutes of close for any session:
        - Day session: 14:50-15:00
        - Night session: 23:50-00:00
        - Early morning: 00:50-01:00

        Used to force exit Lake mode positions (intraday only).
        """

        s_time = str(timetag)
        if len(s_time) < 14:
            return False

        hhmm = int(s_time[8:12])

        # Day session close (14:50-15:00)
        # Most Chinese futures close at 15:00
        if 1450 <= hhmm < 1500:
            return True

        # Night session close (23:50-00:00)
        # SHFE/DCE night session closes at 23:00 for some commodities
        if 2350 <= hhmm <= 2359:
            return True

        # Early morning close (00:50-01:00)
        # Some commodities trade until 01:00
        if 50 <= hhmm <= 100:
            return True

        return False

    def _apply_portfolio_dd_limits(self):
        """
        Apply portfolio-level drawdown limits.

        Two-tier system:
        - Level 1 (-10% DD): Reduce all position sizes by 50%
        - Level 2 (-20% DD): Flatten all positions (risk-off mode)
        """

        if self.drawdown > PORTFOLIO_DD_FLATTEN:
            # Level 2: Flatten all
            logger.info(f"[ALERT] Portfolio DD {self.drawdown:.2%} > {PORTFOLIO_DD_FLATTEN:.0%}: FLATTENING ALL")
            for basket in self.strategies:
                if basket.signal != 0:
                    basket._signal(basket.price, basket.timetag, 0)
            self.portfolio_dd_events += 1

        elif self.drawdown > PORTFOLIO_DD_REDUCE:
            # Level 1: Reduce size
            logger.info(f"[WARNING] Portfolio DD {self.drawdown:.2%} > {PORTFOLIO_DD_REDUCE:.0%}: REDUCING SIZE 50%")
            for basket in self.strategies:
                if basket.signal != 0:
                    basket._fit_position(basket.leverage * 0.5)
            self.portfolio_dd_events += 1

    def _check_basket_dd(self, basket_idx):
        """
        Check and apply per-basket drawdown limit.

        If a single commodity loses more than 15%, close that basket.
        Isolates bad performers without affecting other baskets.
        """

        basket = self.strategies[basket_idx]

        # Update peak for this basket
        if basket.nv > self.basket_peaks[basket_idx]:
            self.basket_peaks[basket_idx] = basket.nv

        # Calculate basket drawdown
        peak = self.basket_peaks[basket_idx]
        if peak > 0:
            basket_dd = (peak - basket.nv) / peak

            # Check limit
            if basket_dd > BASKET_DD_CLOSE and basket.signal != 0:
                market, code = self.basket_to_commodity[basket_idx]
                logger.info(f"[STOP] Basket {basket_idx} ({code.decode()}) DD {basket_dd:.2%} > "
                             f"{BASKET_DD_CLOSE:.0%}: CLOSING BASKET")
                basket._signal(basket.price, basket.timetag, 0)
                self.basket_dd_events += 1


# ===== GLOBAL STRATEGY INSTANCE =====
strategy = TrinityCaptain()


# ===== FRAMEWORK CALLBACKS =====

async def on_init():
    """Initialize strategy and parsers"""
    global strategy, imports, metas, worker_no

    if worker_no != 0 and metas and imports:
        # Load strategy metadata
        strategy.load_def_from_dict(metas)

        # Load parser metadata
        for parser in strategy.quote_parsers.values():
            parser.load_def_from_dict(metas)
            parser.set_global_imports(imports)

        for parser in strategy.scout_parsers.values():
            parser.load_def_from_dict(metas)
            parser.set_global_imports(imports)


async def on_ready():
    """Framework ready callback"""
    pass


async def on_bar(bar: pc.StructValue):
    """Main bar processing callback"""
    global strategy, worker_no

    if worker_no != 1:
        return []

    return strategy.on_bar(bar)


async def on_market_open(market, tradeday, time_tag, time_string):
    """Market open callback"""
    pass


async def on_market_close(market, tradeday, timetag, timestring):
    """Market close callback"""
    pass


async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    """
    MANDATORY: Triggers contract rolling.

    Without this, baskets won't roll from i2501 -> i2505 at expiry.
    """
    global strategy
    strategy.on_tradeday_begin(bytes(market, 'utf-8'), tradeday)


async def on_tradeday_end(market, tradeday, timetag, timestring):
    """
    MANDATORY: End-of-day settlement.

    Handles EOD P&L calculations and position settlements.
    """
    global strategy
    strategy.on_tradeday_end(bytes(market, 'utf-8'), tradeday)


async def on_reference(market, tradeday, data, timetag, timestring):
    """
    CRITICAL: Forwards reference data to baskets for market data routing.

    This populates basket.target_instrument with actual contract codes (e.g., i2501).
    Without this, basket.target_instrument stays empty and baskets won't receive market data.

    This is THE MOST IMPORTANT callback for composite strategies!
    """
    global strategy
    strategy.on_reference(bytes(market, 'utf-8'), tradeday, data)


async def on_historical(params, records):
    """Historical data callback"""
    pass
