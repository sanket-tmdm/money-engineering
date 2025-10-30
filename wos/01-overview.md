# Chapter 01: Wolverine Framework Overview

## Introduction

The Wolverine financial engineering framework is a production-grade, high-performance system designed for developing, testing, and deploying quantitative trading indicators and strategies. This chapter provides a comprehensive overview of the framework's architecture, capabilities, and development workflow.

## What is Wolverine?

Wolverine is a **time-series financial analysis framework** that enables developers to:

- Build **stateless, resumable indicators** with automatic state persistence
- Develop **multi-timeframe analysis** across different granularities
- Create **composite strategies** that manage multiple indicators as portfolios
- **Backtest strategies** with historical market data
- Deploy to **production environments** with guaranteed replay consistency
- Integrate **machine learning models** for enhanced decision-making

### Key Characteristics

**Production-Ready Architecture**
- Proven in live trading environments
- Microsecond-precision timestamp handling
- Multi-worker parallel processing
- Robust state management and persistence

**Developer-Friendly**
- Python-based development
- VS Code integration with debugging support
- Comprehensive visualization tools
- Claude Code AI assistance

**Scalable Design**
- Processes millions of bars efficiently
- Bounded memory usage (O(1) growth)
- Multi-commodity parallel analysis
- Distributed worker architecture

## Framework Architecture

### Three-Tier System

Wolverine implements a hierarchical three-tier architecture that separates concerns and enables modular development:

```
┌─────────────────────────────────────────────────────┐
│  TIER 1: Basic Indicators                           │
│  ---------------------------------------------------│
│  • Technical analysis (MACD, RSI, Bollinger, etc.)  │
│  • Pattern recognition (head & shoulders, flags)    │
│  • Volume analysis                                  │
│  • Custom calculations                              │
│  • Market regime detection                          │
│                                                     │
│  Output: Individual signals and metrics             │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ Individual Signals
                   ▼
┌─────────────────────────────────────────────────────┐
│  TIER 2: Composite Strategies (Portfolio Managers)  │
│  ---------------------------------------------------│
│  • Aggregate signals from multiple Tier 1 indicators│
│  • Dynamic basket management                        │
│  • Capital allocation across strategies             │
│  • Risk management and position sizing              │
│  • Strategy selection and rotation                  │
│  • Performance tracking and attribution             │
│                                                     │
│  Output: Portfolio-level signals and allocations    │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ Portfolio Signals
                   ▼
┌─────────────────────────────────────────────────────┐
│  TIER 3: Execution Strategies                       │
│  ---------------------------------------------------│
│  • Order execution and routing                      │
│  • Position management                              │
│  • Broker interface integration                     │
│  • Slippage and commission modeling                 │
│  • Real-time risk monitoring                        │
│                                                     │
│  Output: Actual trades and positions                │
└─────────────────────────────────────────────────────┘
```

### Component Overview

**Core Framework Components:**

1. **pycaitlyn (pc)** - Core framework library
   - Fundamental data types (StructValue, IndexSchema)
   - Namespace definitions (global/private)
   - Market data structures
   - Memory management

2. **pycaitlynts3 (pcts3)** - Time-series object framework
   - sv_object base class for automatic serialization
   - Schema management and version control
   - State persistence mechanisms

3. **strategyc3 (sc3)** - Strategy execution framework
   - strategy base class for portfolio management
   - Signal processing and execution
   - PnL tracking and performance metrics

4. **calculator3.py** - Core processing engine
   - Message handling and routing
   - Multi-worker coordination
   - State serialization/deserialization
   - Data replay and backtesting

5. **calculator3_test.py** - Testing and backtest launcher
   - Entry point for all backtesting
   - Worker process management
   - Configuration parsing
   - Results collection

## Data Flow Architecture

### End-to-End Data Flow

```
Market Exchanges
    │
    ├─→ DCE (Dalian)
    ├─→ SHFE (Shanghai)
    ├─→ CZCE (Zhengzhou)
    └─→ CFFEX (China Financial)
          ↓
    [Live Market Data Feed]
          ↓
    Time Machine Server
    • Historical data storage
    • Real-time data streaming
    • Websocket connections
          ↓
    calculator3.py
    • Message decoding
    • Worker distribution
    • Data routing
          ↓
    ┌─────────────────────┐
    │  Multi-Worker Pool  │
    ├─────────────────────┤
    │ Worker 0: Master    │
    │ Worker 1: Processor │
    │ Worker N: Processor │
    └─────────────────────┘
          ↓
    Your Indicator/Strategy
    • on_bar() processing
    • State updates
    • Signal generation
          ↓
    StructValue Output
    • Serialized results
    • State persistence
    • Framework storage
          ↓
    Visualization & Analysis
    • Performance metrics
    • Parameter validation
    • Optimization insights
```

