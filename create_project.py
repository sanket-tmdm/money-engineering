#!/usr/bin/env python3
"""
Wolverine Project Creator - CLI tool to create new indicator/strategy projects

Usage:
    ./create_project.py --name MyIndicator --type indicator --market DCE --securities i,j --granularity 900
    ./create_project.py --name MyComposite --type composite
    ./create_project.py --interactive
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path


class ProjectCreator:
    """Create new Wolverine indicator/strategy projects"""

    VALID_MARKETS = {
        'DCE': ['i', 'j', 'm', 'y', 'p', 'c', 'a', 'b', 'v', 'l', 'pp'],
        'SHFE': ['cu', 'al', 'zn', 'pb', 'ni', 'sn', 'au', 'ag', 'rb', 'wr', 'hc', 'fu', 'bu', 'ru', 'sc'],
        'CZCE': ['TA', 'MA', 'FG', 'SR', 'CF', 'RM', 'OI', 'WH', 'AP', 'CJ'],
        'CFFEX': ['IF', 'IC', 'IH', 'T', 'TF']
    }

    GRANULARITIES = {
        '1min': 60,
        '5min': 300,
        '15min': 900,
        '30min': 1800,
        '1h': 3600,
        '4h': 14400,
        '1d': 86400
    }

    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.templates_dir = self.base_dir / 'templates'

    def create_project(self, name, project_type='indicator', markets=None, securities=None,
                      granularities=None, token='YOUR_TOKEN_HERE', interactive=False):
        """Create a new project with specified configuration"""

        if interactive:
            return self._interactive_create()

        # Validate inputs
        if not name:
            raise ValueError("Project name is required")

        if not name.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Project name must be alphanumeric (underscores and hyphens allowed)")

        # Set defaults
        if markets is None:
            markets = ['DCE']
        if securities is None:
            securities = {'DCE': ['i']}
        if granularities is None:
            granularities = [900]

        # Create project directory
        project_dir = self.base_dir / name
        if project_dir.exists():
            response = input(f"Project '{name}' already exists. Overwrite? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return None
            shutil.rmtree(project_dir)

        print(f"Creating project: {name}")
        project_dir.mkdir(parents=True)

        # Determine category based on type
        category = '1' if project_type == 'indicator' else '2' if project_type == 'composite' else '3'

        # Create project structure
        self._create_structure(project_dir, name, project_type, markets, securities,
                              granularities, token, category)

        print(f"\n✅ Project '{name}' created successfully!")
        print(f"\n📁 Location: {project_dir}")
        print(f"\n📚 Resources included:")
        print(f"   - WOS documentation linked at ./wos/ (readonly reference)")
        print(f"   - CLAUDE.md with project-specific guidance")
        print(f"   - Complete debug configurations")
        print(f"\n🚀 Next steps:")
        print(f"   1. cd {name}")
        print(f"   2. code .")
        print(f"   3. Press Cmd/Ctrl+Shift+P → 'Dev Containers: Reopen in Container'")
        print(f"   4. Read CLAUDE.md and ./wos/07-tier1-indicator.md")
        print(f"   5. Edit {name}.py to implement your logic")
        print(f"   6. Press F5 to run 'Quick Test' debug configuration")

        return project_dir

    def _interactive_create(self):
        """Interactive project creation wizard"""
        print("=" * 60)
        print("Wolverine Project Creator - Interactive Mode")
        print("=" * 60)
        print()

        # Project name
        while True:
            name = input("Project name (e.g., MyIndicator): ").strip()
            if name and name.replace('_', '').replace('-', '').isalnum():
                break
            print("❌ Invalid name. Use alphanumeric characters, underscores, or hyphens.")

        # Project type
        print("\nProject type:")
        print("  1. Indicator (Tier 1) - Technical analysis indicator")
        print("  2. Composite (Tier 2) - Multi-strategy portfolio manager")
        print("  3. Strategy (Tier 3) - Execution strategy")
        type_choice = input("Select type [1/2/3] (default: 1): ").strip() or '1'
        project_type = {
            '1': 'indicator',
            '2': 'composite',
            '3': 'strategy'
        }.get(type_choice, 'indicator')

        # Markets and securities
        print("\nSelect markets (comma-separated, e.g., DCE,SHFE):")
        print("  Available: DCE, SHFE, CZCE, CFFEX")
        markets_input = input("Markets (default: DCE): ").strip().upper() or 'DCE'
        markets = [m.strip() for m in markets_input.split(',')]

        securities = {}
        for market in markets:
            print(f"\nSecurities for {market}:")
            print(f"  Available: {', '.join(self.VALID_MARKETS.get(market, []))}")
            secs_input = input(f"  Enter securities (comma-separated, default: {self.VALID_MARKETS[market][0] if market in self.VALID_MARKETS else 'all'}): ").strip()

            if secs_input:
                # Split and validate
                secs = [s.strip() for s in secs_input.split(',')]
                # Validate securities
                valid_secs = []
                for sec in secs:
                    if sec in self.VALID_MARKETS.get(market, []):
                        valid_secs.append(sec)
                    else:
                        print(f"  ⚠️  Warning: '{sec}' not in standard {market} securities, including anyway")
                        valid_secs.append(sec)
                securities[market] = valid_secs
            else:
                securities[market] = [self.VALID_MARKETS[market][0]] if market in self.VALID_MARKETS else []

        # Granularities
        print("\nGranularities:")
        print("  Available: 1min, 5min, 15min, 30min, 1h, 4h, 1d")
        gran_input = input("Enter granularities (comma-separated, default: 15min): ").strip() or '15min'
        gran_list = [g.strip() for g in gran_input.split(',')]
        granularities = [self.GRANULARITIES.get(g, 900) for g in gran_list]

        # API Token
        print("\nAPI Token:")
        token = input("Enter API token (or press Enter to use placeholder): ").strip() or 'YOUR_TOKEN_HERE'

        # Confirm
        print("\n" + "=" * 60)
        print("Project Configuration:")
        print("=" * 60)
        print(f"Name:          {name}")
        print(f"Type:          {project_type}")
        print(f"Markets:       {', '.join(markets)}")
        for market, secs in securities.items():
            print(f"  {market:12} {', '.join(secs)}")
        print(f"Granularities: {', '.join([str(g) for g in granularities])}")
        print(f"Token:         {token if token != 'YOUR_TOKEN_HERE' else '(placeholder)'}")
        print("=" * 60)

        confirm = input("\nCreate project? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Aborted.")
            return None

        return self.create_project(name, project_type, markets, securities, granularities, token, False)

    def _create_structure(self, project_dir, name, project_type, markets, securities,
                         granularities, token, category):
        """Create complete project structure"""

        # Create directories
        (project_dir / '.vscode').mkdir(exist_ok=True)
        (project_dir / '.devcontainer').mkdir(exist_ok=True)

        # Create symlink to WOS documentation (readonly reference)
        wos_source = self.base_dir / 'wos'
        wos_link = project_dir / 'wos'
        if wos_source.exists() and not wos_link.exists():
            try:
                # Create relative symlink so it works across different paths
                wos_link.symlink_to(os.path.relpath(wos_source, project_dir))
                print(f"   ✓ Linked WOS documentation (readonly reference)")
            except Exception as e:
                print(f"   ⚠ Warning: Could not create WOS symlink: {e}")
                print(f"     You can still access docs at: {wos_source}")

        # Create main indicator/strategy file
        self._create_main_file(project_dir, name, project_type, markets, securities)

        # Create uin.json
        self._create_uin_json(project_dir, markets, securities, granularities)

        # Create uout.json
        self._create_uout_json(project_dir, markets, securities, granularities, project_type)

        # Create test_resuming_mode.py
        self._create_test_resuming_mode(project_dir, name, category)

        # Create .vscode/launch.json
        self._create_launch_json(project_dir, name, granularities[0], token, category)

        # Create .devcontainer/devcontainer.json
        self._create_devcontainer_json(project_dir, name)

        # Create CLAUDE.md
        self._create_claude_md(project_dir, name, project_type, markets, securities, granularities)

        # Create visualization script template
        self._create_viz_script(project_dir, name)

        # Create README.md
        self._create_project_readme(project_dir, name, project_type, markets, securities)

    def _create_main_file(self, project_dir, name, project_type, markets, securities):
        """Create main indicator/strategy Python file"""

        if project_type == 'indicator':
            template = self._get_indicator_template(name, markets, securities)
        elif project_type == 'composite':
            template = self._get_composite_template(name)
        else:
            template = self._get_strategy_template(name)

        file_path = project_dir / f"{name}.py"
        file_path.write_text(template)
        os.chmod(file_path, 0o755)

    def _get_indicator_template(self, name, markets, securities):
        """Generate indicator template"""

        # Get first market and security for example
        first_market = list(markets)[0] if markets else 'DCE'
        first_sec = securities.get(first_market, ['i'])[0] if securities else 'i'

        return f'''#!/usr/bin/env python3
# coding=utf-8
"""
{name} - Wolverine Indicator

