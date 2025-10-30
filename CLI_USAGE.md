# Wolverine Project Creator - CLI Tool

## Overview

The `create_project.py` CLI tool automates the creation of new Wolverine indicator and strategy projects. It generates all necessary files, configurations, and boilerplate code to get you started immediately.

## Quick Start

### Interactive Mode (Recommended for Beginners)

```bash
./create_project.py --interactive
```

This will guide you through a series of questions to configure your project.

### Command-Line Mode (Quick)

```bash
# Basic indicator
./create_project.py --name MyIndicator --market DCE --securities i,j

# Multi-market indicator
./create_project.py --name MultiMarket --market DCE,SHFE --securities-DCE i,j --securities-SHFE cu,al --granularity 300,900

# Composite strategy
./create_project.py --name MyComposite --type composite
```

## Usage

### Basic Syntax

```bash
./create_project.py [OPTIONS]
```

### Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--name NAME` | Project name (required in non-interactive mode) | - | `MyIndicator` |
| `--type TYPE` | Project type: `indicator`, `composite`, `strategy` | `indicator` | `--type indicator` |
| `--market MARKETS` | Comma-separated markets | `DCE` | `--market DCE,SHFE` |
| `--securities SECS` | Securities for single market | First available | `--securities i,j` |
| `--securities-MARKET` | Securities for specific market | - | `--securities-DCE i,j` |
| `--granularity GRANS` | Granularities in seconds (comma-separated) | `900` | `--granularity 300,900,3600` |
| `--token TOKEN` | API authentication token | `YOUR_TOKEN_HERE` | `--token abc123...` |
| `--interactive` | Interactive wizard mode | - | `--interactive` |

### Markets and Securities

**Available Markets:**
- **DCE** (Dalian Commodity Exchange)
  - Securities: i, j, m, y, p, c, a, b, v, l, pp
- **SHFE** (Shanghai Futures Exchange)
  - Securities: cu, al, zn, pb, ni, sn, au, ag, rb, wr, hc, fu, bu, ru, sc
- **CZCE** (Zhengzhou Commodity Exchange)
  - Securities: TA, MA, FG, SR, CF, RM, OI, WH, AP, CJ (UPPERCASE!)
- **CFFEX** (China Financial Futures Exchange)
  - Securities: IF, IC, IH, T, TF

**Important:** CZCE uses UPPERCASE commodity codes!

### Granularities

Specify time granularities in seconds:

| Label | Seconds | Usage |
|-------|---------|-------|
| 1min | 60 | High-frequency analysis |
| 5min | 300 | Short-term trading |
| 15min | 900 | Standard timeframe (default) |
| 30min | 1800 | Medium-term analysis |
| 1h | 3600 | Hourly analysis |
| 4h | 14400 | Daily trend analysis |
| 1d | 86400 | Daily analysis |

## Examples

### Example 1: Simple Iron Ore Indicator

Create a basic indicator for iron ore on DCE:

```bash
./create_project.py \\
    --name IronOreMA \\
    --type indicator \\
    --market DCE \\
    --securities i \\
    --granularity 900
```

**Creates:**
- `IronOreMA/IronOreMA.py` - Main indicator file
- `IronOreMA/uin.json` - Configured for DCE iron ore
- `IronOreMA/uout.json` - Output configuration
- `IronOreMA/.vscode/launch.json` - Debug configurations
- `IronOreMA/.devcontainer/devcontainer.json` - Container setup
- `IronOreMA/test_resuming_mode.py` - Replay consistency test
- `IronOreMA/wos/` - **Symlink to WOS documentation** (readonly reference)
- `IronOreMA/CLAUDE.md` - Project guidance for Claude Code
- `IronOreMA/README.md` - Project documentation

### Example 2: Multi-Timeframe Indicator

Create an indicator with multiple timeframes:

```bash
./create_project.py \\
    --name MomentumMaster \\
    --type indicator \\
    --market DCE \\
    --securities i,j \\
    --granularity 300,900,3600
```

**This configures:**
- 5-minute (300s) for short-term signals
- 15-minute (900s) for medium-term analysis
- 1-hour (3600s) for trend confirmation

### Example 3: Multi-Market Indicator

Create an indicator for multiple markets:

```bash
./create_project.py \\
    --name MetalsMomentum \\
    --type indicator \\
    --market SHFE,CZCE \\
    --securities-SHFE cu,al,zn \\
    --securities-CZCE TA,MA
```

**Important:** Notice CZCE securities are UPPERCASE!

### Example 4: Composite Strategy