### Message Processing Pipeline

1. **Market Data Arrival**
   - Raw market data from exchanges
   - Tick data, OHLCV bars, order book updates

2. **Time Machine Processing**
   - Timestamp normalization
   - Data aggregation to various granularities
   - Storage and indexing

3. **Calculator3 Routing**
   - Message decode (CMD_TC_REALTIME_PUSH)
   - Worker assignment based on (market, code)
   - Namespace and meta_id routing

4. **Indicator Processing**
   - on_bar() callback invocation
   - Data parsing via sv_object
   - Calculation execution
   - State serialization

5. **Result Collection**
   - Output aggregation
   - Performance tracking
   - Storage or forwarding to next tier

## Development Workflow

### Standard Development Cycle

```
1. DESIGN PHASE
   ├─ Define indicator concept
   ├─ Specify input requirements (markets, granularities)
   ├─ Design output fields and precision
   └─ Plan state management approach

2. SETUP PHASE
   ├─ Create project folder structure
   ├─ Configure uin.json (input universe)
   ├─ Configure uout.json (output universe)
   ├─ Set up VS Code debug configuration
   └─ Generate template files

3. IMPLEMENTATION PHASE
   ├─ Implement sv_object classes for data structures
   ├─ Write indicator calculation logic
   ├─ Implement cycle boundary handling
   ├─ Add state serialization control
   └─ Write framework callbacks

4. TESTING PHASE
   ├─ Quick test (7-day backtest)
   ├─ Replay consistency test (MANDATORY)
   ├─ Full backtest (historical data)
   └─ Edge case testing

5. VISUALIZATION PHASE
   ├─ Create visualization script
   ├─ Validate parameter effectiveness
   ├─ Analyze indicator behavior
   └─ Generate optimization recommendations

6. OPTIMIZATION PHASE
   ├─ Review visualization insights
   ├─ Adjust parameters based on data
   ├─ Re-test with new parameters
   └─ Iterate until satisfactory

7. DEPLOYMENT PHASE
   ├─ Final replay consistency validation
   ├─ Full backtest with production config
   ├─ Documentation update (CLAUDE.md)
   └─ Production deployment
```

### Development Tools

**VS Code Integration:**
- Debugger with breakpoint support
- Integrated terminal for testing
- Dev Containers for consistent environment
- Extension support (Python, debugpy)

**Claude Code AI Assistant:**
- Project structure generation
- Code template creation
- Parameter optimization suggestions
- Bug diagnosis and fixes
- Documentation generation

**Visualization Tools:**
- Jupyter notebook integration
- matplotlib/seaborn plotting
- Performance metrics dashboard
- Parameter sensitivity analysis
- Random timepoint deep-dive

**Testing Framework:**
- calculator3_test.py for backtesting
- test_resuming_mode.py for replay consistency
- Custom date range testing
- Multi-commodity validation

## Supported Markets and Instruments

### Chinese Futures Markets

**DCE (Dalian Commodity Exchange)**
- i: Iron ore
- j: Coking coal
- m: Soybean meal
- y: Soybean oil
- p: Palm oil
- c: Corn
- a: Soybeans
- b: Soybean meal
- v: PVC
- l: LLDPE
- pp: Polypropylene

**SHFE (Shanghai Futures Exchange)**
- cu: Copper
- al: Aluminum
- zn: Zinc
- pb: Lead
- ni: Nickel
- sn: Tin
- au: Gold
- ag: Silver
- rb: Rebar
- wr: Wire rod
- hc: Hot-rolled coil
- fu: Fuel oil
- bu: Bitumen
- ru: Rubber
- sc: Crude oil

**CZCE (Zhengzhou Commodity Exchange)**
- **Note: CZCE uses UPPERCASE codes**
- TA: PTA (purified terephthalic acid)
- MA: Methanol
- FG: Glass
- SR: White sugar
- CF: Cotton
- RM: Rapeseed meal
- OI: Rapeseed oil
- WH: Wheat
- AP: Apple
- CJ: Red dates

**CFFEX (China Financial Futures Exchange)**
- IF: CSI 300 Index Futures
- IC: CSI 500 Index Futures
- IH: SSE 50 Index Futures
- T: 10-Year Treasury Bond Futures
- TF: 5-Year Treasury Bond Futures

### Contract Types

**Logical Contracts (Continuous):**
- Format: `i<00>`, `cu<00>`, `TA<00>`
- Represents continuous contract with automatic rolling
- Used for technical analysis and indicators
- **This is what indicators process**

