# Wolverine Indicator & Strategy Development Environment (WOS-EGG)

## Overview

This package provides a complete, standalone development environment for building financial indicators and trading strategies using the Wolverine financial engineering system. It includes:

- **CLI Tool** for instant project creation (`create_project.py`)
- **Complete Documentation** (12 comprehensive chapters)
- **Pre-configured Container** (Docker-based development environment)
- **Templates and Examples** (working code patterns)
- **Claude Code Integration** (AI-assisted development)

## 🚀 Quick Start (3 Steps, 2 Minutes)

### Step 1: Create Your Project (30 seconds)

```bash
# Interactive mode (recommended for first time)
./create_project.py --interactive

# Or quick command-line mode
./create_project.py --name MyIndicator --market DCE --securities i,j
```

**That's it!** The CLI tool creates a complete project with:
- ✅ Main indicator Python file with full template
- ✅ uin.json and uout.json pre-configured
- ✅ VS Code debug configurations
- ✅ Container configuration
- ✅ Test scripts
- ✅ **WOS documentation linked** (./wos/ → all 12 chapters accessible)
- ✅ Documentation (CLAUDE.md, README.md)

### Step 2: Open in VS Code (30 seconds)

```bash
cd MyIndicator
code .
```

Then reopen in container:
- Press `Cmd/Ctrl+Shift+P`
- Type "Dev Containers: Reopen in Container"
- Hit Enter

### Step 3: Start Coding (1 minute)

Edit `MyIndicator.py` and implement your logic in the `_on_cycle_pass()` method, then press `F5` to run!

## Detailed Setup Guide

### Prerequisites

1. **Docker**: Installed and running
2. **VS Code**: With the Dev Containers extension installed
3. **Claude Code**: Installed locally (for AI-assisted development)
4. **System Requirements**:
   - 8GB RAM minimum (16GB recommended)
   - 20GB free disk space
   - Linux/macOS/Windows with WSL2

### Using the CLI Tool (Recommended)

**The `create_project.py` CLI tool** automates project creation. See [CLI_USAGE.md](CLI_USAGE.md) for complete documentation.

**Interactive Mode (Easiest):**

```bash
./create_project.py --interactive
```

This walks you through:
- Project name
- Project type (indicator/composite/strategy)
- Markets and securities
- Granularities (timeframes)
- API token (optional)

**Command-Line Mode (Fastest):**

```bash
# Basic indicator for iron ore on DCE
./create_project.py --name IronOreMA --market DCE --securities i

# Multi-market indicator
./create_project.py --name MetalsMomentum --market SHFE,CZCE --securities-SHFE cu,al --securities-CZCE TA,MA

# Multi-timeframe analysis
./create_project.py --name MomentumMaster --market DCE --securities i,j --granularity 300,900,3600

# Composite strategy
./create_project.py --name MyComposite --type composite
```

**More Examples:** See [CLI_USAGE.md](CLI_USAGE.md)

#### Step 2: Open and Develop

After creating the project:

```bash
# Navigate to where you want your project
cd ~/Projects

# Copy the egg folder to create your new project
cp -r path/to/egg my_indicator_project
cd my_indicator_project
```

#### Step 2: Configure Environment

Edit the `.devcontainer/devcontainer.json` file:
- Update the `name` field to your project name
- Verify the Docker image is correct

#### Step 3: Open in Container

```bash
# Open VS Code
code .

# In VS Code:
# 1. Press Cmd/Ctrl+Shift+P
# 2. Type "Dev Containers: Reopen in Container"
# 3. Select it and wait for container to build (first time: 5-10 minutes)
```

#### Step 4: Verify Installation

Once inside the container:

```bash
# Check Python environment
python --version  # Should be Python 3.x

# Check framework availability
python -c "import pycaitlyn as pc; print('Framework loaded!')"

# Check wolverine binary path
ls /home/wolverine/bin/running/calculator3_test.py
```

#### Step 5: Create Your First Indicator

Use Claude Code to assist:

```bash
# In the container terminal
claude "Create a basic indicator project called SimpleMA"
```

Claude Code will:
1. Create the project folder structure
2. Generate template files (uin.json, uout.json, .py file)
3. Set up VS Code debug configuration
4. Create visualization script template

## Project Structure

```
my_indicator_project/
├── README.md                    # This file
├── .devcontainer/
│   └── devcontainer.json       # Container configuration
├── .vscode/
│   └── launch.json.template    # Debug configuration template
├── wos/                        # Wolverine Operating System knowledge base
│   ├── 01-fundamentals.md      # Core concepts
│   ├── 02-indicator-development.md
│   ├── 03-composite-strategies.md
│   ├── 04-visualization.md
│   ├── 05-testing.md
│   └── 06-deployment.md
├── templates/                   # Project templates
│   ├── basic_indicator/        # Basic indicator template
│   ├── composite_strategy/     # Composite strategy template
│   └── visualization/          # Visualization script template
└── examples/                    # Working examples
    ├── simple_moving_average/
    └── momentum_indicator/
```