Create a Tier 2 portfolio manager:

```bash
./create_project.py \\
    --name MultiStrategyPortfolio \\
    --type composite
```

**This creates:**
- Composite strategy structure
- Basket management boilerplate
- Signal aggregation framework
- Portfolio state tracking

### Example 5: With API Token

Include your API token in the configuration:

```bash
./create_project.py \\
    --name MyIndicator \\
    --market DCE \\
    --securities i \\
    --token "58abd12edbde042536637bfba9d20d5faf366ef4..."
```

**Result:** The token is embedded in `.vscode/launch.json` debug configurations.

### Example 6: Interactive Mode

Most user-friendly for beginners:

```bash
./create_project.py --interactive
```

**Interactive Prompts:**
```
Project name (e.g., MyIndicator): IronOreStrategy

Project type:
  1. Indicator (Tier 1) - Technical analysis indicator
  2. Composite (Tier 2) - Multi-strategy portfolio manager
  3. Strategy (Tier 3) - Execution strategy
Select type [1/2/3] (default: 1): 1

Select markets (comma-separated, e.g., DCE,SHFE):
  Available: DCE, SHFE, CZCE, CFFEX
Markets (default: DCE): DCE

Securities for DCE:
  Available: i, j, m, y, p, c, a, b, v, l, pp
  Enter securities (comma-separated, default: i): i,j

Granularities:
  Available: 1min, 5min, 15min, 30min, 1h, 4h, 1d
Enter granularities (comma-separated, default: 15min): 15min,1h

API Token:
Enter API token (or press Enter to use placeholder):

Project Configuration:
====================================
Name:          IronOreStrategy
Type:          indicator
Markets:       DCE
  DCE          i, j
Granularities: 900, 3600
Token:         (placeholder)
====================================

Create project? (yes/no): yes
```

## What Gets Created

When you run the tool, it creates a complete project structure:

```
MyIndicator/
├── MyIndicator.py              # Main implementation (full template)
├── uin.json                    # Input configuration (pre-configured)
├── uout.json                   # Output configuration (pre-configured)
├── test_resuming_mode.py       # Replay consistency test
├── myindicator_viz.py          # Visualization script template
├── wos/                        # → Symlink to WOS docs (12 chapters)
├── CLAUDE.md                   # Claude Code guidance
├── README.md                   # Project documentation
├── .vscode/
│   └── launch.json            # VS Code debug configurations
└── .devcontainer/
    └── devcontainer.json      # Docker container configuration
```

### File Details

**MyIndicator.py:**
- Complete sv_object structure
- on_bar() with data routing
- _on_cycle_pass() for calculations
- All required framework callbacks
- TODO comments for customization

**uin.json:**
- Configured for your markets/securities
- Correct granularities
- Proper array alignment

**uout.json:**
- _preserved_field (required)
- Basic output fields (bar_index, indicator_value, signal)
- Correct field types and precision

**.vscode/launch.json:**
- "Quick Test" configuration (7-day backtest)
- "Full Backtest" configuration (full history)
- "Test Resuming Mode" configuration
- Pre-configured with your token (if provided)

**.devcontainer/devcontainer.json:**
- Docker image: `glacierx/wos-prod-arm64`
- VS Code extensions auto-installed
- PYTHONPATH configured
- Project-specific container name

**test_resuming_mode.py:**
- Automated replay consistency testing
- Configurable date ranges
- Pass/fail validation

**wos/ (symlink):**
- **Readonly link** to complete WOS documentation
- All 12 chapters available locally in project
- No duplication (saves space)
- Always up-to-date with source
- Accessible in container: `./wos/01-overview.md`
- Claude Code can reference: `./wos/07-tier1-indicator.md`

**CLAUDE.md:**
- Project-specific guidance
- Implementation TODOs
- Framework rules reminder
- Development workflow

## Workflow After Creation

### 1. Navigate to Project

```bash
cd MyIndicator
```

### 2. Open in VS Code

```bash
code .
```

### 3. Reopen in Container

- Press `Cmd/Ctrl+Shift+P`
- Type "Dev Containers: Reopen in Container"
- Wait for container to build

### 4. Implement Your Logic

Edit `MyIndicator.py`:
- Implement `_on_cycle_pass()` method
- Add your indicator calculations
- Generate signals based on logic

### 5. Quick Test

- Press `F5`
- Select "MyIndicator - Quick Test"
- Check console output for results

### 6. Debug Issues

- Set breakpoints in your code
- Step through execution
- Inspect variables

### 7. Replay Consistency Test

