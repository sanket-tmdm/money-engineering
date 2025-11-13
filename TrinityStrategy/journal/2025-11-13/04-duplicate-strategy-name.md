# Issue #4: Duplicate Strategy Name Collision

**Status**: ✅ RESOLVED (Renamed to TrinityCaptain)
**Date**: November 13, 2025
**Component**: Strategy Metadata Configuration

---

## Problem Statement

After fixing the category parameter and adding the revision field, a new error appeared:

```
[2025-11-13 21:10:29][ERROR]start backtest failed with message:
User.uuid != author.uuid, very likely duplicated indicator names are found.
Please change your indicator name.
```

**Meaning**: A strategy named "WOS_Captain" already exists on the server under a different user account.

---

## Root Cause

The strategy name `"WOS_Captain"` was already registered in the system, preventing the new registration.

**Two locations define the strategy name:**

### Location 1: Strategy Class Metadata

**File**: `Trinity_Phase-2/WOS_Captain.py` (line 146)

```python
class TrinityCaptain(csc3.composite_strategy):
    """Fund manager with regime-adaptive trading"""

    def __init__(self):
        # Initialize critical attributes FIRST (before super().__init__)
        self.bar_index_this_run = -1
        self.latest_sv = None
        ...

        # Metadata
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'COMPOSITE'
        self.meta_name = "WOS_Captain"    # ← DUPLICATE NAME
        self.revision = (1 << 32) - 1
        ...
```

### Location 2: Launch Configuration

**File**: `.vscode/launch.json` (3 configurations)

1. **Captain - Quick Test (7 days)** - line 139
2. **Captain - Full Backtest (1 year)** - line 167
3. **Captain - Multi-Year (3 years)** - line 196

```json
{
    "name": "Captain - Quick Test (7 days)",
    "args": [
        "--testcase", "${workspaceFolder}/Trinity_Phase-2/",
        "--algoname", "WOS_Captain",     // ← MUST MATCH meta_name
        "--sourcefile", "WOS_Captain.py",
        ...
    ]
}
```

**Requirement**: `--algoname` parameter MUST match `self.meta_name` in the strategy class.

---

## Applied Fix

Changed the strategy name from `"WOS_Captain"` to `"TrinityCaptain"` in both locations:

### Change 1: Updated `WOS_Captain.py`

**Before**:
```python
        # Metadata
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'COMPOSITE'
        self.meta_name = "WOS_Captain"
        self.revision = (1 << 32) - 1
```

**After**:
```python
        # Metadata
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'COMPOSITE'
        self.meta_name = "TrinityCaptain"    # ← CHANGED
        self.revision = (1 << 32) - 1
```

### Change 2: Updated `.vscode/launch.json` (All 3 Configs)

**Quick Test (Line 139)**:
```json
"args": [
    "--testcase", "${workspaceFolder}/Trinity_Phase-2/",
    "--algoname", "TrinityCaptain",    // ← CHANGED
    "--sourcefile", "WOS_Captain.py",
    ...
]
```

**Full Backtest (Line 167)**:
```json
"args": [
    "--testcase", "${workspaceFolder}/Trinity_Phase-2/",
    "--algoname", "TrinityCaptain",    // ← CHANGED
    "--sourcefile", "WOS_Captain.py",
    ...
]
```

**Multi-Year (Line 196)**:
```json
"args": [
    "--testcase", "${workspaceFolder}/Trinity_Phase-2/",
    "--algoname", "TrinityCaptain",    // ← CHANGED
    "--sourcefile", "WOS_Captain.py",
    ...
]
```

---

## Test Results

**Test Command** (with new name):
```bash
python3 /home/wolverine/bin/running/calculator3_test.py \
    --testcase /workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/ \
    --algoname TrinityCaptain \
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
[2025-11-13 21:18:29.143051][vanilla_logger][][INFO]Initialized 12 baskets, capital per basket: 833333.33
[2025-11-13 21:18:29.705990][vanilla_logger][][INFO]Initialized 12 baskets, capital per basket: 833333.33
NET_CMD_GOLD_ROUTE_DATADEF(len=213239) is received, begin to reinitiate
NET_CMD_GOLD_ROUTE_DATADEF is processed
```

✅ **Name Collision Resolved** - Test progressed past initialization

❌ **New Error**: Still got "Incompatible struct value" error (the REAL root cause - see Issue #5)

---

## Analysis

### Why "WOS_Captain" Was Taken

Possible reasons:
1. **Previous test run**: Earlier failed attempts registered the name
2. **Shared dev environment**: Another developer using the same name
3. **Example code**: Template code using common example names

### Name Uniqueness Requirements

The framework enforces **global uniqueness** of strategy names:
- Each `meta_name` must be unique per user account
- Prevents accidental data mixing between strategies
- Ensures proper data routing in multi-strategy environments

**Error Message Components**:
- `User.uuid != author.uuid`: Current user doesn't own this strategy name
- `duplicated indicator names`: Name already registered
- `Please change your indicator name`: Simple fix - pick a different name

---

## Best Practices Learned

### 1. Use Project-Specific Names

**Bad** (Generic):
```python
self.meta_name = "WOS_Captain"        # Too generic
self.meta_name = "MyStrategy"         # Too common
self.meta_name = "CompositeStrategy"  # Too generic
```

**Good** (Project-Specific):
```python
self.meta_name = "TrinityCaptain"     # Project-specific ✅
self.meta_name = "MargaritaComposite" # Project-specific ✅
self.meta_name = "IronCondorManager"  # Descriptive ✅
```

### 2. Match File and Strategy Names

**Pattern**:
- File: `WOS_Captain.py`
- Class: `TrinityCaptain`
- meta_name: `"TrinityCaptain"`
- algoname: `"TrinityCaptain"`

All related, consistent, project-specific.

### 3. Check Name Availability

Before implementing a large strategy, verify the name isn't taken:
- Try a quick test with the desired `meta_name`
- If you get "duplicate indicator names", choose different name
- Saves time vs discovering late in development

---

## Documentation Gap

**WOS Documentation Reference**: `wos/03-programming-basics-and-cli.md`, `wos/04-structvalue-and-sv_object.md`

**What's Documented**:
- `meta_name` field is required
- Must match between class and `--algoname` parameter

**What's Missing**:
1. ❌ No warning about name uniqueness requirements
2. ❌ No guidance on naming conventions
3. ❌ No mention of name collision errors
4. ❌ No recommendation to use project-specific names
5. ❌ No explanation of "User.uuid != author.uuid" error

**Would Be Helpful**:
```markdown
## Strategy Naming Best Practices

**Uniqueness**: `meta_name` must be globally unique per user account.

**Convention**: Use project-specific, descriptive names:
- ✅ Good: "TrinityCaptain", "MargaritaComposite"
- ❌ Bad: "MyStrategy", "TestStrategy", "WOS_Captain"

**Error**: If you see "User.uuid != author.uuid, duplicated indicator names",
your chosen name is already registered. Change `meta_name` in your class
and `--algoname` in launch configuration to a unique value.
```

---

## Lessons Learned

1. ✅ **Quick error resolution** - error message was clear, fix was straightforward
2. 🎯 **Use descriptive names** - "TrinityCaptain" clearly identifies this strategy
3. 🔄 **Consistent naming** - keep meta_name and algoname synchronized
4. ⚠️ **This wasn't the root cause** - just another hurdle before finding the real issue

---

**Next**: [05-contract-code-mismatch.md](./05-contract-code-mismatch.md) ← **THE ACTUAL FIX**
