"""
Test Script - Extract and Map Single Policy
Tests the extraction pipeline on one policy before running on all
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_pdf_text import PDFTextExtractor
from app.utils.taxonomy_mapper import TaxonomyMapper


def test_pdf_extraction(pdf_path: str) -> str:
    """Test PDF text extraction"""
    print(f"\n{'='*70}")
    print("TEST 1: PDF Text Extraction")
    print(f"{'='*70}\n")
    
    try:
        extractor = PDFTextExtractor(pdf_path)
        text = extractor.extract_text(max_pages=10)  # Just first 10 pages for test
        
        print(f"✓ Successfully extracted text")
        print(f"  Total characters: {len(text):,}")
        print(f"  First 500 chars preview:")
        print(f"  {'-'*70}")
        print(f"  {text[:500]}...")
        print(f"  {'-'*70}\n")
        
        return text
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        raise


def test_layer_1_mapping(policy_text: str, product_key: str) -> dict:
    """Test Layer 1 mapping"""
    print(f"\n{'='*70}")
    print("TEST 2: Layer 1 - General Conditions Mapping")
    print(f"{'='*70}\n")
    
    try:
        mapper = TaxonomyMapper()
        layer_1 = mapper._map_layer_1_general_conditions(policy_text, product_key)
        
        print(f"✓ Successfully mapped Layer 1")
        print(f"  Total conditions extracted: {len(layer_1)}")
        print(f"\n  Sample results:")
        
        # Show first 3 conditions
        for i, condition in enumerate(layer_1[:3], 1):
            status = "EXISTS" if condition.get("condition_exist") else "NOT FOUND"
            print(f"\n  {i}. {condition.get('condition')} [{status}]")
            if condition.get("condition_exist"):
                params = condition.get("parameters", {})
                if params:
                    print(f"     Parameters: {json.dumps(params, indent=6)}")
                text = condition.get("original_text", "")
                if text:
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"     Text: {preview}")
        
        print(f"\n  (Showing 3 of {len(layer_1)} conditions)")
        return layer_1
        
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        raise


def test_layer_2_mapping(policy_text: str, product_key: str) -> dict:
    """Test Layer 2 mapping"""
    print(f"\n{'='*70}")
    print("TEST 3: Layer 2 - Benefits Mapping")
    print(f"{'='*70}\n")
    
    try:
        mapper = TaxonomyMapper()
        layer_2 = mapper._map_layer_2_benefits(policy_text, product_key)
        
        print(f"✓ Successfully mapped Layer 2")
        print(f"  Total benefits extracted: {len(layer_2)}")
        
        # Count how many benefits exist
        existing_benefits = [b for b in layer_2 if b.get("condition_exist")]
        print(f"  Benefits that exist: {len(existing_benefits)}")
        
        print(f"\n  Sample existing benefits:")
        for i, benefit in enumerate(existing_benefits[:5], 1):
            print(f"\n  {i}. {benefit.get('benefit_name')}")
            params = benefit.get("parameters", {})
            if params:
                print(f"     {json.dumps(params, indent=6)}")
        
        print(f"\n  (Showing 5 of {len(existing_benefits)} existing benefits)")
        return layer_2
        
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        raise


def test_layer_3_mapping(policy_text: str, product_key: str) -> dict:
    """Test Layer 3 mapping"""
    print(f"\n{'='*70}")
    print("TEST 4: Layer 3 - Benefit-Specific Conditions Mapping")
    print(f"{'='*70}\n")
    
    try:
        mapper = TaxonomyMapper()
        layer_3 = mapper._map_layer_3_benefit_conditions(policy_text, product_key)
        
        print(f"✓ Successfully mapped Layer 3")
        print(f"  Total benefit conditions extracted: {len(layer_3)}")
        
        # Count existing conditions
        existing_conditions = [c for c in layer_3 if c.get("condition_exist")]
        print(f"  Conditions that exist: {len(existing_conditions)}")
        
        # Group by benefit
        by_benefit = {}
        for cond in existing_conditions:
            benefit = cond.get("benefit_name")
            if benefit not in by_benefit:
                by_benefit[benefit] = []
            by_benefit[benefit].append(cond.get("condition"))
        
        print(f"\n  Sample conditions by benefit:")
        for i, (benefit, conditions) in enumerate(list(by_benefit.items())[:3], 1):
            print(f"\n  {i}. {benefit}:")
            for cond in conditions[:3]:
                print(f"     - {cond}")
        
        print(f"\n  (Showing 3 of {len(by_benefit)} benefits with conditions)")
        return layer_3
        
    except Exception as e:
        print(f"✗ FAILED: {e}\n")
        raise


def save_test_results(results: dict, output_path: str):
    """Save test results to JSON"""
    print(f"\n{'='*70}")
    print("Saving Test Results")
    print(f"{'='*70}\n")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Test results saved to: {output_path}")


def main():
    """Run tests"""
    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Select a test policy (you can change this)
    test_pdf = project_root / "assets" / "Policy_Wordings" / "Scootsurance.pdf"
    test_product = "Product A"
    
    print("\n" + "#"*70)
    print("# SINGLE POLICY EXTRACTION TEST")
    print("#"*70)
    print(f"\nTest Policy: {test_pdf.name}")
    print(f"Product Key: {test_product}")
    print(f"PDF Path: {test_pdf}")
    print(f"Exists: {test_pdf.exists()}")
    
    if not test_pdf.exists():
        print(f"\n✗ Error: Test PDF not found!")
        sys.exit(1)
    
    print("\nStarting tests...")
    
    try:
        # Test 1: Extract PDF text
        policy_text = test_pdf_extraction(str(test_pdf))
        
        # Test 2: Map Layer 1
        layer_1 = test_layer_1_mapping(policy_text, test_product)
        
        # Test 3: Map Layer 2
        layer_2 = test_layer_2_mapping(policy_text, test_product)
        
        # Test 4: Map Layer 3
        layer_3 = test_layer_3_mapping(policy_text, test_product)
        
        # Compile results
        results = {
            "product_key": test_product,
            "pdf_file": test_pdf.name,
            "text_length": len(policy_text),
            "layer_1_general_conditions": layer_1,
            "layer_2_benefits": layer_2,
            "layer_3_benefit_specific_conditions": layer_3
        }
        
        # Save results
        output_path = project_root / "backend-mcp" / "test_results" / f"test_{test_product.replace(' ', '_')}.json"
        save_test_results(results, str(output_path))
        
        print(f"\n{'#'*70}")
        print("# ALL TESTS PASSED ✓")
        print(f"{'#'*70}\n")
        print("The extraction pipeline is working correctly!")
        print("You can now run the full populate_taxonomy.py script.\n")
        
    except Exception as e:
        print(f"\n{'#'*70}")
        print("# TEST FAILED ✗")
        print(f"{'#'*70}\n")
        print(f"Error: {e}")
        print("\nPlease fix the error before running the full extraction.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