```bash
python test_resuming_mode.py
```

### 8. Visualize Results

```bash
# After implementing visualization script
python myindicator_viz.py
```

### 9. Full Backtest

- Press `F5`
- Select "MyIndicator - Full Backtest"
- Review complete historical performance

### 10. Deploy

Once all tests pass:
- Set `overwrite = False` in Python file
- Deploy to production following org procedures

## Tips and Best Practices

### Naming Conventions

**Good Names:**
- `MomentumMaster` - Clear purpose
- `IronOreVolatility` - Specific commodity
- `MultiMarketTrend` - Descriptive scope
- `VolumeProfile` - Technical indicator name

**Bad Names:**
- `test123` - Not descriptive
- `MyIndicator` - Too generic
- `Indicator1` - No meaning
- `Strategy` - Too vague

### Market Configuration

**Single Market:**
```bash
--market DCE --securities i,j
```

**Multiple Markets:**
```bash
--market DCE,SHFE \\
--securities-DCE i,j \\
--securities-SHFE cu,al
```

**Remember CZCE Uppercase:**
```bash
--market CZCE --securities TA,MA  # Not ta,ma!
```

### Granularity Selection

**Single Timeframe (Simplest):**
```bash
--granularity 900  # Just 15min
```

**Multi-Timeframe (Better):**
```bash
--granularity 300,900,3600  # 5min, 15min, 1H
```

**Why Multi-Timeframe?**
- Better signal confirmation
- Reduce false signals
- Capture different market dynamics

### Token Management

**Option 1: CLI Argument**
```bash
--token "YOUR_TOKEN_HERE"
```

**Option 2: Environment Variable (Recommended)**
```bash
# Add to ~/.env in container
export WOS_API_TOKEN="YOUR_TOKEN_HERE"

# Then create project without --token flag
# launch.json will use ${env:WOS_API_TOKEN}
```

**Option 3: Manual Edit**
```bash
# Create project without token
# Then edit .vscode/launch.json manually
```

## Troubleshooting

### Issue: Command not found

**Solution:**
```bash
# Make executable
chmod +x create_project.py

# Or run with python
python create_project.py --help
```

### Issue: Project already exists

**Response:**
```
Project 'MyIndicator' already exists. Overwrite? (yes/no):
```

Type `yes` to replace, or `no` to abort and choose a different name.

### Issue: Invalid commodity for market

**Example:**
```bash
--market DCE --securities cu  # cu is SHFE, not DCE!
```

**Solution:**
Check valid commodities for each market (see table above).

### Issue: CZCE commodities not working

**Problem:**
```bash
--securities-CZCE ta,ma  # Wrong! Lowercase
```

**Solution:**
```bash
--securities-CZCE TA,MA  # Correct! UPPERCASE
```

## Advanced Usage

### Custom Directory

Run from a different directory:

```bash
cd /path/to/my/projects
python /path/to/egg/create_project.py --name MyIndicator
```

### Batch Creation

Create multiple projects:

```bash
for commodity in i j cu al; do
    python create_project.py --name ${commodity}_Momentum --securities $commodity
done
```

### Template Customization

After creation, customize the generated files:

```python
# Edit MyIndicator.py
# Add your specific indicators
# Modify output fields in uout.json
# Update uin.json for additional imports
```

## Integration with Claude Code

After creating a project, Claude Code can:

1. **Read CLAUDE.md** for project context
2. **Implement logic** based on TODOs
3. **Debug issues** using framework knowledge
4. **Optimize parameters** using visualization data
5. **Generate tests** for validation

**Example Claude Code prompt:**
```
"Implement a 20-period EMA indicator in the _on_cycle_pass() method
and generate signals when price crosses the EMA"
```

Claude Code will read CLAUDE.md and implement the logic correctly using the framework patterns.

## Summary

The `create_project.py` CLI tool provides:

- ✅ **Fast project creation** (seconds)
- ✅ **Complete boilerplate** (no missing files)
- ✅ **Correct configuration** (no alignment errors)
- ✅ **Framework compliance** (follows all doctrines)
- ✅ **Ready to code** (just implement your logic)
- ✅ **Debug ready** (VS Code configurations included)
- ✅ **Test ready** (replay consistency test included)
- ✅ **Claude Code ready** (CLAUDE.md guidance included)

**Get started in seconds:**

```bash
./create_project.py --interactive
```

Then open VS Code, reopen in container, and start coding!

---

**Questions?** Check the WOS documentation in `wos/` directory or use Claude Code for assistance.