TODO: Add description of what this indicator does
"""

import pycaitlyn as pc
import pycaitlynts3 as pcts3
import pycaitlynutils3 as pcu3
from typing import List

# Framework configuration
use_raw = True
overwrite = True  # Set to False in production
granularity = 900  # Primary granularity (15 minutes)
max_workers = 1
worker_no = None
exports = {{}}
imports = {{}}
metas = {{}}
logger = pcu3.vanilla_logger()


class SampleQuote(pcts3.sv_object):
    """Market data (OHLCV) from global namespace"""

    def __init__(self):
        super().__init__()

        # Metadata - CONSTANTS
        self.meta_name = "SampleQuote"
        self.namespace = pc.namespace_global
        self.revision = (1 << 32) - 1
        self.granularity = 900

        # OHLCV fields (automatically populated by from_sv)
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.volume = None
        self.turnover = None


class {name}(pcts3.sv_object):
    """
    {name} indicator implementation

    TODO: Describe your indicator's purpose and methodology
    """

    def __init__(self):
        super().__init__()

        # Metadata - CONSTANTS (never change during processing)
        self.meta_name = "{name}"
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'{first_market}'
        self.code = b'{first_sec}<00>'
        self.revision = (1 << 32) - 1

        # State variables (automatically persisted)
        self.bar_index = 0
        self.timetag = None

        # TODO: Add your indicator fields here
        self.indicator_value = 0.0
        self.signal = 0

        # Dependency sv_objects
        self.sq = SampleQuote()

    def initialize(self, imports, metas):
        """Initialize schemas for all sv_objects"""
        self.load_def_from_dict(metas)
        self.set_global_imports(imports)

        # Initialize dependencies
        self.sq.load_def_from_dict(metas)
        self.sq.set_global_imports(imports)

    def on_bar(self, bar: pc.StructValue) -> List[pc.StructValue]:
        """
        Process incoming market data bars

        Returns:
            List of StructValue outputs (empty list if no output this cycle)
        """
        ret = []  # ALWAYS return list

        # Extract metadata
        market = bar.get_market()
        code = bar.get_stock_code()
        tm = bar.get_time_tag()
        ns = bar.get_namespace()
        meta_id = bar.get_meta_id()

        # Route to appropriate sv_object
        if self.sq.namespace == ns and self.sq.meta_id == meta_id:
            # Filter for logical contracts only
            if code.endswith(b'<00>'):
                # Set metadata before from_sv
                self.sq.market = market
                self.sq.code = code
                self.sq.granularity = bar.get_granularity()

                # Parse data into sv_object
                self.sq.from_sv(bar)

                # Handle cycle boundaries
                if self.timetag is None:
                    self.timetag = tm

                if self.timetag < tm:
                    # New cycle - process previous cycle's data
                    self._on_cycle_pass(tm)

                    # Serialize state if ready
                    if self.ready_to_serialize():
                        ret.append(self.copy_to_sv())

                    # Update for next cycle
                    self.timetag = tm
                    self.bar_index += 1

        return ret  # ALWAYS return list

    def _on_cycle_pass(self, time_tag):
        """
        Process cycle - implement your indicator logic here

        Args:
            time_tag: Current cycle timestamp
        """
        # Access parsed market data
        current_price = float(self.sq.close)
        current_volume = float(self.sq.volume)
        high = float(self.sq.high)
        low = float(self.sq.low)

        # TODO: Implement your indicator calculations
        # Example: Simple moving average calculation
        self.indicator_value = current_price  # Replace with actual logic

        # TODO: Generate signals based on indicator
        if self.indicator_value > 0:
            self.signal = 1  # Buy signal
        elif self.indicator_value < 0:
            self.signal = -1  # Sell signal
        else:
            self.signal = 0  # Neutral

    def ready_to_serialize(self) -> bool:
        """Determine if state should be serialized"""
        return self.bar_index > 0  # Serialize after first bar


# Global instance
indicator = {name}()


# Framework callbacks (REQUIRED)

async def on_init():
    """Initialize indicator with schemas"""
    global indicator, imports, metas, worker_no
    if worker_no == 1 and metas and imports:
        indicator.initialize(imports, metas)


async def on_bar(bar: pc.StructValue):
    """Process incoming bars"""
    global indicator, worker_no
    if worker_no != 1:
        return []
    return indicator.on_bar(bar)


async def on_ready():
    """Called when framework is ready"""
    pass


async def on_market_open(market, tradeday, time_tag, time_string):
    """Called on market open"""
    pass


async def on_market_close(market, tradeday, timetag, timestring):
    """Called on market close"""
    pass


async def on_reference(market, tradeday, data, timetag, timestring):
    """Called on reference data"""
    pass


async def on_tradeday_begin(market, tradeday, time_tag, time_string):
    """Called at beginning of trade day"""
    pass


async def on_tradeday_end(market, tradeday, timetag, timestring):
    """Called at end of trade day"""
    pass
'''

    def _get_composite_template(self, name):
        """Generate composite strategy template"""
        return f'''#!/usr/bin/env python3
# coding=utf-8
"""
{name} - Wolverine Tier 2 Composite Strategy

