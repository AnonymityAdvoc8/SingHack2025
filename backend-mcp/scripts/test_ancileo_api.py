"""
Test Ancileo API Integration
Verifies that all three product API keys work correctly
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.multi_product_pricing import get_multi_product_pricing_service
from app.services.ancileo_client import AncileoAPIClient
from app.config import get_settings

settings = get_settings()


async def test_individual_api_keys():
    """Test each API key individually"""
    print("\n" + "="*70)
    print("TEST 1: Individual API Key Testing")
    print("="*70 + "\n")
    
    products = {
        "Product A": settings.scoot,
        "Product B": settings.mag,
        "Product C": settings.trip
    }
    
    # Prepare test dates
    departure = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    for product_key, api_key in products.items():
        print(f"{product_key}:")
        print(f"  API Key: {api_key[:20]}..." if api_key else "  API Key: NOT CONFIGURED")
        
        if not api_key:
            print(f"  Status: ⚠️  API key not configured\n")
            continue
        
        try:
            client = AncileoAPIClient(product_key=product_key)
            
            print(f"  Testing pricing API...")
            response = await client.get_pricing(
                departure_date=departure,
                return_date=return_date,
                departure_country="SG",
                arrival_country="JP",  # Japan
                adults_count=1,
                children_count=0,
                trip_type="RT"
            )
            
            parsed = client.parse_pricing_response(response)
            
            print(f"  ✓ API call successful!")
            print(f"  Quote ID: {parsed.get('quote_id')}")
            print(f"  Offers: {len(parsed.get('offers', []))}")
            
            # Show first offer
            if parsed.get("offers"):
                first_offer = parsed["offers"][0]
                print(f"  First Offer:")
                print(f"    - Product Code: {first_offer.get('product_code')}")
                print(f"    - Price: ${first_offer.get('unit_price', 0):,.2f} {first_offer.get('currency', 'SGD')}")
            
            print()
            
        except Exception as e:
            print(f"  ✗ API call failed: {e}\n")


async def test_multi_product_pricing():
    """Test multi-product pricing service"""
    print("\n" + "="*70)
    print("TEST 2: Multi-Product Pricing Service")
    print("="*70 + "\n")
    
    service = get_multi_product_pricing_service()
    
    # Test trip details
    trip_details = {
        "destination_country": "Japan",
        "departure_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "return_date": (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d"),
        "trip_duration_days": 7,
        "travelers": [
            {"age": 35, "has_pre_existing_conditions": False}
        ],
        "planned_activities": ["skiing"]
    }
    
    print("Getting pricing for all products...")
    print(f"Destination: {trip_details['destination_country']}")
    print(f"Duration: {trip_details['trip_duration_days']} days")
    print(f"Travelers: {len(trip_details['travelers'])}")
    print()
    
    try:
        results = await service.get_all_product_pricing(
            trip_details=trip_details,
            eligible_products=["Product A", "Product B", "Product C"]
        )
        
        print("Results:")
        for product_key, pricing_data in results.items():
            print(f"\n{product_key}:")
            
            if pricing_data.get("error"):
                print(f"  ✗ Error: {pricing_data['error']}")
            else:
                print(f"  ✓ Quote ID: {pricing_data.get('quote_id')}")
                offers = pricing_data.get("offers", [])
                print(f"  ✓ Offers: {len(offers)}")
                
                for i, offer in enumerate(offers, 1):
                    print(f"\n  Offer {i}:")
                    print(f"    Product Code: {offer.get('product_code')}")
                    print(f"    Price: ${offer.get('unit_price', 0):,.2f} {offer.get('currency', 'SGD')}")
        
        print()
        
    except Exception as e:
        print(f"✗ Multi-product pricing failed: {e}\n")


async def main():
    """Run all tests"""
    print("\n" + "#"*70)
    print("# ANCILEO API INTEGRATION TEST")
    print("#"*70)
    
    print(f"\nConfiguration:")
    print(f"  Pricing URL: {settings.ancileo_pricing_url}")
    print(f"  Purchase URL: {settings.ancileo_purchase_url}")
    print(f"\nAPI Keys Configured:")
    print(f"  SCOOT (Product A): {'✓' if settings.scoot else '✗'}")
    print(f"  MAG (Product B): {'✓' if settings.mag else '✗'}")
    print(f"  TRIP (Product C): {'✓' if settings.trip else '✗'}")
    
    configured_count = sum([
        bool(settings.scoot),
        bool(settings.mag),
        bool(settings.trip)
    ])
    
    if configured_count == 0:
        print("\n⚠️  WARNING: No API keys configured!")
        print("   Add API keys to your .env file:")
        print("   SCOOT=your_scoot_api_key")
        print("   MAG=your_mag_api_key")
        print("   TRIP=your_trip_api_key\n")
        return
    
    print(f"\n{configured_count}/3 API keys configured")
    
    # Run tests
    await test_individual_api_keys()
    await test_multi_product_pricing()
    
    print("\n" + "#"*70)
    print("# TEST COMPLETE")
    print("#"*70 + "\n")
    
    if configured_count == 3:
        print("✅ All API keys working!")
        print("   Your chatbot can now get real-time pricing from Ancileo API\n")
    else:
        print(f"⚠️  {3-configured_count} API key(s) not configured")
        print("   Configure remaining keys for full functionality\n")


if __name__ == "__main__":
    asyncio.run(main())