**Monthly Contracts (Specific Delivery):**
- Format: `i2501`, `cu2412`, `TA2503`
- Specific delivery month contracts
- Used for physical delivery trading
- **Indicators typically ignore these**

### Market Data Availability

**Granularities Available:**
- **SampleQuote (global namespace)**: 60s (1min), 300s (5min), 900s (15min), 1800s (30min), 3600s (1H), 86400s (1D), weekly, monthly
- **ZampleQuote (private namespace)**: Custom sampled data for missing granularities (e.g., 14400s for 4H)

**Data Fields:**
- open: Opening price
- high: Highest price
- low: Lowest price
- close: Closing price
- volume: Trading volume
- turnover: Trading turnover (volume-weighted price data)

## Core Concepts

### 1. sv_object Pattern

The foundational pattern for all data structures:

```python
class MyIndicator(pcts3.sv_object):
    def __init__(self):
        super().__init__()

        # Metadata (constants - never change during processing)
        self.meta_name = "MyIndicator"
        self.namespace = pc.namespace_private
        self.granularity = 900
        self.market = b'DCE'
        self.code = b'i<00>'
        self.revision = (1 << 32) - 1

        # State variables (automatically persisted)
        self.bar_index = 0
        self.indicator_value = 0.0
```

**Key Features:**
- Automatic serialization/deserialization
- All instance variables automatically persisted
- Type safety across resume operations
- Memory-efficient binary format

### 2. Stateless Design

Indicators must be **stateless and resumable**:

- All critical state in output fields (defined in uout.json)
- No unbounded memory growth (use online algorithms)
- Can resume from any midpoint with identical results
- Use EMAs instead of rolling windows
- Persistent counters instead of growing lists

### 3. Multi-Timeframe Analysis

Process data across multiple timeframes simultaneously:

```python
# 5-minute analysis
self.ema_5min = update_ema(price_5min, self.ema_5min, alpha_5min)

# 15-minute analysis
self.ema_15min = update_ema(price_15min, self.ema_15min, alpha_15min)

# 1-hour analysis
self.ema_1h = update_ema(price_1h, self.ema_1h, alpha_1h)

# Combined signal
self.combined_signal = (0.5 * signal_5min +
                       0.3 * signal_15min +
                       0.2 * signal_1h)
```

### 4. Replay Consistency

**MANDATORY** requirement: Indicator must produce identical results when:
- Running full calculation from start to end
- Resuming calculation from any midpoint

This ensures:
- Production reliability
- Debugging capability
- State management correctness

### 5. Multi-Commodity Architecture

When building indicators for multiple commodities:

**CRITICAL: Use separate indicator instances per commodity**

```python
class MultiCommodityManager:
    def __init__(self):
        self.indicators = {
            b'i': CommodityIndicator(b'i', b'DCE'),
            b'cu': CommodityIndicator(b'cu', b'SHFE'),
            b'TA': CommodityIndicator(b'TA', b'CZCE'),  # UPPERCASE for CZCE
        }
```

**Never reuse a single indicator for multiple commodities** - leads to state contamination.

## Framework Doctrines

### 🚨 Doctrine 1: Multiple Indicator Objects

**NEVER** reuse indicator instances across commodities.

### 🚨 Doctrine 2: No Fallback Logic

**NEVER** use fallback values for dependency data - trust the data format.

### 🚨 Doctrine 3: Always Return List

Framework callbacks **MUST** always return a list, never single objects or None.

### 🚨 Doctrine 4: Logical Contract Filtering

**ONLY** process logical contracts ending in `<00>`.

### 🚨 Doctrine 5: Code Format Convention

- DCE/SHFE: lowercase (`b'i'`, `b'cu'`)
- CZCE: UPPERCASE (`b'TA'`, `b'MA'`)

## Performance Characteristics

### Memory Usage

