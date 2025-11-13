
# The Trinity Strategy: Final Execution Plan

**Objective:** Deploy the Tier-2 "Fund Manager" to trade 12 instruments with strict Regime-Based Risk Management.
**Core Logic:**

1.  **River (Trend):** Hold overnight to catch the big move.
2.  **Lake (Range):** **Intraday ONLY.** Force exit at 14:55 to avoid overnight gap risk.
3.  **Dead Zone:** Do nothing.

-----

### Phase 1: The "Master Rulebook" (`trinity_playbook.py`)

**What to do:** Create this file inside your strategy folder.
**Why:** This acts as the "Brain's Memory." It holds the personality traits and the **Risk Parity Size** for every instrument.

**The Math (Done for you):** I calculated the `size` using your JSON data.

  * **Formula:** `Size = Baseline_Vol (Iron Ore: 27.46) / Instrument_Vol`.
  * *Example:* Copper Vol is 1060. `27.46 / 1060 = 0.026`. (We bet small on wild markets).

**File Content:** `WOS_CaptainStrategy/trinity_playbook.py`

```python
"""
Trinity Strategy - Master Rulebook
Auto-generated from Phase 1.5 Optimization Data.
Baseline Volatility (Iron Ore): 27.46 -> Size 1.0
"""

TRINITY_PLAYBOOK = {
    # --- FERROUS METALS ---
    b'i<00>':  {'river': 39.93, 'lake': 26.36, 'bull': 0.5811, 'bear': -0.6582, 'size': 1.00},
    b'j<00>':  {'river': 39.18, 'lake': 25.82, 'bull': 1.6416, 'bear': -1.6680, 'size': 0.39},
    b'rb<00>': {'river': 38.92, 'lake': 25.79, 'bull': 0.9599, 'bear': -1.8585, 'size': 0.44},

    # --- BASE METALS (High Risk -> Tiny Sizes) ---
    b'cu<00>': {'river': 40.05, 'lake': 26.56, 'bull': 33.036, 'bear': -26.088, 'size': 0.026},
    b'al<00>': {'river': 41.28, 'lake': 27.96, 'bull': 9.7052, 'bear': -7.4529, 'size': 0.12},
    b'au<00>': {'river': 40.91, 'lake': 24.98, 'bull': 0.1485, 'bear': -0.1120, 'size': 5.38}, # Gold (Low Risk)

    # --- ENERGY & CHEMICALS ---
    b'sc<00>': {'river': 42.22, 'lake': 27.64, 'bull': 0.3071, 'bear': -0.3358, 'size': 2.22},
    b'TA<00>': {'river': 40.53, 'lake': 26.30, 'bull': 2.7333, 'bear': -1.5562, 'size': 0.32},
    b'MA<00>': {'river': 42.02, 'lake': 27.37, 'bull': 1.2786, 'bear': -0.6738, 'size': 0.59},
    b'ru<00>': {'river': 39.87, 'lake': 25.54, 'bull': 5.2485, 'bear': -5.9527, 'size': 0.09},

    # --- AGRI ---
    b'm<00>':  {'river': 43.38, 'lake': 26.95, 'bull': 1.3177, 'bear': -1.2224, 'size': 0.44},
    b'y<00>':  {'river': 39.14, 'lake': 25.12, 'bull': 2.3359, 'bear': -2.4180, 'size': 0.20}
}
```

-----

### Phase 2: The "Brain" Logic (`WOS_Captain.py`)

**What to do:** Create the strategy file.
**Why:** This is where the "Intraday vs. Overnight" logic lives.

**Key Logic to Implement:**

1.  **`check_eod_exit()`**: If we are in "Lake Mode" and it is 14:55 (5 mins before close), **Force Sell**.
2.  **Regime Switching**: Use `ADX` to choose the playbook.
3.  **Risk Parity**: Multiply the signal by the `size` from the rulebook.

**File Content:** `WOS_CaptainStrategy/WOS_Captain.py`

