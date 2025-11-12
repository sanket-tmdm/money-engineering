Here is the comprehensive plan.

### Document: Trinity Strategy Implementation Plan

**Phase:** 1.5 (Optimization) & 2.0 (Signal Generation)
**Status:** Pending
**Date:** 2025-11-12

-----

### 1\. What We Have Achieved (Phase 1: Complete)

You have successfully completed the most critical part of the project: **Phase 1 (Scout Development)**.

1.  **Three Tier-1 "Scouts" Built:** You have successfully built, compiled, and run three independent Tier-1 indicators (Trend, Tension, Crowd) as defined in our `TRINITY_STRATEGY.md` document [WOS 07: Tier 1 Indicator].
2.  **Full 1-Year Backtest:** You have run these scouts over a *full year* of data (2024-2025) for your three test instruments: Iron Ore (`i<00>`), Copper (`cu<00>`), and Crude Oil (`sc<00>`) [WOS 06: Backtest].
3.  **Data Generation:** The logs (`[INFO] Serializing bar...`) confirm that the framework has successfully run all scouts and saved their "reports" (the raw `adx_value`, `bb_mid`, `conviction_oscillator`, etc.) to the database for every 5-minute bar.
4.  **Visual Validation:** The 1-year 3-panel charts (`image_9f7676.png`, `image_9f7939.png`, `image_9f7957.png`) serve as our "game tape." They *prove* our scouts are working and seeing the market correctly. For example, the `ADX` (Panel 2) on the Iron Ore chart is consistently high, proving it's a "Trending" market, while the Copper chart shows a "Ranging" market.

You are no longer "blind." You now possess a 1-year "data mine" of expert analysis for three different market personalities.

-----

### 2\. The Next Step (Phase 1.5: Parameter Optimization)

You are **not** ready to move to Phase 2 (building the "Brain") yet.

**Why?** Because we haven't created the "Playbook" for the "Brain" to read. Your key insight was correct: **parameter optimization *must* be different for different instruments.**

A "dumb" Fund Manager would use the same rule for Iron Ore and Copper. A "smart" one knows Iron Ore's "Trending" threshold is different from Copper's.

**How?** You are also correct: we do not need the *line graphs* for this. We need the **raw values** you just generated. We will now analyze that 1-year data mine to find the *statistically optimal* parameters for each instrument.

#### **Your Detailed Optimization Plan:**

This is a **data analysis** step, not a framework-building step.

1.  **Write a *New* Analysis Script (e.g., `tune_parameters.py`):**

      * **How:** This script will use `svr3.sv_reader` [WOS 10: Visualization] to fetch the *full 1-year* of raw "scout reports" for *all three* of your scouts and *all three* of your instruments. You'll be fetching the `adx_value`, `di_plus`, `di_minus`, `upper_band`, `lower_band`, `middle_band`, and `conviction_oscillator` fields.
      * **Why:** The logs are just samples. We need the *entire dataset* (thousands of bars) that the framework serialized.

2.  **Load Data into `pandas`:**

      * **How:** Load the fetched `List[Dict]` into three separate `pandas` DataFrames: one for `i<00>`, one for `cu<00>`, and one for `sc<00>`.
      * **Why:** This creates a "tuning lab" where we can analyze each instrument's unique personality.

3.  **Perform Statistical Tuning (For *Each* Instrument):**

      * You will now perform the analysis shown in your statistical charts (histograms) to find the optimal cutoffs [WOS 11: Fine-tune and Iterate].

      * **Example: Analyzing `i<00>` (Iron Ore):**

          * **Tune `ADX_THRESHOLDS`:**
              * **How:** `adx_col = df['adx_value']`. Calculate the *percentiles*.
              * `river_threshold = adx_col.quantile(0.70)` (Finds the value for the 70th percentile)
              * `lake_threshold = adx_col.quantile(0.30)` (Finds the value for the 30th percentile)
              * **Result:** You might find for Iron Ore, the "Trending" (`river_threshold`) value is **30** and the "Ranging" (`lake_threshold`) value is **22**.
          * **Tune `CONVICTION_THRESHOLD`:**
              * **How:** `conv_col = df['conviction_oscillator']`. This data is packed around 0. We only want the *strong* moves.
              * `bull_conviction = conv_col.quantile(0.80)` (Finds the 80th percentile, e.g., `+1.5`)
              * `bear_conviction = conv_col.quantile(0.20)` (Finds the 20th percentile, e.g., `-1.0`)
              * **Result:** Your rule for Iron Ore is now "Only trust a signal if conviction is *above 1.5* or *below -1.0*."

      * **Example: Analyzing `cu<00>` (Copper):**

          * **Tune `ADX_THRESHOLDS`:**
              * **How:** Repeat the process. Because Copper is a "Ranging" market, you'll find its percentiles are much lower.
              * **Result:** You might find the "Trending" (`river_threshold`) value is **22** and the "Ranging" (`lake_threshold`) value is **17**.
          * **Tune `CONVICTION_THRESHOLD`:**
              * **How:** Repeat the process. You might find its thresholds are `+0.4` and `-0.3`.

4.  **Create the "Playbook":**

      * **How:** At the end of this analysis, you will have a simple Python `dict`. This is your "Playbook."
      * ```python
        # THIS IS THE "PLAYBOOK" WE WILL GIVE TO OUR TIER-2
        PLAYBOOK = {
            'i<00>': {
                'river': 30, 'lake': 22,
                'conv_bull': 1.5, 'conv_bear': -1.0
            },
            'cu<00>': {
                'river': 22, 'lake': 17,
                'conv_bull': 0.4, 'conv_bear': -0.3
            },
            'sc<00>': {
                'river': 25, 'lake': 20, # Default values
                'conv_bull': 1.0, 'conv_bear': -0.8
            }
        }
        ```

-----

### 3\. What To Do Next (Phase 2: Generate Signals)

You are now 100% ready to **build the "Fund Manager" (Tier-2 "Brain")** [WOS 08: Tier 2 Composite].

  * **How:** You will create a *new* Tier-2 project (`WOS_CaptainStrategy`).

      * Its `uin.json` will import your three Tier-1 "Scouts" (`WOS_TrendScout`, `WOS_TensionScout`, `WOS_CrowdScout`) [WOS 02: uin-and-uout.md].
      * Its `WOS_CaptainStrategy.py` file will import the `PLAYBOOK` `dict` you just created.

  * **Why:** This "Fund Manager" will finally *generate the signals*.

  * **The Logic (Inside `on_bar`):**

    1.  It receives the `adx_value`, `upper_band`, `conviction_oscillator`, and `price` reports from the Tier-1 scouts.
    2.  It checks the instrument: "This is for `cu<00>`."
    3.  It looks up the rules: `rules = PLAYBOOK['cu<00>']`.
    4.  It runs the "Trending vs. Ranging" logic *using these custom-tuned rules* (e.g., `if adx_value > rules['river']:`).
    5.  It outputs a `final_signal` (1, 0, or -1).

  * **This completes Phase 2.** You will then have a *new* set of data: the *final trading signals* for every instrument, optimized for that instrument's unique personality.

  * **The Final Step (Phase 3: Basket Management):**

      * You are *already* doing this. A Tier-2 `composite_strategy` [WOS 08] is *natively* a basket manager. By running this logic, it will automatically manage a "basket" of all three instruments, applying the correct, unique playbook to each one in parallel.