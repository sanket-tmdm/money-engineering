# Issue #3: Missing `revision` Field in Import Configuration

**Status**: ⚠️ PARTIAL FIX (Added but not root cause)
**Date**: November 13, 2025
**Component**: uin.json Import Configuration

---

## Problem Statement

After fixing the category parameter, the test still failed with the same "Incompatible struct value" error. Comparative analysis with a working Tier-2 example revealed a missing `revision` field in the import configuration.

---

## Discovery Process

Compared Trinity's `uin.json` with a working Margarita implementation:

### Working Example (Margarita)

**File**: `/Users/sanket/Time-Dynamics/Margarita/MargaritaComposite/uin.json`

```json
{
  "global": {
    "imports": {
      "SampleQuote": {
        "fields": ["open", "high", "low", "close", "volume", "turnover"],
        "granularities": [300],
        "revision": 4294967295,     // ← PRESENT
        "markets": ["DCE", "SHFE", "CZCE"],
        ...
      }
    }
  },
  "private": {
    "imports": {
      "Margarita": {
        "fields": ["_preserved_field", "bar_index", ...],
        "granularities": [300],
        "revision": 4294967295,     // ← PRESENT
        "markets": ["DCE", "SHFE", "CZCE"],
        ...
      }
    }
  }
}
```

### Trinity Configuration (Before Fix)

**File**: `/workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/uin.json`

```json
{
  "global": {
    "imports": {
      "SampleQuote": {
        "fields": ["open", "high", "low", "close", "volume", "turnover"],
        "granularities": [900],
        // ❌ NO revision field
        "markets": ["DCE", "SHFE", "CZCE"],
        ...
      }
    }
  },
  "private": {
    "imports": {
      "TrinityStrategy": {
        "fields": ["_preserved_field", "bar_index", ...],
        "granularities": [900],
        // ❌ NO revision field
        "markets": ["DCE", "SHFE", "CZCE"],
        ...
      }
    }
  }
}
```

**Missing**: `"revision": 4294967295` in both global and private imports

---

## Understanding `revision`

**WOS Documentation Reference**: `wos/02-uin-and-uout.md`

**Line 113-114**:
```
**revision**: Schema version
- Always use `4294967295` (latest version constant: `(1 << 32) - 1`)
```

**Line 660** (Validation Checklist):
```
- [ ] Revision is 4294967295
```

**Purpose**:
- Schema version identifier
- Ensures compatibility between data producers and consumers
- Allows framework to verify producer/consumer version matching
- Value `4294967295` = `(1 << 32) - 1` = "latest version"

---

## Applied Fix

### Change 1: Added `revision` to `uin.json` (Global Import)

**File**: `Trinity_Phase-2/uin.json`

```json
{
  "global": {
    "imports": {
      "SampleQuote": {
        "fields": ["open", "high", "low", "close", "volume", "turnover"],
        "granularities": [900],
        "revision": 4294967295,     // ← ADDED
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

### Change 2: Added `revision` to `uin.json` (Private Import)

```json
{
  "private": {
    "imports": {
      "TrinityStrategy": {
        "fields": ["_preserved_field", "bar_index", "adx_value", "di_plus", "di_minus", "upper_band", "middle_band", "lower_band", "conviction_oscillator"],
        "granularities": [900],
        "revision": 4294967295,     // ← ADDED
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

---

## Test Results

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
[2025-11-13 21:10:29][ERROR]start backtest failed with message:
User.uuid != author.uuid, very likely duplicated indicator names are found. Please change your indicator name.
```

✅ **Progress**: Different error! This proved the revision field was necessary.
❌ **Not Complete**: But there was now a new issue (duplicate strategy name - see Issue #4).

---

## Why This Field Matters

The `revision` field is used by the framework for **schema version verification**:

1. **Producer** (TrinityStrategy): Has `self.revision = (1 << 32) - 1` in class definition
2. **Consumer** (TrinityCaptain): Needs `"revision": 4294967295` in uin.json import
3. **Framework**: Matches these to ensure compatibility

**Without revision in uin.json**:
- Framework cannot verify schema compatibility
- May default to incompatible version matching
- Could cause silent data routing failures
- Results in "Incompatible struct value" errors

---

## Documentation Gap

**Problem**: The `revision` field is mentioned in documentation but **not emphasized** as mandatory.

**WOS Documentation Analysis**:

**What's Documented**:
- `wos/02-uin-and-uout.md` line 113-114: Mentions revision and value
- Line 660: Includes in validation checklist

**What's Missing**:
1. ❌ No clear statement: "revision is REQUIRED in all imports"
2. ❌ No explanation of what happens if revision is omitted
3. ❌ Not prominently featured in examples
4. ❌ Not in the "Critical Requirements" section
5. ❌ Easy to overlook in the checklist

**Confusion Source**: The Tier-2 composite documentation (`wos/08-tier2-composite.md`) shows import examples but **doesn't highlight the revision field**.

**Example from docs** (line 70-85):
```json
"Dependency1": {
  "fields": [
    "bar_index",
    "ema_fast",
    "ema_slow",
    "signal",
    "confidence"
  ],
  "granularities": [300],
  // No revision shown in example!
  "markets": ["SHFE"],
  ...
}
```

---

## Recommendations for Documentation

**1. Make `revision` Prominent**:
```markdown
## CRITICAL: revision Field

**REQUIRED in ALL imports** (both global and private):

```json
"imports": {
  "DataSource": {
    "revision": 4294967295,  // ← ALWAYS REQUIRED
    "fields": [...],
    ...
  }
}
```

**Value**: Always use `4294967295` (constant for "latest version")
**Purpose**: Schema version matching between producer/consumer
**Omitting this will cause**: "Incompatible struct value" errors
```

**2. Add to Examples**: Every uin.json example should include `revision`

**3. Add Warning Box**:
```markdown
⚠️ **Common Error**: Forgetting the `revision` field will cause
"Incompatible struct value" errors during data deserialization.
```

---

## Lessons Learned

1. ✅ **Check working examples** - comparing with Margarita revealed the missing field
2. ⚠️ **Documentation completeness** - field mentioned but not emphasized enough
3. 🔍 **Progress indicators** - getting a DIFFERENT error meant we were making progress
4. 📝 **Validation checklists** - need to be more prominent and mandatory

---

**Next**: [04-duplicate-strategy-name.md](./04-duplicate-strategy-name.md)
