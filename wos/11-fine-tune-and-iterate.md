# Chapter 11: Fine-tune and Iterate

**Learning objectives:**
- Analyze visualization results to identify issues
- Optimize indicator parameters systematically
- Implement A/B testing for parameters
- Iterate improvements efficiently
- Avoid overfitting

**Previous:** [10 - Visualization](10-visualization.md) | **Next:** [12 - Example Project](12-example-project.md)

---

## Overview

Fine-tuning transforms a working indicator into a robust, production-ready strategy. This chapter covers the iterative optimization process.

## Optimization Workflow

```
1. Baseline Implementation
   ↓
2. Visualization & Analysis
   ↓
3. Identify Issues
   ↓
4. Parameter Adjustment
   ↓
5. Backtest Validation
   ↓
6. Replay Consistency Test
   ↓
7. Repeat 2-6 until satisfactory
   ↓
8. Production Deployment
```

## Identifying Common Issues

### Issue 1: Too Many Signals

**Symptoms:**
- High signal frequency
- Low confidence scores
- Poor signal-to-noise ratio

**Diagnosis:**

```python
# Analyze signal frequency
signals_per_day = df.groupby(df['timestamp'].dt.date)['signal'].sum()
print(f"Average signals per day: {signals_per_day.mean():.1f}")

# Check confidence distribution
low_confidence = (df['confidence'] < 0.5).sum() / len(df)
print(f"Low confidence signals: {low_confidence:.1%}")
```

**Solution:**

```python
# Increase thresholds
self.min_signal_strength = 0.5  # Was 0.3
self.min_confidence = 0.6       # Was 0.4
```

### Issue 2: Delayed Signals

**Symptoms:**
- Signals lag price movements
- Missing early entry points
- Late exits

**Diagnosis:**

```python
# Calculate signal lag
df['price_change'] = df['close'].diff()
df['signal_change'] = df['signal'].diff()

# Correlation at different lags
for lag in range(1, 10):
    corr = df['price_change'].corr(df['signal_change'].shift(lag))
    print(f"Lag {lag}: {corr:.3f}")
```

**Solution:**

```python
# Use faster EMA
self.alpha_fast = 2.0 / 6.0   # Was 2.0 / 11.0 (5-period instead of 10)
```

### Issue 3: False Signals in Ranging Markets

**Symptoms:**
- Many signals during consolidation
- Whipsaw trades
- Low win rate

**Diagnosis:**

```python
# Analyze signals by volatility regime
high_vol = df[df['volatility'] > df['volatility'].quantile(0.75)]
low_vol = df[df['volatility'] < df['volatility'].quantile(0.25)]

print(f"Signals in high vol: {high_vol['signal'].abs().sum()}")
print(f"Signals in low vol: {low_vol['signal'].abs().sum()}")
```

**Solution:**

```python
# Add volatility filter
if self.volatility < self.vol_threshold:
    self.signal = 0  # No signals in low volatility
```

## Parameter Optimization

### Grid Search

```python
def grid_search(param_grid):
    """Test all parameter combinations."""
    results = []

    for fast_period in param_grid['fast_period']:
        for slow_period in param_grid['slow_period']:
            for confidence_threshold in param_grid['confidence_threshold']:
                # Run backtest
                metrics = run_backtest(
                    fast_period=fast_period,
                    slow_period=slow_period,
                    confidence_threshold=confidence_threshold
                )

                results.append({
                    'fast_period': fast_period,
                    'slow_period': slow_period,
                    'confidence_threshold': confidence_threshold,
                    'sharpe': metrics['sharpe'],
                    'max_dd': metrics['max_dd'],
                    'win_rate': metrics['win_rate']
                })

    return pd.DataFrame(results)

# Define parameter grid
param_grid = {
    'fast_period': [5, 10, 15, 20],
    'slow_period': [20, 30, 40, 50],
    'confidence_threshold': [0.3, 0.4, 0.5, 0.6]
}

# Run grid search
results = grid_search(param_grid)

# Find best parameters
best = results.nlargest(5, 'sharpe')
print(best)
```

### Walk-Forward Optimization

