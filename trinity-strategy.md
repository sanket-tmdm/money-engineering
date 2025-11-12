## 🚢 WOS Addendum: The "Trinity" Adaptive Strategy

**Document ID:** TRINITY-DS-V1.0
**Date:** 2025-11-10
**Status:** DESIGN
**Purpose:** This document specifies the strategy, goals, architecture, and implementation plan for a "universal" adaptive trading system, built in accordance with the WOS (Wolverine Operating System) documentation.

-----

## 1\. Goal & Philosophy (The "Why")

### 1.1. The Goal

Our aim is to build a **"glass box"**—a **transparent, modular, and adaptive** system, not a complex "black box" prone to overfitting. It is designed to remain robust across diverse market conditions by adapting its core strategy.

### 1.2. The Philosophy: The "Captain's Playbook"

The system operates using the "Captain's Playbook" analogy:

1.  **Identify the "Pitch"** (Market Regime): Is it a **"Tricky Pitch"** (Ranging/Choppy) or a **"Flat Pitch"** (Trending/Directional)?
2.  **Switch the Playbook:** Execute the correct strategy (Mean-Reversion for Ranging, Trend-Following for Trending).

### 1.3. The WOS Architecture

The "Trinity" system maps perfectly to the WOS three-tier architecture:

  * **Tier 1: The "Scouts"** (The Indicators) - Three independent, simple indicators reporting a single truth.
  * **Tier 2: The "Captain"** (The Brain) - A single Composite Strategy that receives Scout reports, identifies the regime, and selects the playbook.
  * **Tier 3: The "Players"** (The Execution) - Outputs a final unified signal (Buy, Sell, Hold) for execution.

-----

## 2\. System Architecture (The "What")

The following diagram illustrates the high-level data flow, which utilizes the WOS Framework Data Bus to connect the components.

| Component | WOS Class | Purpose (The "Question") | Key Output Fields |
| :--- | :--- | :--- | :--- |
| **WOS\_TrendScout** | pcts3.sv\_object | "Is the pitch Tricky or Flat?" (Regime) | adx\_value, di\_plus, di\_minus |
| **WOS\_TensionScout** | pcts3.sv\_object | "Is the batsman stretched?" (Tension) | upper\_band, middle\_band, lower\_band |
| **WOS\_CrowdScout** | pcts3.sv\_object | "Is the crowd roaring?" (Conviction) | conviction\_oscillator |
| **WOS\_CaptainStrategy** | csc3.composite\_strategy | "Which play do we run?" (The Brain) | final\_signal |

-----

## 3\. Tier-1 "Scout" Implementation Plan