TODO: Add description of portfolio management strategy
"""

import pycaitlyn as pc
import strategyc3 as sc3
import pycaitlynutils3 as pcu3
from typing import List, Dict, Tuple
import math

# Framework configuration
use_raw = True
overwrite = True
granularity = 900
max_workers = 1
worker_no = None
exports = {{}}
imports = {{}}
metas = {{}}
logger = pcu3.vanilla_logger()


class {name}(sc3.strategy):
    """
    {name} composite strategy

    Manages multiple basket strategies and allocates capital dynamically.
    TODO: Describe your portfolio management approach
    """

    def __init__(self, initial_money=10000000.00, basket_count=10):
        super().__init__(initial_money)

        # Configuration
        self.basket_count = basket_count

        # Basket management
        self.strategies: List[sc3.strategy] = []
        self.keys: List[Tuple] = []
        self.strategy_map: Dict = {{}}
        self.available_strategies: Dict = {{}}
        self.imported_strategies: Dict = {{}}

        # Portfolio state arrays (one per basket)
        self.markets: List[bytes] = []
        self.codes: List[bytes] = []
        self.metas: List[int] = []
        self.signals: List[int] = []
        self.leverages: List[float] = []
        self.capitals: List[float] = []
        self.pvs: List[float] = []

        # Initialize empty baskets
        self.initialize_empty_baskets()

    def initialize_empty_baskets(self):
        """Initialize basket slots"""
        for i in range(self.basket_count):
            self.keys.append((0, b'', b''))
            basket = sc3.strategy(0.0)
            basket.persistent = False
            self.strategies.append(basket)
        self._save()

    def initialize_imported_strategies(self, imports, metas):
        """Initialize available strategy types from imports"""
        strategies = {{}}

        for _ns in imports.keys():
            for _name in imports[_ns].keys():
                namespace = pc.namespace_global if _ns == 'global' else pc.namespace_private

                for key in metas.keys():
                    if key[0] == namespace and key[1] == _name:
                        meta_def = metas[key]
                        meta_id = meta_def[5]
                        revision = meta_def[0].get_revision()
                        strategies[(namespace, _name)] = [(namespace, meta_id), (_name, revision)]

        for k in strategies.keys():
            if k[0] == pc.namespace_global and k[1] == 'SampleQuote':
                continue
            self.imported_strategies[strategies[k][0]] = strategies[k][1]

    async def on_bar(self, _bar: pc.StructValue) -> pc.StructValue:
        """Main signal processing"""
        # TODO: Implement basket management logic
        # - Process Tier 1 strategy signals
        # - Allocate/deallocate baskets
        # - Update portfolio state

        self._save()
        self._sync()
        return self.copy_to_sv()

    def _save(self):
        """Synchronize arrays with basket states"""
        self.markets = self._get_array('market')
        self.codes = self._get_array('code')
        self.metas = self._get_array('meta_id')
        self.signals = self._get_array('signal')
        self.leverages = self._get_array('leverage')
        self.capitals = self._get_array('pv')
        self.pvs = self._get_array('pv')

    def _get_array(self, prop):
        """Extract property from all baskets"""
        return [getattr(s, prop) for s in self.strategies]

    def _sync(self):
        """Synchronize portfolio metrics"""
        last_pv = self.pv
        self.pv = sum(self.pvs) + self.cash
        self.calc_stats(last_pv)


# Global instance
composite = {name}()


# Framework callbacks

async def on_init():
    """Initialize composite strategy"""
    global composite, imports, metas, worker_no
    if worker_no == 1 and metas and imports:
        composite.initialize_imported_strategies(imports, metas)
        composite.load_def_from_dict(metas)


async def on_bar(bar: pc.StructValue):
    """Process bars"""
    global composite, worker_no
    if worker_no != 1:
        return None
    return await composite.on_bar(bar)


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
'''

    def _get_strategy_template(self, name):
        """Generate execution strategy template"""
        return f'''#!/usr/bin/env python3
# coding=utf-8
"""
{name} - Wolverine Tier 3 Execution Strategy