## Development Workflow

### 1. Create New Indicator Project

```bash
# Use Claude Code to create project structure
claude "Create a new indicator project for [INDICATOR_NAME]"
```

**What Claude Code Will Do:**
1. Create project folder: `./{INDICATOR_NAME}/`
2. Generate template files:
   - `{INDICATOR_NAME}.py` - Main indicator implementation
   - `uin.json` - Input configuration
   - `uout.json` - Output configuration
   - `test_resuming_mode.py` - Replay consistency test
   - `.vscode/launch.json` - Debug configurations
   - `{indicator_name}_viz.py` - Visualization script
   - `CLAUDE.md` - Project-specific AI guidance

### 2. Configure Input/Output

**Edit `uin.json`** to specify:
- Data sources (SampleQuote, ZampleQuote)
- Granularities (timeframes)
- Markets and securities
- Input fields

**Edit `uout.json`** to specify:
- Output fields and types
- Field precision
- Display names
- Export configuration

**Critical Rules:**
- Always use `"XXX"` as the export algorithm name
- Always include `"_preserved_field"` as the first field
- Match markets/securities arrays across uin.json and uout.json

### 3. Implement Indicator Logic

**Edit `{INDICATOR_NAME}.py`**:

```python
#!/usr/bin/env python3
# coding=utf-8

import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3
from typing import List

# Framework globals
use_raw = True
overwrite = True
granularity = 900  # 15 minutes
max_workers = 1
worker_no = None
exports = {}
imports = {}
metas = {}
logger = pcu3.vanilla_logger()

class SampleQuote(pcts3.sv_object):
    """Input data structure"""
    def __init__(self):
        super().__init__()
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # Input fields
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = None
        self.turnover = None

class YourIndicator(pcts3.sv_object):
    """Your indicator implementation"""
    def __init__(self):
        super().__init__()

        # Metadata - CONSTANTS
        self.meta_name = "YourIndicator"
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'i<00>'
        self.revision = (1 << 32) - 1

        # State variables
        self.bar_index = 0
        self.timetag = None

        # Your indicator fields
        self.indicator_value = 0.0

        # Dependency sv_objects
        self.sq = SampleQuote()

    def initialize(self, imports, metas):
        """Initialize schemas"""
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)
        self.sq.load_def_from_dict(metas)
        self.sq.set_global_imports(imports)

    def on_bar(self, bar: pc.StructValue) -> List[pc.StructValue]:
        """Process incoming data"""
        ret = []  # Always return list

        # Extract metadata
        market = bar.get_market()
        code = bar.get_stock_code()
        tm = bar.get_time_tag()
        ns = bar.get_namespace()
        meta_id = bar.get_meta_id()

        # Route to correct sv_object
        if self.sq.namespace == ns and self.sq.meta_id == meta_id:
            # Filter for logical contracts only
            if code.endswith(b'<00>'):
                self.sq.market = market
                self.sq.code = code
                self.sq.granularity = bar.get_granularity()
                self.sq.from_sv(bar)

                # Handle cycle boundaries
                if self.timetag is None:
                    self.timetag = tm

                if self.timetag < tm:
                    self._on_cycle_pass(tm)

                    if self.ready_to_serialize():
                        ret.append(self.copy_to_sv())

                    self.timetag = tm
                    self.bar_index += 1

        return ret

    def _on_cycle_pass(self, time_tag):
        """Process cycle - your logic here"""
        # Use data from self.sq
        current_price = float(self.sq.close)

        # Your calculations
        self.indicator_value = current_price * 1.01  # Example

    def ready_to_serialize(self) -> bool:
        """Determine if state should be saved"""
        return self.bar_index > 0

# Global instance
indicator = YourIndicator()

# Framework callbacks
async def on_init():
    global indicator, imports, metas, worker_no
    if worker_no == 1 and metas and imports:
        indicator.initialize(imports, metas)

async def on_bar(bar: pc.StructValue):
    global indicator, worker_no
    if worker_no != 1:
        return []
    return indicator.on_bar(bar)

# Additional callbacks
async def on_ready():
    pass

async def on_market_open(market, tradeday, time_tag, time_string):
    pass

async def on_market_close(market, tradeday, timetag, timestring):
    pass

async def on_reference(market, tradeday, data, timetag, timestring):
    pass

async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    pass

async def on_tradeday_end(market, tradeday, timetag, timestring):
    pass
```

### 4. Test Your Indicator

**Use VS Code Debugger:**

