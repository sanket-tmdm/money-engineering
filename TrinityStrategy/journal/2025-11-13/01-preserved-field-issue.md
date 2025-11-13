# Issue #1: Incompatible Struct Value - Initial `_preserved_field` Attempt

**Status**: ❌ NOT THE ROOT CAUSE (Error persisted after fix)
**Date**: November 13, 2025
**Component**: Captain Phase-2 Import Configuration

---

## Problem Statement

When attempting to run the Captain - Quick Test, the backtest immediately failed with:

```
Exception('Incompatable struct value')
Traceback (most recent call last):
  File "/home/wolverine/bin/running/calculator3.py", line 716, in logic_loop
    await _task()
  File "/home/wolverine/bin/running/calculator3.py", line 2058, in _on_market_data
    return await self.__on_market_data_raw(msg, receiver)
  File "/home/wolverine/bin/running/calculator3.py", line 2086, in __on_market_data_raw
    _res = await receiver(_sv)
  File "/home/wolverine/bin/running/calculator3.py", line 2192, in _on_bar
    ret = await self.mod.on_bar(_bar)
  File "/workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/WOS_Captain.py", line 488, in on_bar
    return strategy.on_bar(bar)
  File "/workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/WOS_Captain.py", line 210, in on_bar
    parser.from_sv(bar)
  File "/home/wolverine/bin/running/pycaitlynts3.py", line 395, in from_sv
    raise Exception("Incompatable struct value")
```

**Error Location**: `pycaitlynts3.py` line 395 in `ScoutParser.from_sv(bar)`
**Failure Point**: Attempting to deserialize TrinityStrategy data from private namespace

---

## Initial Hypothesis

Looking at the Phase-1 `uout.json`, TrinityStrategy exports **9 fields**:

```json
{
  "private": {
    "export": {
      "XXX": {
        "fields": [
          "_preserved_field",
          "bar_index",
          "adx_value",
          "di_plus",
          "di_minus",
          "upper_band",
          "middle_band",
          "lower_band",
          "conviction_oscillator"
        ]
      }
    }
  }
}
```

However, the Phase-2 `uin.json` was only importing **8 fields** (missing `_preserved_field`):

```json
{
  "private": {
    "imports": {
      "TrinityStrategy": {
        "fields": [
          "bar_index",
          "adx_value",
          "di_plus",
          "di_minus",
          "upper_band",
          "middle_band",
          "lower_band",
          "conviction_oscillator"
        ]
      }
    }
  }
}
```

**Field Count Mismatch**: 9 exported vs 8 imported

---

## Attempted Fix #1: Add `_preserved_field` to `uin.json`

### Change 1: Updated `Trinity_Phase-2/uin.json`

**Before**:
```json
"TrinityStrategy": {
  "fields": ["bar_index", "adx_value", "di_plus", "di_minus", "upper_band", "middle_band", "lower_band", "conviction_oscillator"],
  "granularities": [900],
  "markets": ["DCE", "SHFE", "CZCE"],
  ...
}
```

**After**:
```json
"TrinityStrategy": {
  "fields": ["_preserved_field", "bar_index", "adx_value", "di_plus", "di_minus", "upper_band", "middle_band", "lower_band", "conviction_oscillator"],
  "granularities": [900],
  "markets": ["DCE", "SHFE", "CZCE"],
  ...
}
```

### Change 2: Updated `ScoutParser` class in `WOS_Captain.py`

**Before**:
```python
class ScoutParser(pcts3.sv_object):
    """Trinity Scout data parser (private namespace)"""

    def __init__(self):
        super().__init__()
        self.meta_name = "TrinityStrategy"
        self.namespace = pc.namespace_private
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # Scout outputs from Phase 1
        self.bar_index = 0
        self.adx_value = 0.0
        self.di_plus = 0.0
        self.di_minus = 0.0
        self.upper_band = 0.0
        self.middle_band = 0.0
        self.lower_band = 0.0
        self.conviction_oscillator = 0.0
```

**After**:
```python
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
```

---

## Result

**Test Command**:
```bash
python3 /home/wolverine/bin/running/calculator3_test.py \
    --testcase /workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/ \
    --algoname WOS_Captain \
    --sourcefile WOS_Captain.py \
    --start 20241025000000 \
    --end 20241101000000 \
    --granularity 900 \
    --category 1 \
    --is-managed 1 \
    --restore-length 864000000 \
    --multiproc 1
```

**Output**:
```
[2025-11-13 20:43:24.068089][vanilla_logger][][INFO]Initialized 12 baskets, capital per basket: 833333.33
...
[2025-11-13 20:43:29.416118][2024-10-24T13:15:00.0+0000][error][w1] Exception('Incompatable struct value')
...
Exception: Incompatable struct value
```

❌ **SAME ERROR - Fix did not resolve the issue**

---

## Analysis: Why This Fix Didn't Work

While the field count mismatch WAS a real issue, it wasn't the root cause of the error. The `from_sv()` validation was failing at a different check:

```python
# From pycaitlynts3.py line 387-394
def from_sv(self, sv: pc.StructValue):
    if self.meta_id != sv.get_meta_id() or\
            self.market != sv.get_market() or\
            self.code != sv.get_stock_code() or\      # ← THIS CHECK FAILED
            self.namespace != sv.get_namespace() or\
            self.granularity != sv.get_granularity():
        raise Exception("Incompatable struct value")
```

The actual error was the **contract code mismatch** (see Issue #5), not the field structure.

---

## Documentation Gap

**WOS Documentation Reference**: `wos/02-uin-and-uout.md`

The documentation doesn't clearly explain:
1. Whether `_preserved_field` should be included in import field lists
2. The relationship between export fields and import fields
3. How the framework handles `_preserved_field` internally

**Ambiguity**: Some documentation examples show `_preserved_field` in exports but not in imports, leading to confusion about whether it's required in both places.

---

## Lessons Learned

1. ✅ **Field matching IS important** - export and import field lists should match
2. ❌ **But it wasn't the root cause** - the error was actually in contract code validation
3. ⚠️ **Error messages are not specific** - "Incompatible struct value" could mean many things
4. 📝 **Documentation needs clarity** - The `_preserved_field` handling pattern should be explicit

---

**Next**: [02-category-parameter-hang.md](./02-category-parameter-hang.md)
