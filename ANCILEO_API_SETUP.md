# Ancileo API Integration Setup

## Quick Setup

Add this line to your `backend-mcp/.env` file:

```bash
ANCILEO_API_KEY=MSIG_API_KEY
```

Replace `MSIG_API_KEY` with the actual API key provided by MSIG/Ancileo.

## What Changed

### 1. New Ancileo API Client (`app/services/ancileo_client.py`)
- Real-time pricing calls to `https://dev.api.ancileo.com/v1/travel/front/pricing`
- Purchase endpoint integration (Phase 4)
- Automatic response parsing

### 2. Updated Quote Service (`app/services/quote_service.py`)
- **Smart fallback**: Uses Ancileo API if key exists, falls back to local pricing
- `_generate_quote_from_api()`: Calls real MSIG pricing
- `_generate_quote_local()`: Local pricing logic (fallback)
- Automatic country code mapping (Japan → JP, Thailand → TH, etc.)

### 3. Updated Schema (`app/schemas/trip.py`)
- Added `api_metadata` field to `QuoteItemSchema`
- Stores `quote_id`, `offer_id`, `product_code` for purchase flow

### 4. Configuration (`app/config.py`)
- `ancileo_pricing_url`: Pricing endpoint
- `ancileo_purchase_url`: Purchase endpoint
- `ancileo_api_key`: API key

## API Limitation

⚠️ **Important**: The Ancileo API returns **ONLY ONE offer** per request (MSIG limitation mentioned by user).

Our strategy:
1. Call Ancileo API for real MSIG pricing
2. Still show our 3 local policies for comparison
3. Highlight the MSIG offer with real pricing
4. Use local pricing for other policies

## Testing

Run the test script:

```bash
cd backend-mcp
python scripts/test_ancileo_api.py
```

This will test:
- Japan round trip pricing
- Thailand round trip pricing  
- USA single trip pricing
- Response parsing

## Example API Call

```python
from app.services.ancileo_client import AncileoAPIClient

client = AncileoAPIClient()

response = client.get_pricing_sync(
    departure_date="2025-03-01",
    return_date="2025-03-10",
    departure_country="SG",
    arrival_country="JP",  # Japan
    adults_count=1,
    children_count=0,
    trip_type="RT"  # Round Trip
)

# Returns:
# {
#   "id": "quote_abc123",
#   "offerCategories": {
#     "offers": [
#       {
#         "id": "offer_def456",
#         "productCode": "SG_MSIG_PREMIUM",
#         "unitPrice": 78.50,
#         "productInformation": {
#           "title": "Premium Coverage",
#           "benefits": "..."
#         }
#       }
#     ]
#   }
# }
```

## Next Steps

1. Add `ANCILEO_API_KEY` to `.env`
2. Run test script
3. Test via `/ask` endpoint: "I'm 31 travelling to Japan, which policy?"
4. Verify real MSIG pricing appears in quote

## Phase 4 Integration

The `api_metadata` stored in quotes will be used in Phase 4 for:
- `quote_id`: Required for purchase API
- `offer_id`: Required for purchase API
- `product_code`: Required for purchase API

This enables seamless transition from quote → payment → purchase.

