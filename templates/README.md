# Wolverine Indicator & Strategy Templates

This directory contains template files for quickly creating new indicators and strategies.

## Available Templates

### 1. Basic Indicator Template
Location: `basic_indicator/`

Use this template to create a Tier 1 indicator. It includes:
- Indicator.py template with sv_object pattern
- uin.json with standard market data configuration
- uout.json with common output fields
- test_resuming_mode.py for replay consistency testing

### 2. Composite Strategy Template
Location: `composite_strategy/`

Use this template to create a Tier 2 portfolio manager. It includes:
- CompositeStrategy.py with basket management
- uin.json importing other indicators
- uout.json with portfolio-level fields
- Risk management patterns

### 3. VS Code Debug Configuration
Location: `.vscode/launch.json.template`

Standard debug configuration with placeholders:
- `{{PROJECT_NAME}}`: Your indicator name
- `{{GRANULARITY}}`: Time granularity (e.g., 300, 900)
- `{{API_TOKEN}}`: Your authentication token
- `{{CATEGORY}}`: 1 for indicator, 2 for composite

## Using Templates with Claude Code

### Quick Project Creation

```bash
# In the container, use Claude Code:
claude "Create a new indicator project called MomentumMaster using the basic indicator template"
```

Claude Code will:
1. Copy the appropriate template
2. Replace all `{{PLACEHOLDERS}}` with actual values
3. Create the project directory structure
4. Set up debug configurations
5. Generate CLAUDE.md with project-specific guidance

### Manual Template Usage

```bash
# Copy template to your project
cp -r templates/basic_indicator MyIndicator/
cd MyIndicator

# Replace placeholders
sed -i 's/{{PROJECT_NAME}}/MyIndicator/g' *.py *.json .vscode/launch.json
sed -i 's/{{GRANULARITY}}/900/g' .vscode/launch.json
sed -i 's/{{API_TOKEN}}/your_token_here/g' .vscode/launch.json
sed -i 's/{{CATEGORY}}/1/g' .vscode/launch.json

# Customize the implementation
# Edit MyIndicator.py to add your logic
```

## Template Placeholders

Common placeholders used in templates:

- **{{PROJECT_NAME}}**: Name of your indicator/strategy
- **{{GRANULARITY}}**: Primary time granularity in seconds
  - 60: 1 minute
  - 300: 5 minutes
  - 900: 15 minutes
  - 3600: 1 hour
  - 14400: 4 hours
  - 86400: 1 day

- **{{API_TOKEN}}**: Your Wolverine API authentication token
- **{{CATEGORY}}**: Indicator category
  - 1: Basic indicator (Tier 1)
  - 2: Composite strategy (Tier 2)
  - 3: Execution strategy (Tier 3)

- **{{MARKET}}**: Market identifier
  - DCE, SHFE, CZCE, CFFEX

- **{{COMMODITIES}}**: Commodity codes as comma-separated list
  - DCE/SHFE: lowercase (i, j, cu, al, rb, sc, fu)
  - CZCE: UPPERCASE (TA, MA, FG, SR)

## Customization Guide

### Modifying uin.json

Add or remove markets:
```json
{
  "markets": ["DCE", "SHFE"],  // Add/remove as needed
  "securities": [
    ["i", "j"],      // DCE commodities
    ["cu", "al"]     // SHFE commodities
  ]
}
```

Add granularities for multi-timeframe analysis:
```json
{
  "granularities": [300, 900, 3600]  // 5min, 15min, 1H
}
```

### Modifying uout.json

Add custom output fields:
```json
{
  "fields": [
    "_preserved_field",  // MUST BE FIRST
    "your_field_1",
    "your_field_2"
  ],
  "defs": [
    {"field_type": "int64", "precision": 0, ...},
    {"field_type": "double", "precision": 6, ...},
    {"field_type": "integer", "precision": 0, ...}
  ]
}
```

### Modifying Indicator Logic

In the .py file, customize:

```python
class YourIndicator(pcts3.sv_object):
    def __init__(self):
        super().__init__()

        # Update metadata
        self.meta_name = "YourIndicator"
        self.market = b'DCE'  # Your market
        self.code = b'i<00>'  # Your commodity

        # Add your indicator fields
        self.your_value = 0.0
        self.your_signal = 0

    def _on_cycle_pass(self, time_tag):
        """Your indicator logic here"""
        current_price = float(self.sq.close)

        # Your calculations
        self.your_value = calculate_something(current_price)
        self.your_signal = generate_signal(self.your_value)
```

## Best Practices

1. **Start with Templates**: Don't start from scratch
2. **Replace All Placeholders**: Search for `{{` to find them all
3. **Test Early**: Run quick test immediately after creation
4. **Follow Doctrines**: Adhere to framework requirements (see WOS docs)
5. **Document Changes**: Update CLAUDE.md with your customizations

## Common Issues

### Issue: Template placeholders still present after creation

**Solution**: Make sure to replace all `{{PLACEHOLDER}}` values
```bash
grep -r "{{" .  # Find remaining placeholders
```

### Issue: Import errors when running

**Solution**: Check PYTHONPATH includes framework location
```bash
export PYTHONPATH="/home/wolverine/bin/running:$PYTHONPATH"
```

### Issue: Token authentication fails

**Solution**: Update {{API_TOKEN}} with your actual token in launch.json

## Getting Help

- **Claude Code**: Use for automated project setup
- **WOS Documentation**: See `../wos/` for comprehensive guides
- **Working Examples**: Check parent Margarita project
- **Framework Source**: Examine `/home/wolverine/bin/running/` files

## Contributing

If you create useful templates:
1. Test thoroughly with multiple commodities
2. Document all customization points
3. Add to this templates/ directory
4. Update this README
5. Submit for inclusion in egg package

---

**Quick Start**: Use Claude Code for fastest setup!

```bash
claude "Create indicator project MyIndicator from basic template with DCE i commodity at 15min granularity"
```