All scouts will be **stateless and WOS-compliant** by using **online algorithms** (EMAs, Welford's Algorithm) to ensure $O(1)$ memory usage [WOS 05: Stateless Design].

### 3.1. Scout 1: WOS\_TrendScout (The "Pitch Report")

  * **Purpose:** Measures the **strength and direction** of the market trend.
  * **Core Math:** **Average Directional Index (ADX)** and Directional Movement Indicators ($DI+$ and $DI-$).
  * **Implementation Note:** Uses a series of EMAs for True Range, $+DM$, and $-DM$ to remain stateless.

### 3.2. Scout 2: WOS\_TensionScout (The "Batsman's Form")

  * **Purpose:** Measures **price volatility** and identifies "stretched" (overbought/oversold) conditions.
  * **Core Math:** **Stateless Bollinger Bands**.
  * **Implementation Note:**
      * Middle Band is a 20-period **EMA**.
      * Standard Deviation uses **Welford's Algorithm (Online Variance)** with EMA decay to ensure statelessness, correcting the standard, stateful implementation.
      * Upper/Lower Bands = $Middle\_Band \pm (2 \times Online\_Std\_Dev)$.

### 3.3. Scout 3: WOS\_CrowdScout (The "Crowd Noise")

  * **Purpose:** Measures market **"conviction"** by comparing price action to volume.
  * **Core Math:** A **Volume-Weighted Moving Average (VWMA) Oscillator**.
  * **Implementation Note:**
      * $Conviction\_Oscillator = VWMA_{10} - EMA_{10}$ of the close price.
      * The VWMA is calculated as a ratio of the EMA of ($Price \times Volume$) to the EMA of $Volume$.
      * **Output:** $> 0$ for Bullish Conviction, $< 0$ for Bearish Conviction.

-----

## 4\. Tier-2 "Captain" Implementation Plan

The `WOS_CaptainStrategy` is the "brain" that runs the adaptive algorithm.

### Algorithm (Pseudocode Logic)

```
# --- Parameters (to be tuned) ---
ADX_RIVER_THRESHOLD = 25  # Strong Trend
ADX_LAKE_THRESHOLD = 20   # Choppy/Ranging
CONVICTION_THRESHOLD = 0.0

# --- 3. The "Captain's" Decision (The Regime Switch) ---

# PLAYBOOK 1: "Flat Pitch" / TRENDING Market
if trend_report.adx_value > ADX_RIVER_THRESHOLD:
    # Only trade WITH the strong trend, confirmed by conviction

    # UPTREND: di_plus > di_minus
    if trend_report.di_plus > trend_report.di_minus and crowd_report.conviction_oscillator > CONVICTION_THRESHOLD:
        final_signal = 1 # BUY
            
    # DOWNTREND: di_minus > di_plus
    elif trend_report.di_minus > trend_report.di_plus and crowd_report.conviction_oscillator < CONVICTION_THRESHOLD:
        final_signal = -1 # SELL

# PLAYBOOK 2: "Tricky Pitch" / RANGING Market
elif trend_report.adx_value < ADX_LAKE_THRESHOLD:
    # Only play "buy low, sell high" (Mean-Reversion)

    # Stretched Low (Buy): Price < lower_band, confirmed by conviction
    if price < tension_report.lower_band and crowd_report.conviction_oscillator > CONVICTION_THRESHOLD:
        final_signal = 1 # BUY
            
    # Stretched High (Sell): Price > upper_band, confirmed by conviction
    elif price > tension_report.upper_band and crowd_report.conviction_oscillator < CONVICTION_THRESHOLD:
        final_signal = -1 # SELL

# "DEAD ZONE": ADX is between 20 and 25
else:
    # Uncertain pitch, avoids "whipsaw" losses
    final_signal = 0 # HOLD

# --- 4. Set Final Signal ---
self.final_signal = final_signal
```

-----

## 5\. Validation & Testing Plan (The "Proof")

The system will be tested on three instruments with distinct personalities: **Iron Ore** (Trending), **Copper** (Ranging), and **Crude Oil** (Wild Card).

### 5.2. Phase 1: Scout Validation (Tier-1)

Each scout is built and validated independently using `calculator3_test.py` and visualized via `svr3.sv_reader`.

  * **Goal:** Visually confirm the **`WOS_TrendScout`'s `adx_value` is LOW during choppy (ranging) price action and HIGH during strong directional (trending) price action.**

### 5.3. Phase 2: "Captain" Validation (Tier-2)

The `WOS_CaptainStrategy` is tested using a multi-panel "Game Tape" dashboard for full transparency:

  * **Panel 1:** Price with **`WOS_TensionScout`** bands.
  * **Panel 2:** **`WOS_TrendScout`** (ADX) report.
  * **Panel 3:** **`WOS_CrowdScout`** (Oscillator) report.
  * **Panel 4:** The **`WOS_CaptainStrategy`'s `final_signal`** (plotted as Buy/Sell arrows).

### 5.4. Phase 3: Iteration & How This Makes Money

By reviewing the "Game Tape," we ensure that:

  * **In a Ranging Market (ADX Low):** Trades are generated when price hits the bands (**Playbook 2**), confirmed by conviction.
  * **In a Trending Market (ADX High):** Trades are generated *only* in the direction of the trend (**Playbook 1**), confirmed by conviction. Critically, the system will **avoid** mean-reversion trades (e.g., selling at the upper band) during a strong trend.
    This visualization-driven feedback loop is essential for parameter tuning [WOS 11: Fine-tune and Iterate].