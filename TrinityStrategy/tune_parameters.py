#!/usr/bin/env python3
# coding=utf-8
"""
Trinity Strategy - Parameter Tuning Script (Phase 1.5)

Analyzes 1-year of Scout indicator data to determine optimal thresholds
for each instrument using statistical percentile analysis.

Outputs:
  - trinity_parameters.json: Instrument-specific tuned parameters
  - tier-1_output/tuning/: Visualization charts showing distributions

Usage:
    python tune_parameters.py --start 20240101000000 --end 20250101000000
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import svr3

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette('husl')

# Server configuration (matches TrinityStrategy_viz.ipynb)
RAILS_URL = 'https://10.99.100.116:4433/private-api/'
WS_URL = 'wss://10.99.100.116:4433/tm'
TM_MASTER = ('10.99.100.116', 6102)
TOKEN = '58abd12edbde042536637bfba9d20d5faf366ef481651cdbb046b1c3b4f7bf7a97ae7a2e6e5dc8fe05cd91147c8906f8a82aaa1bb1356d8cb3d6a076eadf5b5a'

# Strategy configuration
INDICATOR_NAME = 'TrinityStrategy'
GRANULARITY = 900  # 15-minute bars
NAMESPACE = 'private'

# Default percentiles for threshold calculation
ADX_RIVER_PERCENTILE = 0.70  # 70th percentile = strong trending
ADX_LAKE_PERCENTILE = 0.30   # 30th percentile = ranging market
CONVICTION_BULL_PERCENTILE = 0.80  # 80th percentile = strong bullish
CONVICTION_BEAR_PERCENTILE = 0.20  # 20th percentile = strong bearish


def parse_uout_instruments() -> List[Tuple[str, str]]:
    """Parse uout.json to get all (market, security) pairs for tuning

    Returns:
        List of tuples: [(market, code), ...] e.g., [('DCE', 'i<00>'), ('SHFE', 'cu<00>'), ...]
    """
    with open('uout.json', 'r') as f:
        config = json.load(f)

    # Access nested structure
    private_config = config['private']
    markets = private_config['markets']
    securities_per_market = private_config['securities']

    # Build instrument list
    instruments = []
    for market, securities in zip(markets, securities_per_market):
        for security in securities:
            instruments.append((market, f'{security}<00>'))

    return instruments


class TrinityParameterTuner:
    """Parameter tuner for Trinity Strategy using statistical analysis"""

    def __init__(self, token: str, start: int, end: int):
        self.token = token
        self.start_date = start
        self.end_date = end
        self.client = None
        self.data_cache = {}  # {instrument: DataFrame}

    async def connect(self):
        """Establish connection to server (Pattern 2: reusable connection)"""
        print(f'🔄 Connecting to server...')

        # Initialize with dummy market/code (will be updated per fetch)
        self.client = svr3.sv_reader(
            self.start_date, self.end_date,
            INDICATOR_NAME, GRANULARITY, NAMESPACE,
            'symbol', ['DCE'], ['i<00>'],  # Dummy initial values
            False, RAILS_URL, WS_URL,
            '', '', TM_MASTER,
        )
        self.client.token = self.token

        await self.client.login()
        await self.client.connect()
        self.client.ws_task = asyncio.create_task(self.client.ws_loop())
        await self.client.shakehand()

        print(f'✓ Connected to server')

    async def fetch_instrument_data(self, market: str, code: str) -> pd.DataFrame:
        """Fetch Scout indicator data for specified instrument"""
        print(f'📊 Fetching data for {market}/{code}...')

        # Update markets/codes for this fetch (Pattern 2)
        self.client.markets = [market]
        self.client.codes = [code]
        self.client.namespace = NAMESPACE

        ret = await self.client.save_by_symbol()
        data = ret[1][1]

        if not data:
            print(f'⚠ No data returned for {market}/{code}')
            return pd.DataFrame()

        df = pd.DataFrame(data)

        if 'time_tag' in df.columns:
            df['datetime'] = pd.to_datetime(df['time_tag'], unit='ms')
            df = df.sort_values('datetime')

        print(f'✓ Loaded {len(df)} data points for {market}/{code}')
        if 'datetime' in df.columns:
            print(f'  Date range: {df["datetime"].min()} to {df["datetime"].max()}')

        return df

    async def fetch_all_instruments(self, instruments: List[Tuple[str, str]]) -> Dict[str, pd.DataFrame]:
        """Fetch data for all instruments and cache results"""
        print(f'\n{"="*70}')
        print(f'Fetching data for {len(instruments)} instruments...')
        print(f'{"="*70}\n')

        for market, code in instruments:
            instrument_key = f'{market}/{code}'
            df = await self.fetch_instrument_data(market, code)

            if not df.empty:
                self.data_cache[instrument_key] = df
            else:
                print(f'⚠ Skipping {instrument_key} - no data')

        print(f'\n✓ Successfully fetched data for {len(self.data_cache)} instruments\n')
        return self.data_cache

    async def close(self):
        """Clean up connection"""
        if self.client:
            self.client.stop()
            await self.client.join()
            print('✓ Connection closed')

    @staticmethod
    def calculate_instrument_parameters(df: pd.DataFrame, instrument_name: str) -> Dict:
        """Calculate optimal parameters for a single instrument using percentile analysis

        Args:
            df: DataFrame with Scout indicator data
            instrument_name: Instrument identifier (e.g., 'DCE/i<00>')

        Returns:
            Dict with tuned parameters
        """
        print(f'\n{"="*70}')
        print(f'Analyzing {instrument_name}...')
        print(f'{"="*70}')

        params = {
            'instrument': instrument_name,
            'data_points': len(df)
        }

        # ADX Threshold Analysis
        if 'adx_value' in df.columns:
            adx_data = df['adx_value'].dropna()

            river_threshold = adx_data.quantile(ADX_RIVER_PERCENTILE)
            lake_threshold = adx_data.quantile(ADX_LAKE_PERCENTILE)

            params['adx_river_threshold'] = round(float(river_threshold), 2)
            params['adx_lake_threshold'] = round(float(lake_threshold), 2)
            params['adx_mean'] = round(float(adx_data.mean()), 2)
            params['adx_std'] = round(float(adx_data.std()), 2)

            print(f'\n📈 ADX Analysis:')
            print(f'   River Threshold (70th percentile): {params["adx_river_threshold"]:.2f}')
            print(f'   Lake Threshold (30th percentile): {params["adx_lake_threshold"]:.2f}')
            print(f'   Mean: {params["adx_mean"]:.2f}, Std: {params["adx_std"]:.2f}')

        # Conviction Oscillator Threshold Analysis
        if 'conviction_oscillator' in df.columns:
            conv_data = df['conviction_oscillator'].dropna()

            bull_threshold = conv_data.quantile(CONVICTION_BULL_PERCENTILE)
            bear_threshold = conv_data.quantile(CONVICTION_BEAR_PERCENTILE)

            params['conviction_bull_threshold'] = round(float(bull_threshold), 4)
            params['conviction_bear_threshold'] = round(float(bear_threshold), 4)
            params['conviction_mean'] = round(float(conv_data.mean()), 4)
            params['conviction_std'] = round(float(conv_data.std()), 4)

            print(f'\n📊 Conviction Oscillator Analysis:')
            print(f'   Bull Threshold (80th percentile): {params["conviction_bull_threshold"]:.4f}')
            print(f'   Bear Threshold (20th percentile): {params["conviction_bear_threshold"]:.4f}')
            print(f'   Mean: {params["conviction_mean"]:.4f}, Std: {params["conviction_std"]:.4f}')

        # Bollinger Band Width Analysis
        if all(col in df.columns for col in ['upper_band', 'lower_band', 'middle_band']):
            bb_data = df[['upper_band', 'lower_band', 'middle_band']].dropna()

            bb_width = bb_data['upper_band'] - bb_data['lower_band']
            bb_width_pct = (bb_width / bb_data['middle_band']) * 100

            params['bb_width_mean'] = round(float(bb_width.mean()), 2)
            params['bb_width_std'] = round(float(bb_width.std()), 2)
            params['bb_width_pct_mean'] = round(float(bb_width_pct.mean()), 2)
            params['bb_width_pct_std'] = round(float(bb_width_pct.std()), 2)

            # Calculate extreme volatility thresholds (90th percentile)
            params['bb_width_high_volatility'] = round(float(bb_width.quantile(0.90)), 2)
            params['bb_width_low_volatility'] = round(float(bb_width.quantile(0.10)), 2)

            print(f'\n📉 Bollinger Band Analysis:')
            print(f'   Width Mean: {params["bb_width_mean"]:.2f}, Std: {params["bb_width_std"]:.2f}')
            print(f'   Width % Mean: {params["bb_width_pct_mean"]:.2f}%, Std: {params["bb_width_pct_std"]:.2f}%')
            print(f'   High Volatility Threshold (90th percentile): {params["bb_width_high_volatility"]:.2f}')
            print(f'   Low Volatility Threshold (10th percentile): {params["bb_width_low_volatility"]:.2f}')

        # DI+/DI- Statistics (informational)
        if all(col in df.columns for col in ['di_plus', 'di_minus']):
            di_plus = df['di_plus'].dropna()
            di_minus = df['di_minus'].dropna()

            params['di_plus_mean'] = round(float(di_plus.mean()), 2)
            params['di_minus_mean'] = round(float(di_minus.mean()), 2)

            print(f'\n📍 Directional Indicators:')
            print(f'   DI+ Mean: {params["di_plus_mean"]:.2f}')
            print(f'   DI- Mean: {params["di_minus_mean"]:.2f}')

        return params

    @staticmethod
    def plot_threshold_analysis(df: pd.DataFrame, params: Dict, output_dir: str):
        """Generate visualization charts showing distributions with threshold lines

        Args:
            df: DataFrame with Scout indicator data
            params: Calculated parameters with thresholds
            output_dir: Directory to save charts
        """
        instrument_name = params['instrument']
        print(f'\n📊 Generating visualization charts for {instrument_name}...')

        # Create 3x1 subplot layout
        fig, axes = plt.subplots(3, 1, figsize=(14, 16))
        fig.suptitle(f'Parameter Tuning Analysis - {instrument_name}',
                    fontsize=14, fontweight='bold', y=0.995)

        # ========================================================================
        # Panel 1: ADX Distribution
        # ========================================================================
        if 'adx_value' in df.columns:
            ax = axes[0]
            adx_data = df['adx_value'].dropna()

            # Histogram with KDE
            ax.hist(adx_data, bins=50, alpha=0.6, color='steelblue',
                   edgecolor='black', density=True, label='Distribution')

            # KDE overlay
            from scipy import stats
            kde = stats.gaussian_kde(adx_data)
            x_range = np.linspace(adx_data.min(), adx_data.max(), 200)
            ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')

            # Threshold lines
            river_thresh = params['adx_river_threshold']
            lake_thresh = params['adx_lake_threshold']

            ax.axvline(river_thresh, color='green', linestyle='--', linewidth=2.5,
                      label=f'River Threshold: {river_thresh:.2f}')
            ax.axvline(lake_thresh, color='orange', linestyle='--', linewidth=2.5,
                      label=f'Lake Threshold: {lake_thresh:.2f}')
            ax.axvline(adx_data.mean(), color='red', linestyle=':', linewidth=2,
                      label=f'Mean: {params["adx_mean"]:.2f}')

            ax.set_xlabel('ADX Value', fontsize=11, fontweight='bold')
            ax.set_ylabel('Density', fontsize=11, fontweight='bold')
            ax.set_title('ADX Trend Strength Distribution', fontsize=12, fontweight='bold')
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3)

            # Add statistics text box
            stats_text = (f'N = {len(adx_data):,}\n'
                         f'Mean = {params["adx_mean"]:.2f}\n'
                         f'Std = {params["adx_std"]:.2f}\n'
                         f'Trending: ADX > {river_thresh:.2f}\n'
                         f'Ranging: ADX < {lake_thresh:.2f}')
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # ========================================================================
        # Panel 2: Conviction Oscillator Distribution
        # ========================================================================
        if 'conviction_oscillator' in df.columns:
            ax = axes[1]
            conv_data = df['conviction_oscillator'].dropna()

            # Histogram with KDE
            ax.hist(conv_data, bins=60, alpha=0.6, color='purple',
                   edgecolor='black', density=True, label='Distribution')

            # KDE overlay
            kde = stats.gaussian_kde(conv_data)
            x_range = np.linspace(conv_data.min(), conv_data.max(), 200)
            ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')

            # Threshold lines
            bull_thresh = params['conviction_bull_threshold']
            bear_thresh = params['conviction_bear_threshold']

            ax.axvline(bull_thresh, color='green', linestyle='--', linewidth=2.5,
                      label=f'Bull Threshold: {bull_thresh:.4f}')
            ax.axvline(bear_thresh, color='red', linestyle='--', linewidth=2.5,
                      label=f'Bear Threshold: {bear_thresh:.4f}')
            ax.axvline(0, color='black', linestyle='-', linewidth=1.5,
                      label='Neutral: 0.0')

            ax.set_xlabel('Conviction Oscillator', fontsize=11, fontweight='bold')
            ax.set_ylabel('Density', fontsize=11, fontweight='bold')
            ax.set_title('Volume Conviction Distribution', fontsize=12, fontweight='bold')
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3)

            # Statistics text box
            stats_text = (f'N = {len(conv_data):,}\n'
                         f'Mean = {params["conviction_mean"]:.4f}\n'
                         f'Std = {params["conviction_std"]:.4f}\n'
                         f'Bullish: > {bull_thresh:.4f}\n'
                         f'Bearish: < {bear_thresh:.4f}')
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # ========================================================================
        # Panel 3: Bollinger Band Width Distribution
        # ========================================================================
        if all(col in df.columns for col in ['upper_band', 'lower_band']):
            ax = axes[2]
            bb_data = df[['upper_band', 'lower_band']].dropna()
            bb_width = bb_data['upper_band'] - bb_data['lower_band']

            # Histogram with KDE
            ax.hist(bb_width, bins=50, alpha=0.6, color='teal',
                   edgecolor='black', density=True, label='Distribution')

            # KDE overlay
            kde = stats.gaussian_kde(bb_width)
            x_range = np.linspace(bb_width.min(), bb_width.max(), 200)
            ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')

            # Threshold lines
            high_vol = params['bb_width_high_volatility']
            low_vol = params['bb_width_low_volatility']

            ax.axvline(high_vol, color='red', linestyle='--', linewidth=2.5,
                      label=f'High Volatility: {high_vol:.2f}')
            ax.axvline(low_vol, color='blue', linestyle='--', linewidth=2.5,
                      label=f'Low Volatility: {low_vol:.2f}')
            ax.axvline(bb_width.mean(), color='orange', linestyle=':', linewidth=2,
                      label=f'Mean: {params["bb_width_mean"]:.2f}')

            ax.set_xlabel('Bollinger Band Width', fontsize=11, fontweight='bold')
            ax.set_ylabel('Density', fontsize=11, fontweight='bold')
            ax.set_title('Bollinger Band Volatility Distribution', fontsize=12, fontweight='bold')
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3)

            # Statistics text box
            stats_text = (f'N = {len(bb_width):,}\n'
                         f'Mean = {params["bb_width_mean"]:.2f}\n'
                         f'Std = {params["bb_width_std"]:.2f}\n'
                         f'High Vol (90%): {high_vol:.2f}\n'
                         f'Low Vol (10%): {low_vol:.2f}')
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # Save figure
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'threshold_analysis.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        print(f'✓ Saved visualization: {output_path}')


async def main():
    """Main execution function"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Tune Trinity Strategy parameters using statistical analysis'
    )
    parser.add_argument('--start', type=int, required=True,
                       help='Start date (format: YYYYMMDDHHMMSS)')
    parser.add_argument('--end', type=int, required=True,
                       help='End date (format: YYYYMMDDHHMMSS)')
    parser.add_argument('--output', type=str, default='trinity_parameters.json',
                       help='Output JSON file path (default: trinity_parameters.json)')
    parser.add_argument('--no-visualize', action='store_true',
                       help='Skip visualization generation')

    args = parser.parse_args()

    print('='*70)
    print('Trinity Strategy Parameter Tuning')
    print('='*70)
    print(f'Date Range: {args.start} to {args.end}')
    print(f'Output: {args.output}')
    print(f'Visualizations: {"Disabled" if args.no_visualize else "Enabled"}')
    print('='*70)

    # Parse instruments from uout.json
    instruments = parse_uout_instruments()
    print(f'\n📊 Found {len(instruments)} instruments to tune:')
    for market, code in instruments:
        print(f'   - {market}/{code}')

    # Initialize tuner and fetch data
    tuner = TrinityParameterTuner(TOKEN, args.start, args.end)
    await tuner.connect()

    # Fetch all instrument data
    data_cache = await tuner.fetch_all_instruments(instruments)

    # Close connection (data is cached)
    await tuner.close()

    if not data_cache:
        print('\n❌ No data fetched. Exiting.')
        return

    # Analyze each instrument and calculate parameters
    all_parameters = {}

    for instrument_key, df in data_cache.items():
        # Calculate parameters
        params = TrinityParameterTuner.calculate_instrument_parameters(df, instrument_key)

        # Extract instrument code (e.g., 'DCE/i<00>' -> 'i<00>')
        instrument_code = instrument_key.split('/')[-1]
        all_parameters[instrument_code] = params

        # Generate visualizations if requested
        if not args.no_visualize:
            # Create output directory
            chart_dir = f'tier-1_output/tuning/{instrument_code.replace("<00>", "")}'
            os.makedirs(chart_dir, exist_ok=True)

            # Generate charts
            TrinityParameterTuner.plot_threshold_analysis(df, params, chart_dir)

    # Create final JSON output structure
    output_data = {
        'tuning_metadata': {
            'date_range': [args.start, args.end],
            'data_points_per_instrument': {
                code: params['data_points']
                for code, params in all_parameters.items()
            },
            'generated_at': datetime.now().isoformat(),
            'percentiles': {
                'adx_river': ADX_RIVER_PERCENTILE,
                'adx_lake': ADX_LAKE_PERCENTILE,
                'conviction_bull': CONVICTION_BULL_PERCENTILE,
                'conviction_bear': CONVICTION_BEAR_PERCENTILE
            }
        },
        'instruments': all_parameters
    }

    # Save to JSON file
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f'\n{"="*70}')
    print(f'✅ Parameter tuning complete!')
    print(f'{"="*70}')
    print(f'\n📄 Parameters saved to: {args.output}')

    if not args.no_visualize:
        print(f'📊 Visualizations saved to: tier-1_output/tuning/')

    print(f'\n📋 Summary:')
    for code, params in all_parameters.items():
        print(f'\n  {code}:')
        print(f'    ADX River: {params.get("adx_river_threshold", "N/A")}')
        print(f'    ADX Lake: {params.get("adx_lake_threshold", "N/A")}')
        print(f'    Conviction Bull: {params.get("conviction_bull_threshold", "N/A")}')
        print(f'    Conviction Bear: {params.get("conviction_bear_threshold", "N/A")}')


if __name__ == '__main__':
    asyncio.run(main())