TODO: Add description
"""

import pycaitlyn as pc
import strategyc3 as sc3
import pycaitlynutils3 as pcu3

# Framework configuration
use_raw = True
overwrite = True
granularity = 900
max_workers = 1
worker_no = None
exports = {{}}
imports = {{}}
metas = {{}}
logger = pcu3.vanilla_logger()


class {name}(sc3.strategy):
    """
    {name} execution strategy

    TODO: Describe execution logic
    """

    def __init__(self, initial_money=10000000.00):
        super().__init__(initial_money)

        # TODO: Add strategy-specific fields

    async def on_bar(self, _bar: pc.StructValue) -> pc.StructValue:
        """Process bars and execute trades"""
        # TODO: Implement execution logic
        return self.copy_to_sv()


# Global instance
strategy = {name}()


# Framework callbacks

async def on_init():
    global strategy, metas, worker_no
    if worker_no == 1 and metas:
        strategy.load_def_from_dict(metas)


async def on_bar(bar: pc.StructValue):
    global strategy, worker_no
    if worker_no != 1:
        return None
    return await strategy.on_bar(bar)


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
'''

    def _create_uin_json(self, project_dir, markets, securities, granularities):
        """Create uin.json configuration"""

        # Build securities array aligned with markets
        market_list = list(markets)
        securities_list = []
        sec_cats_list = []

        for market in market_list:
            secs = securities.get(market, [])
            securities_list.append(secs)
            sec_cats_list.append([1, 2, 3])

        config = {
            "global": {
                "imports": {
                    "SampleQuote": {
                        "fields": [
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume",
                            "turnover"
                        ],
                        "granularities": granularities,
                        "revision": 4294967295,
                        "markets": market_list,
                        "security_categories": sec_cats_list,
                        "securities": securities_list
                    }
                }
            }
        }

        file_path = project_dir / "uin.json"
        file_path.write_text(json.dumps(config, indent=2))

    def _create_uout_json(self, project_dir, markets, securities, granularities, project_type):
        """Create uout.json configuration"""

        # Build securities array aligned with markets
        market_list = list(markets)
        securities_list = []
        sec_cats_list = []

        for market in market_list:
            secs = securities.get(market, [])
            securities_list.append(secs)
            sec_cats_list.append([1, 2, 3])

        # Define output fields based on type
        if project_type == 'indicator':
            fields = [
                "_preserved_field",
                "bar_index",
                "indicator_value",
                "signal"
            ]
            defs = [
                {
                    "field_type": "int64",
                    "display_name": "Preserved Field",
                    "precision": 0,
                    "sample_type": 0,
                    "multiple": 1
                },
                {
                    "field_type": "integer",
                    "display_name": "Bar Index",
                    "precision": 0,
                    "sample_type": 0,
                    "multiple": 1
                },
                {
                    "field_type": "double",
                    "display_name": "Indicator Value",
                    "precision": 6,
                    "sample_type": 0,
                    "multiple": 1
                },
                {
                    "field_type": "integer",
                    "display_name": "Signal",
                    "precision": 0,
                    "sample_type": 0,
                    "multiple": 1
                }
            ]
        else:
            # Composite/strategy fields
            fields = [
                "_preserved_field",
                "portfolio_value",
                "cash",
                "num_positions"
            ]
            defs = [
                {
                    "field_type": "int64",
                    "display_name": "Preserved Field",
                    "precision": 0,
                    "sample_type": 0,
                    "multiple": 1
                },
                {
                    "field_type": "double",
                    "display_name": "Portfolio Value",
                    "precision": 2,
                    "sample_type": 0,
                    "multiple": 1
                },
                {
                    "field_type": "double",
                    "display_name": "Cash",
                    "precision": 2,
                    "sample_type": 0,
                    "multiple": 1
                },
                {
                    "field_type": "integer",
                    "display_name": "Number of Positions",
                    "precision": 0,
                    "sample_type": 0,
                    "multiple": 1
                }
            ]

        config = {
            "private": {
                "markets": market_list,
                "security_categories": sec_cats_list,
                "securities": securities_list,
                "sample_granularities": {
                    "type": "min",
                    "cycles": [granularities[0]],
                    "cycle_lengths": [0]
                },
                "export": {
                    "XXX": {
                        "fields": fields,
                        "defs": defs,
                        "revision": -1
                    }
                }
            }
        }

        file_path = project_dir / "uout.json"
        file_path.write_text(json.dumps(config, indent=2))

    def _create_test_resuming_mode(self, project_dir, name, category):
        """Create test_resuming_mode.py"""
        content = f'''#!/usr/bin/env python3
"""
Replay Consistency Test for {name}