1. Press F5 or go to Run > Start Debugging
2. Select "Quick Test" configuration
3. Set breakpoints in your code
4. Step through execution

**Run Replay Consistency Test:**

```bash
python test_resuming_mode.py
```

This test is **MANDATORY** and ensures your indicator produces identical results when:
- Running from start to end
- Resuming from a midpoint

### 5. Visualize Results

**Run Visualization Script:**

```bash
# In VS Code or terminal
python {indicator_name}_viz.py
```

**Or use Jupyter:**

```bash
jupyter notebook {indicator_name}_viz.py
```

The visualization script helps you:
- Validate parameter effectiveness
- Analyze indicator behavior
- Optimize thresholds and constants
- Generate performance reports

### 6. Deploy to Production

Once your indicator passes all tests:

1. **Final Validation:**
   - Replay consistency test passes
   - Full backtest completes successfully
   - Visualization shows expected behavior

2. **Configuration Check:**
   - `overwrite = False` in production
   - All parameters documented
   - CLAUDE.md updated with final guidance

3. **Deployment:**
   ```bash
   # Follow your organization's deployment process
   # Typically involves copying to production servers
   ```

## Working with Claude Code

Claude Code is your AI assistant for this project. Here are recommended workflows:

### Creating a New Indicator

```
Prompt: "Create a new indicator called MomentumMaster that tracks price momentum across 5min, 15min, and 1H timeframes. It should output a momentum score and regime classification."
```

Claude Code will:
1. Create folder structure
2. Generate uin.json with correct granularities
3. Generate uout.json with momentum_score and regime fields
4. Create template .py file with multi-timeframe structure
5. Set up debug configurations

### Debugging Issues

```
Prompt: "My indicator is showing AttributeError when accessing self.sq.close. Help me debug this."
```

Claude Code will:
1. Check your data routing logic
2. Verify sv_object initialization
3. Ensure proper from_sv() usage
4. Fix the issue

### Optimizing Parameters

```
Prompt: "Help me optimize the EMA alpha parameters in my indicator. Current alpha_fast is 0.1, alpha_slow is 0.05. I want them based on 10-period and 20-period EMAs."
```

Claude Code will:
1. Calculate correct alpha values: 2/(period+1)
2. Update your code
3. Regenerate visualization to validate changes

### Understanding Framework Concepts

```
Prompt: "Explain how the multiple indicator objects pattern works and why I need separate instances for each commodity."
```

Claude Code will reference the WOS knowledge base and provide detailed explanations.

## Critical Framework Rules

### 🚨 DOCTRINE 1: Multiple Indicator Objects Pattern

**NEVER** reuse a single indicator object for multiple commodities.

❌ **WRONG:**
```python
class MyIndicator:
    def on_bar(self, bar):
        code = bar.get_stock_code()
        if code.startswith(b'i'):
            # Process iron ore
        elif code.startswith(b'cu'):
            # Process copper - State contamination!
```

✅ **CORRECT:**
```python
class CommodityIndicator:
    def __init__(self, commodity_code, market):
        self.commodity_code = commodity_code
        self.market = market
        # Own sv_objects

class Manager:
    def __init__(self):
        self.indicators = {}
        for commodity in [b'i', b'cu', ...]:
            self.indicators[commodity] = CommodityIndicator(commodity, market)
```

### 🚨 DOCTRINE 2: No Fallback Logic for Dependency Data

**NEVER** use fallback logic for imported data.

❌ **WRONG:**
```python
current_price = float(active_quote.close) if active_quote.close is not None else 100.0
```

✅ **CORRECT:**
```python
current_price = float(active_quote.close)  # Trust dependency data
```

### 🚨 DOCTRINE 3: Always Return List Pattern

**ALWAYS** return a list from framework callbacks.

❌ **WRONG:**
```python
def on_bar(self, bar):
    if ready:
        return self.copy_to_sv()  # Wrong!
    return None  # Wrong!
```

✅ **CORRECT:**
```python
def on_bar(self, bar):
    ret = []  # Always start with empty list
    if ready:
        ret.append(self.copy_to_sv())
    return ret  # Always return list
```

### 🚨 DOCTRINE 4: Logical Contract Filtering

**ONLY** process logical contracts (ending in `<00>`).

❌ **WRONG:**
```python
if code.startswith(commodity_code):
    process()  # Processes monthly contracts too!
```

✅ **CORRECT:**
```python
if code.startswith(commodity_code) and code.endswith(b'<00>'):
    process()  # Only logical contracts
```

### 🚨 DOCTRINE 5: Code Format Convention

**DCE/SHFE**: lowercase `[b'i', b'j', b'cu', b'al', b'rb', b'sc', b'fu']`
**CZCE**: UPPERCASE `[b'TA', b'MA']`

## Knowledge Base (WOS)