**Bounded O(1) Memory:**
- Use online algorithms (EMA, Welford's variance)
- Avoid growing lists/deques
- Persistent counters for aggregates
- No full historical storage

**Example - Bad vs Good:**

```python
# ❌ BAD: O(n) memory growth
self.price_history = []  # Grows forever
self.price_history.append(price)
avg = sum(self.price_history) / len(self.price_history)

# ✅ GOOD: O(1) memory
self.ema_price = 0.1 * price + 0.9 * self.ema_price
```

### Processing Speed

**Typical Performance:**
- Process 1M bars in ~1-2 minutes (single worker)
- Microsecond-level timestamp precision
- Minimal serialization overhead
- Efficient multi-worker parallelization

### Scalability

**Multi-Worker Architecture:**
- Worker 0: Master coordinator
- Worker 1+: Parallel processors
- Automatic load balancing by (market, code)
- Linear scaling with worker count

## Getting Started

### Prerequisites

1. **Docker** - For containerized development environment
2. **VS Code** - With Dev Containers extension
3. **Claude Code** - AI assistant for development
4. **System Requirements**:
   - 8GB RAM minimum (16GB recommended)
   - 20GB free disk space
   - Linux/macOS/Windows with WSL2

### Quick Start

```bash
# 1. Copy egg package to create your project
cp -r /path/to/egg my_indicator_project
cd my_indicator_project

# 2. Open in VS Code
code .

# 3. Reopen in container (Cmd/Ctrl+Shift+P → "Dev Containers: Reopen in Container")

# 4. Inside container, use Claude Code
claude "Create a basic indicator project called SimpleMA"

# 5. Start development!
```

## Learning Path

### Recommended Reading Order

1. **Chapter 01: Overview** (this chapter) - Framework architecture
2. **Chapter 02: uin.json and uout.json** - Configuration files
3. **Chapter 03: Programming Basics and CLI** - Base classes and tools
4. **Chapter 04: StructValue and sv_object** - Core data structures
5. **Chapter 05: Singularity** - State management patterns
6. **Chapter 06: Backtest** - Testing and validation
7. **Chapter 07: Tier-1 Indicator** - Basic indicator development
8. **Chapter 08: Tier-2 Composite** - Portfolio management
9. **Chapter 09: Tier-3 Strategy** - Execution strategies
10. **Chapter 10: Visualization** - Analysis and validation
11. **Chapter 11: Fine-Tune and Iterate** - Optimization workflow
12. **Chapter 12: Example Project** - End-to-end implementation

### Hands-On Approach

After reading chapters 1-4:
- Create a simple moving average indicator
- Run a quick backtest
- Visualize the results

After chapters 5-7:
- Build a more complex multi-timeframe indicator
- Validate replay consistency
- Optimize parameters

After chapters 8-9:
- Create a composite strategy
- Manage multiple indicators
- Implement risk management

## Common Use Cases

### Technical Analysis Indicators

- Moving averages (SMA, EMA, WMA)
- Momentum indicators (RSI, MACD, Stochastic)
- Volatility indicators (Bollinger Bands, ATR, Keltner Channels)
- Volume indicators (OBV, Money Flow Index, A/D Line)
- Trend indicators (ADX, Parabolic SAR, Ichimoku)

### Pattern Recognition

- Chart patterns (head & shoulders, triangles, flags)
- Candlestick patterns (doji, engulfing, hammer)
- Support/resistance levels
- Breakout detection
- Reversal signals

### Market Regime Detection

- Volatility regime classification
- Trend regime identification
- Mean reversion vs momentum regimes
- Market phase analysis (accumulation, markup, distribution, markdown)

### Multi-Timeframe Analysis

- Higher timeframe trend + lower timeframe entry
- Divergence analysis across timeframes
- Timeframe correlation studies
- Regime consistency across scales

### Portfolio Management

- Multi-strategy allocation
- Dynamic basket management
- Risk parity approaches
- Strategy rotation based on performance

## Resources and Support

### Documentation

- **WOS Knowledge Base**: Comprehensive guide (chapters 01-12)
- **Code Examples**: Working implementations in examples/
- **Template Projects**: Starter templates in templates/
- **API Reference**: Framework API documentation

### Development Tools

- **VS Code Debugger**: Step-through debugging
- **Claude Code**: AI-assisted development
- **Visualization Scripts**: Performance analysis
- **Testing Framework**: Replay consistency validation

### Community and Support

- **GitHub Issues**: Bug reports and feature requests
- **Community Forum**: Questions and discussions
- **Example Projects**: Learn from existing implementations
- **Claude Code Integration**: In-IDE assistance

## Summary

This overview introduced the Wolverine framework:

- **Three-tier architecture** separating indicators, portfolios, and execution
- **sv_object pattern** for automatic state management
- **Stateless design** principles for resumable calculations
- **Multi-timeframe analysis** capabilities
- **Production-ready** architecture with replay consistency
- **Developer-friendly** tools and AI assistance

The framework enables developers to focus on indicator logic while the framework handles:
- State serialization and persistence
- Multi-worker parallel processing
- Data routing and message handling
- Backtesting and validation
- Production deployment

**Next Chapter**: [Chapter 02 - uin.json and uout.json](./02-uin-and-uout.md) - Learn how to configure input and output specifications for your indicators.