This test validates that the indicator produces identical results when:
1. Running from start to end
2. Resuming from a midpoint

This is MANDATORY for production deployment.
"""

import subprocess
import sys
import argparse


def run_test(start="20250701203204", end="20250710203204", midpoint=None):
    """
    Run replay consistency test

    Args:
        start: Start timestamp (YYYYMMDDHHMMSS)
        end: End timestamp (YYYYMMDDHHMMSS)
        midpoint: Optional midpoint for resume test (YYYYMMDDHHMMSS)
    """
    if midpoint is None:
        # Calculate midpoint (roughly in the middle)
        midpoint = str((int(start) + int(end)) // 2)

    print("=" * 60)
    print("Replay Consistency Test for {name}")
    print("=" * 60)
    print(f"Start:     {{start}}")
    print(f"End:       {{end}}")
    print(f"Midpoint:  {{midpoint}}")
    print()

    base_cmd = [
        "python",
        "/home/wolverine/bin/running/calculator3_test.py",
        "--testcase", ".",
        "--algoname", "{name}",
        "--sourcefile", "{name}.py",
        "--granularity", "900",
        "--tm", "wss://10.99.100.116:4433/tm",
        "--tm-master", "10.99.100.116:6102",
        "--rails", "https://10.99.100.116:4433/private-api/",
        "--token", "YOUR_TOKEN_HERE",
        "--category", "{category}",
        "--is-managed", "1",
        "--restore-length", "864000000",
        "--multiproc", "1"
    ]

    # Test 1: Full run from start to end
    print("Test 1: Full run (start → end)...")
    cmd1 = base_cmd + ["--start", start, "--end", end, "--overwrite"]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)

    if result1.returncode != 0:
        print("❌ Test 1 FAILED")
        print(result1.stderr)
        return False
    print("✅ Test 1 passed")

    # Test 2: Resume from midpoint
    print("\\nTest 2: Resume run (midpoint → end)...")
    cmd2 = base_cmd + ["--start", midpoint, "--end", end]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)

    if result2.returncode != 0:
        print("❌ Test 2 FAILED")
        print(result2.stderr)
        return False
    print("✅ Test 2 passed")

    print("\\n" + "=" * 60)
    print("✅ REPLAY CONSISTENCY TEST PASSED")
    print("=" * 60)
    print("\\nYour indicator produces identical results when resuming from midpoint.")
    print("This is required for production deployment.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay consistency test")
    parser.add_argument("--start", default="20250701203204", help="Start timestamp")
    parser.add_argument("--end", default="20250710203204", help="End timestamp")
    parser.add_argument("--midpoint", help="Midpoint timestamp (auto-calculated if not provided)")

    args = parser.parse_args()

    success = run_test(args.start, args.end, args.midpoint)
    sys.exit(0 if success else 1)
'''
        file_path = project_dir / "test_resuming_mode.py"
        file_path.write_text(content)
        os.chmod(file_path, 0o755)

    def _create_launch_json(self, project_dir, name, granularity, token, category):
        """Create .vscode/launch.json"""
        config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": f"{name} - Quick Test",
                    "type": "debugpy",
                    "request": "launch",
                    "stopOnEntry": False,
                    "python": "python",
                    "program": "/home/wolverine/bin/running/calculator3_test.py",
                    "args": [
                        "--testcase", "${workspaceFolder}/",
                        "--algoname", name,
                        "--sourcefile", f"{name}.py",
                        "--start", "20250703203204",
                        "--end", "20250710203204",
                        "--granularity", str(granularity),
                        "--tm", "wss://10.99.100.116:4433/tm",
                        "--tm-master", "10.99.100.116:6102",
                        "--rails", "https://10.99.100.116:4433/private-api/",
                        "--token", token,
                        "--category", category,
                        "--is-managed", "1",
                        "--restore-length", "864000000",
                        "--multiproc", "1"
                    ],
                    "cwd": "${workspaceFolder}",
                    "envFile": "~/.env",
                    "env": {
                        "PYTHONPATH": "/home/wolverine/bin/running:${env:PYTHONPATH}"
                    },
                    "console": "integratedTerminal"
                },
                {
                    "name": f"{name} - Full Backtest",
                    "type": "debugpy",
                    "request": "launch",
                    "stopOnEntry": False,
                    "python": "python",
                    "program": "/home/wolverine/bin/running/calculator3_test.py",
                    "args": [
                        "--testcase", "${workspaceFolder}/",
                        "--algoname", name,
                        "--sourcefile", f"{name}.py",
                        "--start", "20230101000000",
                        "--end", "20250131000000",
                        "--granularity", str(granularity),
                        "--tm", "wss://10.99.100.116:4433/tm",
                        "--tm-master", "10.99.100.116:6102",
                        "--rails", "https://10.99.100.116:4433/private-api/",
                        "--token", token,
                        "--category", category,
                        "--is-managed", "1",
                        "--restore-length", "864000000",
                        "--multiproc", "1"
                    ],
                    "cwd": "${workspaceFolder}",
                    "envFile": "~/.env",
                    "env": {
                        "PYTHONPATH": "/home/wolverine/bin/running:${env:PYTHONPATH}"
                    },
                    "console": "integratedTerminal"
                },
                {
                    "name": f"{name} - Test Resuming Mode",
                    "type": "debugpy",
                    "request": "launch",
                    "stopOnEntry": False,
                    "python": "python",
                    "program": "${workspaceFolder}/test_resuming_mode.py",
                    "args": [],
                    "cwd": "${workspaceFolder}",
                    "envFile": "~/.env",
                    "env": {
                        "PYTHONPATH": "/home/wolverine/bin/running:${env:PYTHONPATH}"
                    },
                    "console": "integratedTerminal"
                }
            ]
        }

        vscode_dir = project_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        file_path = vscode_dir / "launch.json"
        file_path.write_text(json.dumps(config, indent=4))

    def _create_devcontainer_json(self, project_dir, name):
        """Create .devcontainer/devcontainer.json"""
        config = {
            "name": f"wos-{name.lower()}",
            "image": "glacierx/wos-prod-arm64",
            "remoteUser": "wolverine",
            "runArgs": [
                "--cap-add=SYS_PTRACE",
                "--security-opt",
                "seccomp=unconfined"
            ],
            "appPort": [],
            "customizations": {
                "vscode": {
                    "extensions": [
                        "ms-python.python",
                        "ms-python.vscode-pylance",
                        "ms-python.debugpy",
                        "ms-toolsai.jupyter"
                    ],
                    "settings": {
                        "python.defaultInterpreterPath": "/usr/bin/python3",
                        "python.linting.enabled": True,
                        "python.linting.pylintEnabled": False
                    }
                }
            },
            "postCreateCommand": f"echo '{name} development environment ready!'",
            "remoteEnv": {
                "PYTHONPATH": "/home/wolverine/bin/running:${containerEnv:PYTHONPATH}"
            }
        }

        devcontainer_dir = project_dir / ".devcontainer"
        devcontainer_dir.mkdir(exist_ok=True)
        file_path = devcontainer_dir / "devcontainer.json"
        file_path.write_text(json.dumps(config, indent=4))

    def _create_claude_md(self, project_dir, name, project_type, markets, securities, granularities):
        """Create CLAUDE.md project guidance"""

        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        market_str = ', '.join(markets)
        sec_str = ', '.join([f"{m}: {', '.join(secs)}" for m, secs in securities.items()])
        gran_str = ', '.join([f"{g}s" for g in granularities])

        content = f'''# CLAUDE.md

This file provides guidance to Claude Code when working on the {name} project.

## Project Overview

**Project**: {name}
**Type**: {project_type.title()}
**Markets**: {market_str}
**Securities**: {sec_str}
**Granularities**: {gran_str}

TODO: Add detailed description of what this {project_type} does

## Implementation Status

- [ ] Basic structure created
- [ ] Indicator logic implemented
- [ ] Quick test passing
- [ ] Replay consistency test passing
- [ ] Visualization script created
- [ ] Parameters optimized
- [ ] Full backtest completed
- [ ] Ready for production

## Key Implementation Details

### Input Configuration (uin.json)

Currently configured to import:
- SampleQuote (OHLCV data) from markets: {market_str}
- Granularities: {gran_str}

TODO: Document any additional imports

### Output Configuration (uout.json)

Currently exports:
- _preserved_field (required framework field)
- bar_index (counter)
- indicator_value (main indicator value)
- signal (trading signal: -1, 0, 1)

TODO: Document additional output fields as you add them

### Algorithm Description

TODO: Describe your indicator/strategy algorithm in detail

**Methodology:**
1. TODO: Step 1
2. TODO: Step 2
3. TODO: Step 3

**Parameters:**
TODO: List all tunable parameters and their current values

### State Management

This {project_type} maintains the following state:
- bar_index: Bar counter
- timetag: Current cycle timestamp
- TODO: Add other state variables

All state is automatically persisted via sv_object.

## Critical Framework Rules

### ✅ Always Follow These Doctrines

1. **Multiple Indicator Objects**: Separate instances per commodity
2. **No Fallback Logic**: Trust dependency data format
3. **Always Return List**: Framework callbacks return lists
4. **Logical Contract Filtering**: Only process contracts ending in <00>
5. **Code Format Convention**: DCE/SHFE lowercase, CZCE UPPERCASE

## Development Workflow

### Running Tests

```bash
# Quick test (7 days)
# Press F5 in VS Code, select "{name} - Quick Test"

# Replay consistency (MANDATORY before production)
python test_resuming_mode.py

# Full backtest
# Press F5, select "{name} - Full Backtest"
```

### Debugging

Set breakpoints in {name}.py:
- `on_bar()`: Check data arrival
- `_on_cycle_pass()`: Check calculations
- `ready_to_serialize()`: Check output control

### Visualization

TODO: Create visualization script once indicator is working
```bash
python {name.lower()}_viz.py
```

## Current TODOs

High Priority:
- [ ] TODO: Implement core indicator logic in _on_cycle_pass()
- [ ] TODO: Add proper signal generation logic
- [ ] TODO: Test with quick backtest
- [ ] TODO: Create visualization script

Medium Priority:
- [ ] TODO: Optimize parameters
- [ ] TODO: Add multi-timeframe support if needed
- [ ] TODO: Run full backtest

Low Priority:
- [ ] TODO: Documentation improvements
- [ ] TODO: Performance optimizations

## Notes for Claude Code

When working on this project:

1. **Always check uin.json and uout.json** for configuration
2. **Follow the sv_object pattern** for state management
3. **Use online algorithms** (EMA, not rolling windows)
4. **Ensure replay consistency** (no random values, no system time)
5. **Filter for logical contracts** (`code.endswith(b'<00>')`)
6. **Return lists** from all framework callbacks
7. **Trust dependency data** (no fallback values)

## Resources

- **Framework Documentation**: ./wos/ (complete WOS knowledge base)
- **Working Examples**: Check parent egg directory for Margarita examples
- **Visualization Guide**: ./wos/10-visualization.md
- **Testing Guide**: ./wos/06-backtest.md
- **Quick Reference**: ./wos/INDEX.md

---

Last Updated: {today}
'''
        file_path = project_dir / "CLAUDE.md"
        file_path.write_text(content)

    def _create_viz_script(self, project_dir, name):
        """Create visualization script template"""
        content = f'''#!/usr/bin/env python3
"""
Visualization and Analysis for {name}