The `wos/` directory contains comprehensive documentation:

1. **01-fundamentals.md** - Core concepts, sv_object pattern, framework architecture
2. **02-indicator-development.md** - Step-by-step indicator development guide
3. **03-composite-strategies.md** - Tier 2 portfolio management strategies
4. **04-visualization.md** - Creating visualization and analysis scripts
5. **05-testing.md** - Testing requirements, replay consistency
6. **06-deployment.md** - Production deployment guidelines

**Read these documents to deepen your understanding of the framework.**

## Templates

### Basic Indicator Template

Located in `templates/basic_indicator/`, includes:
- Complete indicator implementation
- Proper sv_object usage
- Multi-timeframe support
- Visualization script

### Composite Strategy Template

Located in `templates/composite_strategy/`, includes:
- Tier 2 portfolio manager
- Basket management
- Signal aggregation
- Risk management

### Visualization Template

Located in `templates/visualization/`, includes:
- Data fetching
- Parameter validation
- Performance analysis
- Random timepoint explorer

## Common Issues and Solutions

### Issue: "AttributeError: 'NoneType' object has no attribute 'close'"

**Solution:** Check data routing in `on_bar()`. Ensure:
1. Correct namespace/meta_id matching
2. `from_sv(bar)` called before accessing fields
3. Logical contract filtering (`code.endswith(b'<00>')`)

### Issue: "Replay consistency test fails"

**Solution:** Check for:
1. Non-deterministic calculations (random values)
2. State not properly persisted in output fields
3. Time-dependent operations using system time instead of timetag

### Issue: "No data received in on_bar()"

**Solution:** Verify:
1. `uin.json` markets/securities configuration
2. Date range has data for your commodities
3. Granularity matches what's available
4. Server connection parameters correct

### Issue: "Framework says '_preserved_field' not found"

**Solution:** Ensure:
1. `"_preserved_field"` is the FIRST field in `uout.json` fields array
2. Field type is `"int64"` with precision 0
3. No typos in field name

## Advanced Topics

### Multi-Commodity Indicators

When developing indicators for multiple commodities, create separate indicator instances:

```python
class MultiCommodityManager:
    def __init__(self):
        self.indicators = {
            b'i': CommodityIndicator(b'i', b'DCE'),
            b'j': CommodityIndicator(b'j', b'DCE'),
            b'cu': CommodityIndicator(b'cu', b'SHFE'),
            b'TA': CommodityIndicator(b'TA', b'CZCE'),  # Note: UPPERCASE
        }

    def on_bar(self, bar):
        results = []
        for code, indicator in self.indicators.items():
            if bar.get_stock_code().startswith(code):
                output = indicator.on_bar(bar)
                if output:
                    results.extend(output)
        return results
```

### Composite Strategies (Tier 2)

Build portfolio managers that consume multiple Tier 1 indicators:

```python
class CompositeStrategy(sc3.strategy):
    def __init__(self, initial_money=10000000.00, basket_count=10):
        super().__init__(initial_money)
        self.strategies = []  # Basket strategies
        self.imported_strategies = {}  # Available strategies

    def _on_strategy(self, strategy_signal):
        """Process Tier 1 strategy signals"""
        # Allocate capital to promising strategies
        # Remove underperformers
        # Rebalance portfolio
```

### Machine Learning Integration

Integrate ML models for enhanced decision-making:

```python
class MLIndicator(pcts3.sv_object):
    def __init__(self):
        super().__init__()
        self.ml_endpoint = "http://ml-server:8000/predict"

    async def get_ml_prediction(self, features):
        response = await aiohttp.post(
            self.ml_endpoint,
            json={'features': features}
        )
        return response.json()['prediction']
```

## Resources

### Documentation
- [Framework GitHub](https://github.com/your-org/wolverine)
- [API Reference](https://docs.your-org.com/wolverine/api)
- [Community Forum](https://forum.your-org.com/wolverine)

### Support
- **Issues**: Report at GitHub Issues
- **Questions**: Ask on Community Forum
- **Claude Code**: Use in-IDE for instant help

### Examples
- See `examples/` directory for working implementations
- Study the parent Margarita project for complex multi-timeframe indicators
- Check MargaritaComposite for Tier 2 composite strategy patterns

## Contributing

If you develop useful indicators or improvements to this egg package:

1. Test thoroughly (replay consistency, backtesting)
2. Document your changes
3. Submit pull request to the main repository
4. Share your experience with the community

## License

[Your License Here]

## Changelog

### v1.0.0 (2025-01-30)
- Initial release
- Basic indicator template
- Composite strategy template
- Comprehensive documentation
- Claude Code integration

---

**Happy Trading!** 🚀

For questions or issues, use Claude Code in your development environment or consult the WOS knowledge base in the `wos/` directory.
