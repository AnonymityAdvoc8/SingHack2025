"""
Debug why taxonomy returns 0 eligible products
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.taxonomy_service import get_taxonomy_service


def main():
    print("\n" + "="*70)
    print("DEBUGGING TAXONOMY ELIGIBILITY")
    print("="*70 + "\n")
    
    service = get_taxonomy_service()
    
    # Test trip details (same as in chatbot test)
    trip_details = {
        "departure_location": "Singapore",
        "destination_country": "Japan",
        "travelers": [
            {"age": 35, "has_pre_existing_conditions": False}
        ],
        "activities": ["skiing"]
    }
    
    print("Trip Details:")
    for key, value in trip_details.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("CHECKING EACH PRODUCT:")
    print("="*70 + "\n")
    
    for product_key in service.get_all_products():
        print(f"\n{product_key}:")
        print("-" * 70)
        
        # Get product data
        product_data = service.get_product_data(product_key)
        layer_1 = product_data.get("layer_1_conditions", [])
        
        print(f"  Layer 1 Conditions Found: {len(layer_1)}")
        
        if layer_1:
            print(f"\n  Conditions:")
            for cond in layer_1[:5]:  # Show first 5
                print(f"    - {cond['condition']}")
                print(f"      Parameters: {cond.get('parameters', {})}")
        
        # Check eligibility
        print(f"\n  ELIGIBILITY CHECK:")
        eligibility = service.check_eligibility(product_key, trip_details)
        
        print(f"    Eligible: {eligibility['is_eligible']}")
        print(f"    Reasons:")
        for reason in eligibility['reasons']:
            print(f"      - {reason}")
    
    print("\n" + "="*70)
    print("COMPARISON:")
    print("="*70 + "\n")
    
    comparison = service.compare_products(
        product_keys=service.get_all_products(),
        trip_details=trip_details
    )
    
    print(f"Eligible products: {[k for k, v in comparison['eligibility'].items() if v['is_eligible']]}")
    print(f"Recommended: {comparison.get('recommendation', 'None')}")
    
    print("\n" + "="*70)
    print("DIAGNOSIS:")
    print("="*70 + "\n")
    
    eligible_count = sum(1 for v in comparison['eligibility'].values() if v['is_eligible'])
    
    if eligible_count > 0:
        print(f"✅ SUCCESS: {eligible_count} products are eligible!")
        print("   The taxonomy is working correctly.")
    else:
        print("⚠️ ISSUE: 0 products are eligible")
        print("\nPossible causes:")
        print("  1. Layer 1 conditions not matching trip details")
        print("  2. Eligibility logic too strict")
        print("  3. Parameter format mismatch")
        print("\nRecommendation: Check the conditions and parameters above")


if __name__ == "__main__":
    main()

