"""
Alternative plain-text comparison formatter for clients that don't render markdown
"""

def format_comparison_plain_text(comparison: dict) -> str:
    """
    Format comparison in plain text with ASCII art and spacing
    Better for terminals and clients that don't render markdown
    """
    policies = comparison.get("policies", [])
    
    if not policies:
        return "No policies available for comparison."
    
    lines = []
    
    # Header
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"  POLICY COMPARISON - {len(policies)} Options".center(80))
    lines.append("=" * 80)
    lines.append("")
    
    # Quick comparison (simple text table)
    lines.append("QUICK COMPARISON:")
    lines.append("-" * 80)
    lines.append("")
    
    # Policy names row
    policy_names = [p.get('policy_name', 'Unknown')[:18] for p in policies]
    lines.append(f"{'Feature':<20} | " + " | ".join(f"{name:^18}" for name in policy_names))
    lines.append("-" * 80)
    
    # Age Range
    age_ranges = []
    for policy in policies:
        gc = policy.get('general_conditions', {})
        age_min = gc.get('age_min', 'N/A')
        age_max = gc.get('age_max', 'N/A')
        age_ranges.append(f"{age_min}-{age_max} yrs" if age_min != 'N/A' else 'N/A')
    lines.append(f"{'Age Range':<20} | " + " | ".join(f"{age:^18}" for age in age_ranges))
    
    # Medical Coverage
    medical_coverages = []
    for policy in policies:
        benefits = policy.get('benefits', [])
        medical_max = 0
        for b in benefits:
            if 'medical' in b.get('benefit_name', '').lower():
                coverage = b.get('coverage_limit', 0) or 0
                medical_max = max(medical_max, coverage)
        medical_coverages.append(f"${medical_max:,}" if medical_max > 0 else 'N/A')
    lines.append(f"{'Medical Coverage':<20} | " + " | ".join(f"{cov:^18}" for cov in medical_coverages))
    
    # Pre-existing
    pre_existing = []
    for policy in policies:
        gc = policy.get('general_conditions', {})
        covered = "YES" if gc.get('pre_existing_covered') else "NO"
        pre_existing.append(covered)
    lines.append(f"{'Pre-existing':<20} | " + " | ".join(f"{pe:^18}" for pe in pre_existing))
    
    # Total Benefits
    benefit_counts = []
    for policy in policies:
        count = len(policy.get('benefits', []))
        benefit_counts.append(str(count))
    lines.append(f"{'Total Benefits':<20} | " + " | ".join(f"{bc:^18}" for bc in benefit_counts))
    
    lines.append("-" * 80)
    lines.append("")
    
    # Detailed breakdown
    lines.append("DETAILED BREAKDOWN:")
    lines.append("=" * 80)
    lines.append("")
    
    for i, policy in enumerate(policies, 1):
        policy_name = policy.get('policy_name', 'Unknown Policy')
        lines.append(f"{i}. {policy_name.upper()}")
        lines.append("-" * 40)
        
        # Eligibility
        gc = policy.get('general_conditions', {})
        if gc:
            lines.append("  Eligibility:")
            lines.append(f"    • Age: {gc.get('age_min', 'N/A')}-{gc.get('age_max', 'N/A')} years")
            lines.append(f"    • Max trip: {gc.get('max_trip_duration_days', 'N/A')} days")
            lines.append(f"    • Pre-existing: {'YES - Covered' if gc.get('pre_existing_covered') else 'NO - Not covered'}")
            lines.append("")
        
        # Key benefits (top 3 medical)
        benefits = policy.get('benefits', [])
        medical_benefits = [
            (b.get('benefit_name', ''), b.get('coverage_limit', 0) or 0)
            for b in benefits
            if 'medical' in b.get('benefit_name', '').lower() and (b.get('coverage_limit', 0) or 0) > 0
        ]
        
        if medical_benefits:
            lines.append("  Key Medical Coverage:")
            for name, limit in medical_benefits[:3]:
                lines.append(f"    • {name}: ${limit:,}")
            if len(medical_benefits) > 3:
                lines.append(f"    • ...and {len(medical_benefits) - 3} more benefits")
            lines.append("")
        
        lines.append("")
    
    # Recommendation
    lines.append("=" * 80)
    lines.append("RECOMMENDATION:")
    lines.append("=" * 80)
    
    recommendation = comparison.get("recommendation")
    if recommendation:
        # Wrap text to 78 characters
        import textwrap
        for line in textwrap.wrap(recommendation, width=78):
            lines.append(f"  {line}")
    else:
        lines.append("  Choose based on your needs:")
        for policy in policies:
            policy_name = policy.get('policy_name', 'Unknown')
            gc = policy.get('general_conditions', {})
            
            if gc.get('pre_existing_covered'):
                lines.append(f"    • {policy_name}: Best for pre-existing conditions")
            else:
                benefits_count = len(policy.get('benefits', []))
                if benefits_count > 30:
                    lines.append(f"    • {policy_name}: Best for comprehensive coverage")
                else:
                    lines.append(f"    • {policy_name}: Best for budget travelers")
    
    lines.append("")
    lines.append("Would you like pricing for any of these policies?")
    lines.append("")
    
    return "\n".join(lines)


# Test the formatter
if __name__ == "__main__":
    # Sample data
    sample_comparison = {
        "policies": [
            {
                "policy_name": "Scootsurance",
                "general_conditions": {"age_min": 12, "age_max": 74, "pre_existing_covered": False},
                "benefits": [
                    {"benefit_name": "Medical Expenses", "coverage_limit": 70000},
                    {"benefit_name": "Accidental Death", "coverage_limit": 100000}
                ]
            },
            {
                "policy_name": "TravelEasy Pre-Existing",
                "general_conditions": {"age_min": 1, "age_max": 100, "pre_existing_covered": True},
                "benefits": [
                    {"benefit_name": "Medical Coverage", "coverage_limit": 50000}
                ]
            }
        ],
        "recommendation": "Based on your needs, TravelEasy Pre-Existing is recommended if you have pre-existing conditions."
    }
    
    print(format_comparison_plain_text(sample_comparison))