TODO: Implement visualization using svr3 data fetching
"""

# TODO: Implement based on ../wos/10-visualization.md
print("Visualization script for {name}")
print("TODO: Implement data fetching and visualization")
'''
        file_path = project_dir / f"{name.lower()}_viz.py"
        file_path.write_text(content)
        os.chmod(file_path, 0o755)

    def _create_project_readme(self, project_dir, name, project_type, markets, securities):
        """Create project README.md"""

        market_str = ', '.join(markets)
        sec_list = []
        for m, secs in securities.items():
            sec_list.append(f"- **{m}**: {', '.join(secs)}")
        sec_str = '\n'.join(sec_list)

        content = f'''# {name}

TODO: Add project description

## Overview

**Type**: {project_type.title()}
**Markets**: {market_str}

**Securities**:
{sec_str}

## Quick Start

### Running Tests

```bash
# Quick test (7 days)
python /home/wolverine/bin/running/calculator3_test.py \\
    --testcase . \\
    --algoname {name} \\
    --sourcefile {name}.py \\
    --start 20250703203204 \\
    --end 20250710203204 \\
    --granularity 900 \\
    --tm wss://10.99.100.116:4433/tm \\
    --tm-master 10.99.100.116:6102 \\
    --rails https://10.99.100.116:4433/private-api/ \\
    --token YOUR_TOKEN \\
    --category 1 \\
    --is-managed 1 \\
    --restore-length 864000000 \\
    --multiproc 1

# Or use VS Code debugger (F5)
```

### Replay Consistency Test

```bash
python test_resuming_mode.py
```

## Project Structure

```
{name}/
├── {name}.py                  # Main implementation
├── uin.json                   # Input configuration
├── uout.json                  # Output configuration
├── test_resuming_mode.py      # Replay consistency test
├── CLAUDE.md                  # Claude Code guidance
├── README.md                  # This file
├── .vscode/
│   └── launch.json           # Debug configurations
└── .devcontainer/
    └── devcontainer.json     # Container configuration
```

## Development

See CLAUDE.md for detailed development guidance.

## Resources

- **WOS Documentation**: ./wos/ (complete framework guide, 12 chapters)
- **Quick Reference**: ./wos/INDEX.md
- **CLAUDE.md**: Project-specific AI guidance
- **Working Examples**: Check parent egg directory for Margarita examples

### Key Documentation

- [Chapter 07: Tier-1 Indicator](./wos/07-tier1-indicator.md) - Start here!
- [Chapter 06: Backtest](./wos/06-backtest.md) - Testing guide
- [Chapter 10: Visualization](./wos/10-visualization.md) - Analysis tools
- [Chapter 02: uin/uout](./wos/02-uin-and-uout.md) - Configuration reference
'''
        file_path = project_dir / "README.md"
        file_path.write_text(content)


def main():
    parser = argparse.ArgumentParser(
        description="Create new Wolverine indicator/strategy project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  ./create_project.py --interactive

  # Create basic indicator
  ./create_project.py --name MyIndicator --type indicator --market DCE --securities i,j

  # Create multi-market indicator
  ./create_project.py --name MultiMarket --type indicator --market DCE,SHFE --securities-DCE i,j --securities-SHFE cu,al

  # Create composite strategy
  ./create_project.py --name MyComposite --type composite
        """
    )

    parser.add_argument('--name', help='Project name')
    parser.add_argument('--type', choices=['indicator', 'composite', 'strategy'],
                       default='indicator', help='Project type (default: indicator)')
    parser.add_argument('--market', '--markets', help='Comma-separated markets (e.g., DCE,SHFE)')
    parser.add_argument('--securities', help='Comma-separated securities for single market')
    parser.add_argument('--granularity', '--granularities',
                       help='Comma-separated granularities in seconds (e.g., 300,900,3600)')
    parser.add_argument('--token', default='YOUR_TOKEN_HERE', help='API token')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode (recommended for first time)')

    # Support per-market securities
    for market in ['DCE', 'SHFE', 'CZCE', 'CFFEX']:
        parser.add_argument(f'--securities-{market}',
                           help=f'Comma-separated securities for {market}')

    args = parser.parse_args()

    creator = ProjectCreator()

    if args.interactive or not args.name:
        creator._interactive_create()
        return

    # Parse markets
    markets = [m.strip().upper() for m in args.market.split(',')] if args.market else ['DCE']

    # Parse securities
    securities = {}
    if args.securities:
        # Single market shorthand
        securities[markets[0]] = [s.strip() for s in args.securities.split(',')]

    # Parse per-market securities
    for market in markets:
        sec_arg = getattr(args, f'securities_{market}', None)
        if sec_arg:
            securities[market] = [s.strip() for s in sec_arg.split(',')]
        elif market not in securities:
            # Use first available security for market
            securities[market] = [creator.VALID_MARKETS.get(market, ['i'])[0]]

    # Parse granularities
    if args.granularity:
        granularities = [int(g.strip()) for g in args.granularity.split(',')]
    else:
        granularities = [900]

    creator.create_project(
        name=args.name,
        project_type=args.type,
        markets=markets,
        securities=securities,
        granularities=granularities,
        token=args.token,
        interactive=False
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