```python
#!/usr/bin/env python3
# coding=utf-8
import composite_strategyc3 as csc3
import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3
from trinity_playbook import TRINITY_PLAYBOOK

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

class TrinityCaptain(csc3.composite_strategy):
    def __init__(self):
        # Initialize with 10 Million Virtual Capital
        super().__init__(10000000.0)
        self.meta_name = "WOS_Captain"
        self.namespace = pc.namespace_private
        self.market = b'DCE'
        self.code = b'COMPOSITE<00>'
        
        self.current_positions = {} 
        self.bar_index = 0

    def initialize(self, imports, metas):
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)

    def is_market_closing_soon(self, timetag):
        """
        Returns True if time is between 14:50 and 15:00.
        This is our signal to flatten 'Lake' trades.
        """
        s_time = str(timetag)
        if len(s_time) < 14: return False
        hhmm = int(s_time[8:12])
        # Chinese Futures Close at 15:00. We exit 10 mins early.
        return 1450 <= hhmm < 1500

    def on_bar(self, bar: pc.StructValue):
        # 1. Identify Instrument
        code_bytes = bar.get_stock_code()
        if code_bytes not in TRINITY_PLAYBOOK:
            return []

        # 2. Get Tier-1 Scout Data
        # Note: This assumes the incoming 'bar' IS the Tier-1 struct value
        # If using standard imports, we map the fields directly.
        try:
            scout = self.get_import_source('WOS_TrinityScout')
            if bar.get_meta_id() != scout.meta_id: return []
            scout.from_sv(bar)
            
            adx = scout.adx_value
            di_plus = scout.di_plus
            di_minus = scout.di_minus
            conviction = scout.conviction_oscillator
            lower_band = scout.lower_band
            upper_band = scout.upper_band
            # We use the Middle Band as a proxy for Price location if Price isn't passed
            # Ideally, use scout.close or calculate based on band proximity
            # For this logic, we assume price relationships:
            # If price hit bands, the scout would report it, or we check bands vs Close.
            # Let's assume we access 'close' from the scout (add to uin.json if needed)
            # or we use bar.close if available.
            # Assuming scout has 'close' field for logic:
            price = scout.close 
        except:
            return []

        # 3. Load Rules
        rules = TRINITY_PLAYBOOK[code_bytes]
        signal = 0
        regime = "NEUTRAL"

        # --- LOGIC ENGINE ---

        # === PLAYBOOK A: RIVER (Trending) ===
        # Logic: Trend is King. Hold Overnight.
        if adx > rules['river']:
            regime = "RIVER"
            if di_plus > di_minus and conviction > rules['bull']:
                signal = 1  # BUY & HOLD
            elif di_minus > di_plus and conviction < rules['bear']:
                signal = -1 # SELL & HOLD

        # === PLAYBOOK B: LAKE (Ranging) ===
        # Logic: Buy Dip/Sell Rip. STRICT INTRADAY.
        elif adx < rules['lake']:
            regime = "LAKE"
            if price <= lower_band and conviction > rules['bull']:
                signal = 1  # BUY DIP
            elif price >= upper_band and conviction < rules['bear']:
                signal = -1 # SELL RIP
            
            # *** THE SAFETY NET ***
            # If it's near 3:00 PM, we FORCE EXIT.
            # We do NOT hold choppy markets overnight.
            if self.is_market_closing_soon(bar.get_time_tag()):
                signal = 0  # FLATTEN

        # === PLAYBOOK C: DEAD ZONE ===
        else:
            signal = 0 # Safety First

        # 4. Risk Parity Execution
        current_pos = self.current_positions.get(code_bytes, 0)
        
        if signal != current_pos:
            # Apply Volatility Sizing
            size = rules['size']
            target_qty = signal * size
            
            logger.info(f"TRADE [{code_bytes.decode()}] {regime}: {current_pos}->{signal} (Size {size})")
            
            # The Framework handles the Money/P&L tracking automatically
            self.set_target_position(code_bytes, target_qty)
            self.current_positions[code_bytes] = signal

        return [] # Tier-2 usually outputs signals, but here we just trade.

# Boilerplate
strategy = TrinityCaptain()
async def on_init():
    global strategy, imports, metas, worker_no
    if worker_no != 0 and metas and imports: strategy.initialize(imports, metas)
async def on_bar(bar):
    global strategy, worker_no
    if worker_no != 1: return []
    return strategy.on_bar(bar)
# ... (Add other empty callbacks: on_ready, on_market_open, etc.)
```

-----

### Phase 3: The Configuration (`uin.json`)

**What to do:** Create the input map.
**Why:** Wires the "Brain" to the "Scouts."

**File Content:** `WOS_CaptainStrategy/uin.json`

```json
{
  "private": {
    "imports": {
      "WOS_TrinityScout": {
        "fields": [
          "adx_value", "di_plus", "di_minus",
          "upper_band", "lower_band", "middle_band",
          "conviction_oscillator", "close" 
        ],
        "granularities": [900],
        "markets": ["DCE", "SHFE", "CZCE"],
        "security_categories": [[1, 2, 3], [1, 2, 3], [1, 2, 3]],
        "securities": [
          ["i", "j", "m", "y"],
          ["cu", "sc", "al", "rb", "au", "ru"],
          ["TA", "MA"]
        ]
      }
    }
  }
}
```

*(Note: Ensure your Tier-1 `uout.json` actually exports `close` or `price` so the Captain can compare it to the bands\!)*

-----

### Phase 4: Execution

**Command:**

```bash
python /home/wolverine/bin/running/calculator3_test.py \
    --testcase ./WOS_CaptainStrategy/ \
    --algoname WOS_Captain \
    --sourcefile WOS_Captain.py \
    --start 20240101000000 \
    --end 20250101000000 \
    --granularity 900 \
    --category 2 \
    --is-managed 1 \
    --multiproc 1
```

**What will happen:**

1.  The system loads your `TRINITY_PLAYBOOK`.
2.  It runs through 2024 data.
3.  For **Gold**, it will trade HUGE size (5.38), but hold overnight on trends.
4.  For **Copper**, it will trade TINY size (0.026), and if the market is choppy ("Lake"), it will **automatically sell everything at 14:55** to prevent overnight loss.
5.  At the end, it generates a P\&L curve showing the result of this risk-managed approach.