# Travel Insurance Product Taxonomy - Documentation

## Overview

This taxonomy provides a standardized framework for extracting and comparing travel insurance policy information across multiple products. It organizes policy conditions, benefits, and their specific requirements into three hierarchical layers, enabling systematic analysis and comparison of travel insurance products.

## Purpose

This taxonomy is designed for hackathon participants to:
● Extract policy wording systematically from insurance documents
● Structure unstructured policy text into comparable data points
● Enable cross-product comparison of terms, conditions, and benefits
● Facilitate automated policy analysis and recommendation systems

## Taxonomy Structure

The taxonomy is organized into three distinct layers, each serving a specific purpose in the policy extraction process:

## Layer 1: General Conditions

**Purpose:** Captures fundamental eligibility requirements and exclusions that apply across the entire policy, regardless of specific benefits.

**Categories:**
1. Eligibility Conditions - Requirements that must be met to qualify for coverage
2. Exclusion Conditions - Circumstances under which coverage is not provided

**Key Characteristics:**
● Apply universally to all benefits within a policy
● Must be evaluated before considering specific benefit coverage
● Typically include age requirements, health conditions, travel restrictions, and prohibited activities

**Common Condition Types:**
● **Eligibility:** Trip origin requirements, age limits, health declarations, purchase timing requirements
● **Exclusions:** Pre-existing conditions, high-risk activities, prohibited destinations, war/terrorism, pandemic-related exclusions

**Data Structure for Each Condition:**

```json
{
  "condition": "condition_name",
  "condition_type": "eligibility | exclusion",
  "products": {
    "Product A/B/C": {
      "condition_exist": "boolean",
      "original_text": "extracted policy wording",
      "parameters": {
        "key": "value" // e.g., age limits, time periods
      }
    }
  }
}
```

**Example Conditions:**
● trip_start_singapore - Policy requires trip to commence from Singapore
● age_eligibility - Age restrictions for coverage
● pre_existing_conditions - Exclusion for pre-existing medical conditions
● dangerous_activities_exclusion - Exclusion for high-risk sports/activities

## Layer 2: Benefits

**Purpose:** Identifies all coverage benefits offered by each product, representing what the policy will pay for under qualifying circumstances.

**Key Characteristics:**
● Lists all available benefits/coverages in the policy
● Benefits are standardized across products for comparison
● Each benefit has its own coverage limits and sub-conditions (defined in Layer 3)

**Benefit Categories:**
1. Personal Accident Coverage - Death, disability, injury-related benefits
2. Medical Coverage - Medical expenses, hospitalization, evacuation
3. Trip-Related Coverage - Cancellation, delay, curtailment, disruption
4. Baggage Coverage - Loss, damage, or delay of personal belongings
5. Liability Coverage - Personal liability, legal expenses
6. Specialized Coverage - Activities, golf, rental vehicle, home protection

**Data Structure for Each Benefit:**

```json
{
  "benefit_name": "benefit_identifier",
  "parameters": [], // benefit-level parameters if applicable
  "products": {
    "Product A/B/C": {
      "condition_exist": "boolean",
      "parameters": {
        "coverage_limit": "amount",
        "sub_limits": {}
      }
    }
  }
}
```

**Example Benefits:**
● overseas_medical_expenses - Coverage for medical treatment abroad
● trip_cancellation - Reimbursement for cancelled trips
● delayed_baggage - Compensation for delayed luggage
● personal_liability - Coverage for third-party injury/damage claims
● adventurous_activities - Coverage for specified adventure sports

## Layer 3: Benefit-Specific Conditions

**Purpose:** Defines the specific eligibility requirements and exclusions that apply to individual benefits, providing granular detail on when and how each benefit pays out.

**Key Characteristics:**
● Each condition is tied to a specific benefit from Layer 2
● Defines the circumstances under which a benefit is payable or excluded
● Contains specific parameters like time limits, minimum thresholds, documentation requirements

**Condition Categories:**
1. Benefit Eligibility - Specific requirements to trigger the benefit
2. Benefit Exclusion - Circumstances where the benefit does not apply

**Data Structure for Each Benefit-Specific Condition:**

```json
{
  "benefit_name": "parent_benefit",
  "condition": "specific_condition_name",
  "condition_type": "benefit_eligibility | benefit_exclusion",
  "parameters": [], // condition-level parameters
  "products": {
    "Product A/B/C": {
      "condition_exist": "boolean",
      "original_text": "extracted policy wording",
      "parameters": {
        "time_limit": "90 days",
        "minimum_amount": "$500",
        // other specific parameters
      }
    }
  }
}
```

**Example Benefit-Specific Conditions:**

**For overseas_medical_expenses:**
● overseas_medical_necessity_requirement - Treatment must be medically necessary
● medical_expenses_incurred_within_time_limit - Claims must be filed within specified timeframe
● excluded_treatments - Specific medical treatments not covered
● pre_trip_medical_requirement - Must not have received medical advice against travel

**For trip_cancellation:**
● covered_cancellation_reasons - Eligible reasons for cancellation
● unavoidable_cancellation_of_trip - Cancellation must be unavoidable
● known_circumstances_cancellation - Exclusion for known circumstances at purchase

**For delayed_baggage:**
● minimum_delay_duration - Minimum hours of delay required
● baggage_delayed_overseas - Must occur outside Singapore
● written_proof_requirement - Documentation needed from carrier

## Practical Extraction Example

**Policy Text:**
"You must be between 18 and 70 years old to purchase this policy. Coverage commences when you leave Singapore and ends when you return."

**Extraction:**

**Layer 1 Condition: age_eligibility**

```json
{
  "condition": "age_eligibility",
  "condition_type": "eligibility",
  "products": {
    "Product A": {
      "condition_exist": true,
      "original_text": "You must be between 18 and 70 years old to purchase this policy.",
      "parameters": {
        "minimum_age": 18,
        "maximum_age": 70,
        "unit": "years"
      }
    }
  }
}
```

**Layer 1 Condition: trip_start_singapore**

```json
{
  "condition": "trip_start_singapore",
  "condition_type": "eligibility",
  "products": {
    "Product A": {
      "condition_exist": true,
      "original_text": "Coverage commences when you leave Singapore and ends when you return.",
      "parameters": {
        "departure_location": "Singapore",
        "return_location": "Singapore"
      }
    }
  }
}
```

## Summary

This taxonomy provides the foundation for systematic policy analysis. By carefully extracting information into this structure enables powerful comparison, matching, and recommendation capabilities for travel insurance products.

## Quick Reference: Three-Layer Structure

| Layer | What It Captures | Scope | Example |
|-------|------------------|-------|---------|
| Layer 1 | General Conditions | Policy-wide eligibility & exclusions | Age limits, pre-existing conditions, dangerous activities |
| Layer 2 | Benefits | Available coverages | Medical expenses, trip cancellation, baggage delay |
| Layer 3 | Benefit-Specific Conditions | Requirements & exclusions per benefit | Time limits, minimum thresholds, proof requirements |