```python
def walk_forward_optimization(data, train_period, test_period):
    """Walk-forward analysis to avoid overfitting."""
    results = []

    for start in range(0, len(data), test_period):
        # Training period
        train_data = data[start:start+train_period]

        # Find optimal parameters on training data
        best_params = optimize_parameters(train_data)

        # Test on next period
        test_data = data[start+train_period:start+train_period+test_period]
        performance = backtest_with_params(test_data, best_params)

        results.append({
            'start': start,
            'train_sharpe': best_params['sharpe'],
            'test_sharpe': performance['sharpe'],
            'params': best_params
        })

    return pd.DataFrame(results)
```

## A/B Testing

```python
class ABTester:
    """Compare two parameter sets."""

    def __init__(self, params_a, params_b):
        self.params_a = params_a
        self.params_b = params_b

    def run_test(self, data):
        """Run both versions and compare."""
        results_a = self.backtest(data, self.params_a)
        results_b = self.backtest(data, self.params_b)

        print("=== A/B Test Results ===")
        print(f"Version A Sharpe: {results_a['sharpe']:.3f}")
        print(f"Version B Sharpe: {results_b['sharpe']:.3f}")

        # Statistical significance test
        p_value = self.ttest(results_a['returns'], results_b['returns'])
        print(f"P-value: {p_value:.4f}")

        if p_value < 0.05:
            print("Difference is statistically significant!")
        else:
            print("No significant difference.")

        return results_a, results_b

    def backtest(self, data, params):
        """Run backtest with parameters."""
        # Implementation
        pass

    def ttest(self, returns_a, returns_b):
        """Perform t-test."""
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(returns_a, returns_b)
        return p_value
```

## Avoiding Overfitting

### Best Practices

1. **Use out-of-sample testing**

```python
# Split data
train_size = int(len(data) * 0.7)
train_data = data[:train_size]
test_data = data[train_size:]

# Optimize on train
best_params = optimize(train_data)

# Validate on test
performance = validate(test_data, best_params)
```

2. **Limit parameter complexity**

```python
# ❌ BAD - Too many parameters
class Overfit(pcts3.sv_object):
    def __init__(self):
        self.param1 = 0.1
        self.param2 = 0.2
        # ... 20 more parameters
        self.param23 = 0.95

# ✅ GOOD - Few key parameters
class Simple(pcts3.sv_object):
    def __init__(self):
        self.fast_period = 10
        self.slow_period = 20
        self.threshold = 0.5
```

3. **Use robust metrics**

```python
# Focus on risk-adjusted returns
metrics = {
    'sharpe_ratio': calculate_sharpe(returns),
    'sortino_ratio': calculate_sortino(returns),
    'calmar_ratio': calculate_calmar(returns),
    'max_drawdown': calculate_max_dd(equity_curve)
}

# Not just raw returns
# raw_returns = final_value / initial_value  # ❌ Can be misleading
```

4. **Test across market conditions**

```python
# Split by market regime
bull_market = data[data['trend'] == 'bull']
bear_market = data[data['trend'] == 'bear']
sideways = data[data['trend'] == 'sideways']

# Test in each regime
for regime, regime_data in [('bull', bull_market), 
                            ('bear', bear_market),
                            ('sideways', sideways)]:
    performance = backtest(regime_data, params)
    print(f"{regime}: Sharpe={performance['sharpe']:.2f}")
```

## Iteration Checklist

Before each iteration:
- [ ] Visualize current performance
- [ ] Identify specific issues
- [ ] Form hypothesis for improvement
- [ ] Change ONE thing at a time
- [ ] Run full backtest
- [ ] Test replay consistency
- [ ] Compare to previous version
- [ ] Document changes

## Summary

Fine-tuning process:
1. Visualize and analyze
2. Identify specific issues
3. Optimize parameters systematically
4. Avoid overfitting
5. Validate improvements
6. Iterate

Key principles:
- Change one thing at a time
- Use out-of-sample testing
- Focus on robust metrics
- Test across market conditions
- Document all changes

**Next**: Complete example project walkthrough.

---

**Previous:** [10 - Visualization](10-visualization.md) | **Next:** [12 - Example Project](12-example-project.md)
