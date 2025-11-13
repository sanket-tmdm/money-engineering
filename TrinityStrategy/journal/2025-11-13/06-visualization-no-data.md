# Issue #6: Visualization Script Returns No Data

**Status**: ❓ UNRESOLVED
**Date**: November 13, 2025
**Component**: Data Retrieval / Visualization
**Severity**: HIGH - Cannot validate strategy outputs visually

---

## Problem Statement

After successfully completing the backtest, the visualization Jupyter notebook fails to retrieve any data from the server.

**Expected**: Fetch TrinityCaptain strategy outputs for the test period (Oct 25 - Nov 1, 2024)
**Actual**: "Fetched 0 bars" - no data retrieved

---

## Backtest Completion Evidence

The backtest completed successfully:

```
[2025-11-13 21:49:23.737275][vanilla_logger][][INFO]SHORT basket 7 (rb<00>): RIVER, leverage=0.44
[2025-11-13 21:49:23.737348][2024-10-31T15:00:00.0+0000] signal:-1
[2025-11-13 21:49:23.737395][2024-10-31T15:00:00.0+0000] inst=b'rb2501',acc_div=1.0,signal=-1,lev=1.0000,price=3382.0,cost=3382.0,vol=24.00,nv=0.9857,dipp=-0.01431,maxdipp=-0.01431
...
[2025-11-13 21:49:23.742242][vanilla_logger][][INFO]Bar 205: NV=0.9946, PV=9945623.91, Active=0, DD=100.00%
pid=31701, CMD_TC_FINISH_BACKTEST worker=0
ON FINISHED
pid=31916, CMD_TC_FINISH_BACKTEST worker=1
ON FINISHED
calculatorp3 acknowledged
PROCESS_IMPLODE
PROCESS_IMPLODE2 b'{"runtime":1,"category":1,"session_id":6546,"status":0,"error_code":0,"error_msg":"","next_action":2}'
__logic_on_backtest_finish_acknowledge
ON FINISHED
calculatorp3 acknowledged
calculator3 imploded
```

**Key Indicators**:
- ✅ `CMD_TC_FINISH_BACKTEST` - Backtest finished
- ✅ `status":0,"error_code":0` - No errors
- ✅ `calculator3 imploded` - Clean shutdown
- ✅ 205 bars processed successfully
- ✅ Trading signals generated and positions taken

**Conclusion**: Data WAS uploaded to the server.

---

## Visualization Script Details

**File**: `WOS_Captain_viz.ipynb`

### Cell 3: Data Fetching

```python
# Fetch TrinityCaptain data
START_DATE = 20241025000000
END_DATE = 20241101000000
COMMODITY = 'i<00>'  # Iron Ore logical contract

# Using svr3.sv_reader to fetch from server
data = fetch_strategy_data(
    strategy_name="TrinityCaptain",
    start_date=START_DATE,
    end_date=END_DATE,
    commodity=COMMODITY,
    namespace="private"
)
```

**Output**:
```
[2025-11-13 21:53:28][INFO]Connection lost
[2025-11-13 21:53:28][INFO][None]
Fetched 0 bars.
```

**Result**: No data retrieved despite successful backtest.

---

## Possible Causes

### 1. Namespace Mismatch

**Hypothesis**: TrinityCaptain exports to private namespace, but fetcher might be looking in wrong namespace.

**Evidence**:
```python
# WOS_Captain.py line 142
self.namespace = pc.namespace_private
```

**Check Needed**: Is the visualization script using the correct namespace parameter?

### 2. Strategy Name Mismatch

**Hypothesis**: Strategy registered as "TrinityCaptain" but fetch using different name.

**Verification Needed**:
- Backtest used: `--algoname TrinityCaptain`
- Class uses: `self.meta_name = "TrinityCaptain"`
- Fetch script uses: `strategy_name="TrinityCaptain"` (??)

### 3. Contract Code Format

**Hypothesis**: Data stored with monthly contracts (`i2501`) but fetch requesting logical contract (`i<00>`).

**Evidence from Issue #5**: Bars are processed with monthly contract codes, not logical codes.

**Possible Fix**:
```python
# Instead of:
COMMODITY = 'i<00>'

# Try:
COMMODITY = 'i2501'  # Or whatever monthly contract was active during test period
```

### 4. Data Export Configuration

**Hypothesis**: TrinityCaptain not actually exporting data to server.

**Check Needed**: Does `uout.json` exist for TrinityCaptain?

**File**: `Trinity_Phase-2/uout.json`

**Status**: Unknown - needs verification

**Requirement**: For data to be retrievable, strategy must:
1. Have `uout.json` defining export fields
2. Call serialization methods to upload data
3. Have `ready_to_serialize()` returning `True`

### 5. Data Retention / Cleanup

**Hypothesis**: Data uploaded but immediately deleted or not persisted.

**Check Needed**:
- Is `--is-managed 1` causing data to be cleaned up?
- Is there a data retention policy?
- Are backtest results ephemeral?

