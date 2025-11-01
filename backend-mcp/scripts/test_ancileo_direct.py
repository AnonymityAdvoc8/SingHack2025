"""
Direct test of Ancileo API with raw httpx
Helps debug 405 Method Not Allowed error
"""

import httpx
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings

settings = get_settings()

def test_direct_api_call():
    print("=" * 80)
    print("Ancileo API Direct Test")
    print("=" * 80)
    
    url = "https://dev.api.ancileo.com/v1/travel/front/pricing"
    api_key = settings.ancileo_api_key
    
    if not api_key:
        print("❌ ANCILEO_API_KEY not found in .env")
        return False
    
    print(f"\n✅ API Key found: {api_key[:10]}...")
    print(f"✅ URL: {url}")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    # Use future dates (API requires dates after today)
    from datetime import datetime, timedelta
    today = datetime.now()
    departure = today + timedelta(days=30)  # 30 days from now
    return_date = departure + timedelta(days=9)  # 9-day trip
    
    payload = {
        "market": "SG",
        "languageCode": "en",
        "channel": "white-label",
        "deviceType": "DESKTOP",
        "context": {
            "tripType": "RT",
            "departureDate": departure.strftime("%Y-%m-%d"),
            "returnDate": return_date.strftime("%Y-%m-%d"),
            "departureCountry": "SG",
            "arrivalCountry": "JP",
            "adultsCount": 1,
            "childrenCount": 0
        }
    }
    
    print("\n" + "=" * 80)
    print("REQUEST DETAILS:")
    print("=" * 80)
    print(f"Method: POST")
    print(f"Headers: {json.dumps({k: v[:20] + '...' if k == 'x-api-key' else v for k, v in headers.items()}, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    print("\n" + "=" * 80)
    print("SENDING REQUEST...")
    print("=" * 80)
    
    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=30.0
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        response.raise_for_status()
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS: API call worked!")
        print("=" * 80)
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"\nResponse Headers:")
        for key, value in e.response.headers.items():
            print(f"  {key}: {value}")
        print(f"\nResponse Body:")
        print(e.response.text)
        
        # Try to give helpful advice
        if e.response.status_code == 405:
            print("\n💡 405 Method Not Allowed - Possible causes:")
            print("  1. API expects GET instead of POST")
            print("  2. Wrong endpoint URL")
            print("  3. Missing required headers")
            print("  4. API key invalid or expired")
            print("\n   Let me try with different headers...")
            
            # Try with different header capitalization
            alt_headers = {
                "Content-Type": "application/json",
                "X-API-Key": api_key  # Try uppercase
            }
            
            try:
                alt_response = httpx.post(url, json=payload, headers=alt_headers, timeout=30.0)
                print(f"\n   Alternative headers result: {alt_response.status_code}")
                if alt_response.status_code == 200:
                    print("   ✅ WORKED with uppercase X-API-Key!")
                    return True
            except:
                pass
        
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_direct_api_call()
    sys.exit(0 if success else 1)

