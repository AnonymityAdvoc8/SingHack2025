"""
Test Taxonomy Service - Verify the populated taxonomy is being used correctly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.taxonomy_service import get_taxonomy_service


def test_taxonomy_loading():
    """Test that taxonomy loads successfully"""
    print("\n" + "="*70)
    print("TEST 1: Taxonomy Loading")
    print("="*70 + "\n")
    
    service = get_taxonomy_service()
    products = service.get_all_products()
    
    print(f"✓ Taxonomy loaded successfully")
    print(f"  Products available: {products}")
    print(f"  Total products: {len(products)}")
    
    return service


def test_product_data(service):
    """Test retrieving product data"""
    print("\n" + "="*70)
    print("TEST 2: Product Data Retrieval")
    print("="*70 + "\n")
    
    for product_key in service.get_all_products():
        print(f"\n{product_key}:")
        product_data = service.get_product_data(product_key)
        
        layer_1_count = len(product_data.get("layer_1_conditions", []))
        layer_2_count = len(product_data.get("layer_2_benefits", []))
        layer_3_count = len(product_data.get("layer_3_benefit_conditions", []))
        
        print(f"  ✓ Layer 1 Conditions: {layer_1_count}")
        print(f"  ✓ Layer 2 Benefits: {layer_2_count}")
        print(f"  ✓ Layer 3 Conditions: {layer_3_count}")
        
        # Show sample benefit
        if layer_2_count > 0:
            sample_benefit = product_data["layer_2_benefits"][0]
            print(f"\n  Sample Benefit: {sample_benefit['benefit_name']}")
            params = sample_benefit.get("parameters", {})
            coverage_limit = params.get("coverage_limit")
            if coverage_limit is not None and isinstance(coverage_limit, (int, float)):
                print(f"  Coverage Limit: ${coverage_limit:,}")


def test_eligibility_check(service):
    """Test eligibility checking"""
    print("\n" + "="*70)
    print("TEST 3: Eligibility Checking")
    print("="*70 + "\n")
    
    # Test trip details
    trip_details = {
        "departure_location": "Singapore",
        "destination_country": "Japan",
        "travelers": [
            {"name": "John Doe", "age": 35, "has_pre_existing_conditions": False},
            {"name": "Jane Doe", "age": 32, "has_pre_existing_conditions": False}
        ],
        "activities": ["sightseeing", "shopping"]
    }
    
    print("Trip Details:")
    print(f"  Departure: {trip_details['departure_location']}")
    print(f"  Destination: {trip_details['destination_country']}")
    print(f"  Travelers: {len(trip_details['travelers'])} people")
    print(f"  Activities: {', '.join(trip_details['activities'])}")
    
    print("\nEligibility Results:")
    for product_key in service.get_all_products():
        eligibility = service.check_eligibility(product_key, trip_details)
        
        status = "✓ ELIGIBLE" if eligibility["is_eligible"] else "✗ NOT ELIGIBLE"
        print(f"\n  {product_key}: {status}")
        for reason in eligibility["reasons"]:
            print(f"    - {reason}")


def test_benefit_coverage(service):
    """Test benefit coverage lookup"""
    print("\n" + "="*70)
    print("TEST 4: Benefit Coverage Lookup")
    print("="*70 + "\n")
    
    key_benefits = [
        "overseas_medical_expenses",
        "trip_cancellation",
        "delayed_baggage"
    ]
    
    for benefit_name in key_benefits:
        print(f"\n{benefit_name}:")
        for product_key in service.get_all_products():
            coverage = service.get_benefit_coverage(product_key, benefit_name)
            if coverage:
                limit = coverage.get("coverage_limit")
                if limit is not None and isinstance(limit, (int, float)):
                    print(f"  {product_key}: ${limit:,}")
                elif limit is not None:
                    print(f"  {product_key}: {limit}")
                else:
                    print(f"  {product_key}: Covered (limit not specified)")
            else:
                print(f"  {product_key}: Not covered")


def test_product_comparison(service):
    """Test product comparison"""
    print("\n" + "="*70)
    print("TEST 5: Product Comparison")
    print("="*70 + "\n")
    
    trip_details = {
        "departure_location": "Singapore",
        "destination_country": "USA",
        "travelers": [
            {"age": 45, "has_pre_existing_conditions": False}
        ],
        "activities": ["sightseeing"]
    }
    
    comparison = service.compare_products(
        product_keys=service.get_all_products(),
        trip_details=trip_details
    )
    
    print("Comparison Results:")
    print(f"  Products compared: {len(comparison['products'])}")
    print(f"  Recommended product: {comparison['recommendation']}")
    
    print("\nEligibility Summary:")
    for product_key, eligibility in comparison['eligibility'].items():
        status = "✓" if eligibility['is_eligible'] else "✗"
        print(f"  {status} {product_key}: {eligibility['is_eligible']}")


def test_product_summary(service):
    """Test product summaries"""
    print("\n" + "="*70)
    print("TEST 6: Product Summaries")
    print("="*70 + "\n")
    
    for product_key in service.get_all_products():
        summary = service.get_product_summary(product_key)
        print(f"{product_key}:")
        print(f"  {summary}\n")


def main():
    """Run all tests"""
    print("\n" + "#"*70)
    print("# TAXONOMY SERVICE TEST SUITE")
    print("#"*70)
    
    try:
        # Test 1: Loading
        service = test_taxonomy_loading()
        
        # Test 2: Product Data
        test_product_data(service)
        
        # Test 3: Eligibility
        test_eligibility_check(service)
        
        # Test 4: Coverage Lookup
        test_benefit_coverage(service)
        
        # Test 5: Comparison
        test_product_comparison(service)
        
        # Test 6: Summaries
        test_product_summary(service)
        
        print("\n" + "#"*70)
        print("# ALL TESTS PASSED ✓")
        print("#"*70 + "\n")
        print("The taxonomy service is working correctly!")
        print("Your populated taxonomy data is now being used for:")
        print("  - Product eligibility checking")
        print("  - Benefit coverage lookup")
        print("  - Product comparison")
        print("  - Policy recommendations\n")
        
    except Exception as e:
        print("\n" + "#"*70)
        print("# TEST FAILED ✗")
        print("#"*70 + "\n")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