### 6. API Parameters

**Hypothesis**: Wrong API endpoint, token, or query parameters.

**Verification Needed**:
- Is the TOKEN correct in the visualization script?
- Is the RAILS endpoint correct?
- Are start/end date formats correct?
- Is granularity specified?

---

## Error Message Analysis

```
[2025-11-13 21:53:28][INFO]Connection lost
[2025-11-13 21:53:28][INFO][None]
Fetched 0 bars.
```

**"Connection lost"**: Suggests connection to server succeeded initially but then closed.

**"[None]"**: Null response, possibly indicating:
- No data found matching query
- Query succeeded but returned empty result set
- API error not being caught

**"Fetched 0 bars"**: Explicit count, means query executed but returned no results.

---

## Information Needed for Resolution

To diagnose this issue, the following information is needed:

### 1. Export Configuration

- Does `Trinity_Phase-2/uout.json` exist?
- What fields does it define?
- What namespace does it export to?

### 2. Serialization Implementation

- Does `TrinityCaptain` implement `ready_to_serialize()`?
- Does it call `copy_to_sv()` or equivalent?
- Are there logs showing serialization happening?

### 3. Fetch Script Details

- Complete code of the data fetching function
- What library/API is being used (`svr3.sv_reader`)?
- What parameters are passed?

### 4. Server-Side Verification

- Can data be queried using a different tool?
- Does the server have any data for "TrinityCaptain"?
- What contract codes are stored?
- What namespace is the data in?

### 5. Working Example Comparison

- How does Phase-1 TrinityStrategy visualization work?
- What's different between Phase-1 and Phase-2 fetch scripts?
- Can we successfully fetch Phase-1 data?

---

## Attempted Workarounds

### Attempt 1: Check Phase-1 Data

**Action**: Try fetching Phase-1 TrinityStrategy data to verify the fetch mechanism works.

```python
# Fetch TrinityStrategy (Phase-1) instead
data = fetch_strategy_data(
    strategy_name="TrinityStrategy",
    start_date=START_DATE,
    end_date=END_DATE,
    commodity='i<00>',
    namespace="private"
)
```

**Expected**: If this returns data, fetch mechanism works and issue is specific to TrinityCaptain.

### Attempt 2: Try Monthly Contract

**Action**: Use monthly contract code instead of logical.

```python
# Use monthly contract from test period
COMMODITY = 'i2501'  # October 2024 contract
```

**Expected**: If data was stored with monthly codes, this should retrieve it.

### Attempt 3: Check Global Namespace

**Action**: Try fetching from global namespace instead of private.

```python
data = fetch_strategy_data(
    strategy_name="TrinityCaptain",
    start_date=START_DATE,
    end_date=END_DATE,
    commodity='i2501',
    namespace="global"  # Instead of private
)
```

---

## Documentation Gap

**WOS Documentation Reference**: `wos/10-visualization.md`

**What's Needed**:
1. Clear guide on data export configuration for Tier-2 strategies
2. Explanation of how composite strategies store data
3. Troubleshooting section for "no data found" errors
4. Contract code format guidance for data retrieval
5. Example of fetching Tier-2 composite strategy data
6. Namespace specification for different strategy types

**Current Documentation Gaps**:
- No explicit guidance on Tier-2 data export
- Unclear how to query composite strategy data
- Missing troubleshooting for empty query results
- No contract format guidance for queries

---

## Impact

**Severity**: HIGH

**Blocked Workflows**:
- ✗ Cannot visually validate Scout indicators are being read correctly
- ✗ Cannot verify regime detection logic (RIVER vs LAKE)
- ✗ Cannot analyze per-basket performance
- ✗ Cannot generate performance plots for documentation
- ✗ Cannot debug strategy behavior visually

**Workaround**: Use log analysis from backtest output, but this is:
- Less visual
- More manual
- Harder to spot patterns
- Not suitable for presentations

---

## Recommended Next Steps

### For Immediate Resolution:

1. **Verify uout.json exists** for TrinityCaptain
2. **Compare with working visualization** (Phase-1 TrinityStrategy)
3. **Try different contract code formats** (monthly vs logical)
4. **Check server-side logs** for any data from TrinityCaptain
5. **Verify serialization** is actually happening during backtest

### For Long-Term Fix:

1. **Document Tier-2 data export pattern** in WOS docs
2. **Add visualization examples** for composite strategies
3. **Improve error messages** - "Fetched 0 bars" doesn't explain why
4. **Add validation tools** to check if data was uploaded
5. **Provide query debugging tools** to diagnose empty results

---

## Status Summary

**Current State**: UNRESOLVED
**Blocker**: Unknown data export or retrieval issue
**Workaround**: Manual log analysis
**Priority**: HIGH - visualization is essential for validation
**Owner**: Needs WOS developer investigation

---

**Next**: [summary-for-developer.md](./summary-for-developer.md)
