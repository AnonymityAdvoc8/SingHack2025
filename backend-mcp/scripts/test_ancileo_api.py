"""
Test script for Ancileo/MSIG API integration
Validates real-time pricing API calls
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ancileo_client import AncileoAPIClient
from app.config import get_settings
import structlog

logger = structlog.get_logger()

def test_ancileo_api():
    print("================================================================================")
    print("🏥 Ancileo/MSIG API Integration - Test Suite")
    print("================================================================================")
    
    settings = get_settings()
    
    # Check if API key is configured
    print("\n============================================================")
    print("Test 1: API Configuration")
    print("============================================================")
    
    if not settings.ancileo_api_key:
        print("❌ MSIG_API_KEY not found in .env")
        print("\nPlease add to backend-mcp/.env:")
        print("ANCILEO_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ API Key configured: {settings.ancileo_api_key[:10]}...")
    print(f"✅ Pricing URL: {settings.ancileo_pricing_url}")
    
    # Initialize client
    client = AncileoAPIClient()
    
    # Test 2: Get pricing for Japan trip
    print("\n============================================================")
    print("Test 2: Get Pricing - Japan Round Trip")
    print("============================================================")
    
    try:
        response = client.get_pricing_sync(
            departure_date="2025-03-01",
            return_date="2025-03-10",
            departure_country="SG",
            arrival_country="JP",  # Japan
            adults_count=1,
            children_count=0,
            trip_type="RT"
        )
        
        print("✅ API call successful!")
        print("\n📋 Raw Response:")
        print("------------------------------------------------------------")
        import json
        print(json.dumps(response, indent=2))
        
        # Parse response
        parsed = client.parse_pricing_response(response)
        
        print("\n📊 Parsed Response:")
        print("------------------------------------------------------------")
        print(f"Quote ID: {parsed.get('quote_id')}")
        print(f"Offers Count: {len(parsed.get('offers', []))}")
        
        for i, offer in enumerate(parsed.get('offers', []), 1):
            print(f"\n🎫 Offer {i}:")
            print(f"  Offer ID: {offer.get('offer_id')}")
            print(f"  Product Code: {offer.get('product_code')}")
            print(f"  Unit Price: SGD ${offer.get('unit_price')}")
            
            product_info = offer.get('product_info', {})
            print(f"  Product Name: {product_info.get('title', 'N/A')}")
            
            benefits = product_info.get('benefits', '')
            if benefits:
                print(f"  Benefits:")
                for line in benefits.strip().split('\n'):
                    if line.strip():
                        print(f"    {line.strip()}")
        
        print("\n✅ Test 2: PASSED")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Get pricing for Thailand trip
    print("\n============================================================")
    print("Test 3: Get Pricing - Thailand Round Trip")
    print("============================================================")
    
    try:
        response = client.get_pricing_sync(
            departure_date="2025-04-15",
            return_date="2025-04-25",
            departure_country="SG",
            arrival_country="TH",  # Thailand
            adults_count=2,
            children_count=1,
            trip_type="RT"
        )
        
        parsed = client.parse_pricing_response(response)
        
        print("✅ API call successful!")
        print(f"\nQuote ID: {parsed.get('quote_id')}")
        print(f"Offers: {len(parsed.get('offers', []))}")
        
        for offer in parsed.get('offers', []):
            print(f"\n  Product: {offer.get('product_info', {}).get('title', 'N/A')}")
            print(f"  Price: SGD ${offer.get('unit_price')} × {len(offer.get('passengers', []))} passengers")
        
        print("\n✅ Test 3: PASSED")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False
    
    # Test 4: Single trip (no return date)
    print("\n============================================================")
    print("Test 4: Get Pricing - Single Trip (USA)")
    print("============================================================")
    
    try:
        response = client.get_pricing_sync(
            departure_date="2025-06-01",
            return_date="2025-06-01",  # Same date for single trip
            departure_country="SG",
            arrival_country="US",  # USA
            adults_count=1,
            children_count=0,
            trip_type="ST"  # Single trip
        )
        
        parsed = client.parse_pricing_response(response)
        
        print("✅ API call successful!")
        print(f"\nQuote ID: {parsed.get('quote_id')}")
        print(f"Trip Type: Single Trip")
        print(f"Price: SGD ${parsed.get('offers', [{}])[0].get('unit_price', 0)}")
        
        print("\n✅ Test 4: PASSED")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False
    
    # Summary
    print("\n============================================================")
    print("📊 Test Summary")
    print("============================================================")
    print("  ✅ PASS: API Configuration")
    print("  ✅ PASS: Japan Round Trip Pricing")
    print("  ✅ PASS: Thailand Round Trip Pricing")
    print("  ✅ PASS: USA Single Trip Pricing")
    print("\n============================================================")
    print("Overall: 4/4 tests passed")
    print("============================================================")
    print("\n✅ Ancileo API integration is working correctly!")
    print("\n⚠️  NOTE: API returns ONLY ONE offer per request (MSIG limitation)")
    print("    Our system will use this for real pricing, but still show")
    print("    our 3 local policies for comparison.")
    
    return True


if __name__ == "__main__":
    success = test_ancileo_api()
    sys.exit(0 if success else 1)

