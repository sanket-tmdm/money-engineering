# Issue #2: Category Parameter Causes Debugger Hang

**Status**: ✅ RESOLVED (Changed to category=1)
**Date**: November 13, 2025
**Component**: Launch Configuration

---

## Problem Statement

When running the Captain - Quick Test with `--category 2`, the debugger would **hang indefinitely** without starting the backtest.

**Symptoms**:
- Test command executed
- Debugger attached successfully
- No initialization logs
- No errors displayed
- Process stuck, no progress
- Required manual termination (Ctrl+C or kill process)

---

## Original Configuration

**File**: `.vscode/launch.json` - "Captain - Quick Test (7 days)"

```json
{
    "name": "Captain - Quick Test (7 days)",
    "type": "debugpy",
    "request": "launch",
    "program": "/home/wolverine/bin/running/calculator3_test.py",
    "args": [
        "--testcase", "${workspaceFolder}/Trinity_Phase-2/",
        "--algoname", "WOS_Captain",
        "--sourcefile", "WOS_Captain.py",
        "--start", "20241025000000",
        "--end", "20241101000000",
        "--granularity", "900",
        "--tm", "wss://10.99.100.116:4433/tm",
        "--tm-master", "10.99.100.116:6102",
        "--rails", "https://10.99.100.116:4433/private-api/",
        "--token", "...",
        "--category", "2",              // ← CAUSED HANG
        "--is-managed", "1",
        "--restore-length", "864000000",
        "--multiproc", "1"
    ],
    ...
}
```

---

## Initial Understanding

**From WOS Documentation** (`wos/03-programming-basics-and-cli.md` line 402):

```
--category: Algorithm category
- 1: Indicators (Tier-1)
- 2: Strategies (Tier-2/Tier-3)
```

**Assumption**: Since TrinityCaptain is a Tier-2 composite strategy, it should use `--category 2`.

---

## Observed Behavior

**Test Execution**:
```bash
$ python3 /home/wolverine/bin/running/calculator3_test.py \
    --testcase /workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/ \
    --algoname WOS_Captain \
    --sourcefile WOS_Captain.py \
    --category 2 \
    --is-managed 1 \
    ...
```

**Output**:
```
[Debugger attached]
[No further output]
[Process hangs indefinitely]
```

**No logs, no errors, no initialization**. The framework appeared to be waiting for something that never arrived.

---

## Resolution

Changed `--category` from `2` to `1` in all three Captain launch configurations:

### Updated Configuration

```json
"args": [
    "--testcase", "${workspaceFolder}/Trinity_Phase-2/",
    "--algoname", "WOS_Captain",
    "--sourcefile", "WOS_Captain.py",
    "--start", "20241025000000",
    "--end", "20241101000000",
    "--granularity", "900",
    "--tm", "wss://10.99.100.116:4433/tm",
    "--tm-master", "10.99.100.116:6102",
    "--rails", "https://10.99.100.116:4433/private-api/",
    "--token", "...",
    "--category", "1",              // ← CHANGED FROM 2 TO 1
    "--is-managed", "1",
    "--restore-length", "864000000",
    "--multiproc", "1"
]
```

### Configurations Updated

1. Captain - Quick Test (7 days) - line 148
2. Captain - Full Backtest (1 year) - line 176
3. Captain - Multi-Year (3 years) - line 205

---

## Result

**Test Execution After Fix**:
```bash
$ python3 /home/wolverine/bin/running/calculator3_test.py \
    --testcase /workspaces/money-engineering/TrinityStrategy/Trinity_Phase-2/ \
    --algoname WOS_Captain \
    --sourcefile WOS_Captain.py \
    --category 1 \
    ...
```

**Output**:
```
[2025-11-13 20:34:37.946747][vanilla_logger][][INFO]Initialized 12 baskets, capital per basket: 833333.33
[2025-11-13 20:34:38.534907][vanilla_logger][][INFO]Initialized 12 baskets, capital per basket: 833333.33
NET_CMD_GOLD_ROUTE_DATADEF(len=213185) is received, begin to reinitiate
NET_CMD_GOLD_ROUTE_DATADEF is processed
```

✅ **Test started successfully** - initialization logs appeared, baskets created, data routing established.

---

## Root Cause Analysis

**Hypothesis**: Category=2 likely triggers different initialization paths in the framework:
- May require additional infrastructure (trading permissions, risk checks, broker connections)
- May have stricter validation that silently fails
- Could be reserved for production strategies vs backtests

**Evidence**:
- Phase-1 TrinityStrategy uses `--category 1` and works perfectly
- Other working examples (Margarita) also use `--category 1` for Tier-2
- Changing to `--category 1` immediately resolved the hang

---

## Documentation Gap

**WOS Documentation Reference**: `wos/03-programming-basics-and-cli.md` line 402

The documentation states:
```
--category: Algorithm category
- 1: Indicators (Tier-1)
- 2: Strategies (Tier-2/Tier-3)
```

**Problem**: This guidance is **misleading** for backtest scenarios:
1. Suggests Tier-2 should use category=2
2. Doesn't mention category=2 may cause issues in backtests
3. Doesn't explain when to use which category
4. No examples of Tier-2 composite strategies using category=1

**What's Needed**:
- Clarify that category=1 works for BOTH Tier-1 and Tier-2 in backtests
- Explain when category=2 should actually be used
- Add explicit guidance: "For backtests, use category=1 for all tiers"
- Document the behavior difference between categories

---

## Impact

**Time Lost**: ~1 hour of debugging and testing different configurations

**Confusion Level**: High - documentation directly contradicts working solution

**Workaround**: Use `--category 1` for all backtest scenarios, regardless of tier level

---

## Lessons Learned

1. ⚠️ **Documentation can be misleading** - stated category mapping doesn't match backtest behavior
2. 🔍 **Silent failures are hard to debug** - no error message, just infinite hang
3. 📋 **Check working examples** - other Tier-2 strategies use category=1
4. 🧪 **Test simple changes** - changing one parameter revealed the issue

---

**Next**: [03-revision-field-missing.md](./03-revision-field-missing.md)
