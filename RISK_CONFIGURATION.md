# Risk Configuration Guide

## Overview

High-risk destinations and activity multipliers are now **configurable via environment variables** instead of being hardcoded. This allows easy adjustment without code changes.

## Environment Variables

Add these to your `backend-mcp/.env` file:

```bash
# Risk Configuration
HIGH_RISK_DESTINATIONS=USA,Canada,Japan,Switzerland
HIGH_RISK_MULTIPLIER=1.3
HIGH_RISK_ACTIVITY_MULTIPLIER=1.4
```

## Configuration Details

### 1. `HIGH_RISK_DESTINATIONS`
**Format**: Comma-separated list of country names  
**Default**: `["USA", "Canada", "Japan", "Switzerland"]`  
**Purpose**: Countries with higher medical/travel costs where premiums should increase

**Common high-risk destinations**:
- **USA, Canada**: Expensive healthcare ($1000+ for ER visit)
- **Japan**: High cost of living, language barriers
- **Switzerland**: Expensive medical care and services
- **UK, France**: Higher than average costs
- **Australia**: Remote locations, expensive medical evacuation

**Example**:
```bash
# Minimal risk list
HIGH_RISK_DESTINATIONS=USA,Canada

# Comprehensive list
HIGH_RISK_DESTINATIONS=USA,Canada,Japan,Switzerland,UK,France,Australia,New Zealand
```

### 2. `HIGH_RISK_MULTIPLIER`
**Format**: Decimal number  
**Default**: `1.3` (30% increase)  
**Purpose**: Premium multiplier for high-risk destinations

**Examples**:
```bash
HIGH_RISK_MULTIPLIER=1.0   # No increase (treat all destinations equally)
HIGH_RISK_MULTIPLIER=1.2   # 20% increase for high-risk
HIGH_RISK_MULTIPLIER=1.5   # 50% increase for high-risk
HIGH_RISK_MULTIPLIER=2.0   # Double the premium for high-risk
```

**Impact**:
- Base premium: $700
- With `1.3` multiplier: $910 (30% increase)
- With `1.5` multiplier: $1,050 (50% increase)

### 3. `HIGH_RISK_ACTIVITY_MULTIPLIER`
**Format**: Decimal number  
**Default**: `1.4` (40% increase)  
**Purpose**: Premium multiplier when `has_high_risk_activities = true`

**High-risk activities** (detected automatically):
- Skiing, snowboarding
- Scuba diving
- Bungee jumping
- Skydiving
- Mountain climbing
- Extreme sports

**Examples**:
```bash
HIGH_RISK_ACTIVITY_MULTIPLIER=1.0   # No increase (don't charge extra)
HIGH_RISK_ACTIVITY_MULTIPLIER=1.3   # 30% increase
HIGH_RISK_ACTIVITY_MULTIPLIER=1.5   # 50% increase
HIGH_RISK_ACTIVITY_MULTIPLIER=2.0   # Double the premium
```

## How Premiums Are Calculated

```python
# 1. Base calculation
premium = base_rate × travelers × duration

# 2. Age adjustments
if age > 65: premium × 1.5
if age < 18: premium × 0.7

# 3. HIGH_RISK_DESTINATIONS check
if destination in HIGH_RISK_DESTINATIONS:
    premium × HIGH_RISK_MULTIPLIER

# 4. HIGH_RISK_ACTIVITY_MULTIPLIER check
if has_high_risk_activities:
    premium × HIGH_RISK_ACTIVITY_MULTIPLIER

# 5. Pre-existing conditions
if has_pre_existing and policy_covers_it:
    premium × 1.8
```

## Example Pricing Scenarios

### Scenario 1: Japan Trip (High-Risk Destination)
```
Base: $700
× 1.3 (high-risk destination) = $910
```

### Scenario 2: Thailand Trip + Diving (High-Risk Activity)
```
Base: $500
× 1.4 (high-risk activity) = $700
```

### Scenario 3: USA Trip + Skiing (Both High-Risk)
```
Base: $600
× 1.3 (destination) = $780
× 1.4 (activity) = $1,092
```

### Scenario 4: Morocco Trip (Low-Risk)
```
Base: $500
(no multipliers) = $500
```

## Customization Tips

### Conservative Pricing (Lower Premiums)
```bash
HIGH_RISK_DESTINATIONS=USA,Switzerland  # Only most expensive
HIGH_RISK_MULTIPLIER=1.2                # Modest 20% increase
HIGH_RISK_ACTIVITY_MULTIPLIER=1.2       # Modest 20% increase
```

### Aggressive Pricing (Higher Premiums)
```bash
HIGH_RISK_DESTINATIONS=USA,Canada,Japan,Switzerland,UK,France,Australia
HIGH_RISK_MULTIPLIER=1.5                # 50% increase
HIGH_RISK_ACTIVITY_MULTIPLIER=1.6       # 60% increase
```

### Flat Pricing (No Risk Adjustments)
```bash
HIGH_RISK_DESTINATIONS=                 # Empty list
HIGH_RISK_MULTIPLIER=1.0                # No increase
HIGH_RISK_ACTIVITY_MULTIPLIER=1.0       # No increase
```

## Implementation

The configuration is loaded from `app/config.py`:

```python
class Settings(BaseSettings):
    # Risk Configuration
    high_risk_destinations: list[str] = ["USA", "Canada", "Japan", "Switzerland"]
    high_risk_multiplier: float = 1.3
    high_risk_activity_multiplier: float = 1.4
```

Used in `app/services/quote_service.py`:

```python
# Destination risk
if trip_details.destination_country in settings.high_risk_destinations:
    total_premium *= settings.high_risk_multiplier

# Activity risk
if trip_details.has_high_risk_activities:
    total_premium *= settings.high_risk_activity_multiplier
```

## Testing

After changing configuration:
1. **Restart the server** (config loaded at startup)
2. Test pricing:

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "31yo to Japan Dec 1-10 for skiing"}' | \
  jq '.quotes[0].premium'
```

Expected changes:
- Add "Switzerland" to list → Switzerland trips become more expensive
- Change multiplier to 1.5 → All high-risk trips 50% more expensive
- Set to 1.0 → No risk premium applied

