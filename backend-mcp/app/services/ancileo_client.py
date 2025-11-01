"""
TravelMate AI - Ancileo/MSIG API Client
Integrates with real MSIG travel insurance pricing and purchase APIs
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AncileoAPIClient:
    """
    Client for Ancileo/MSIG Travel Insurance API
    Handles pricing and purchase operations
    """
    
    def __init__(self):
        self.pricing_url = settings.ancileo_pricing_url
        self.purchase_url = settings.ancileo_purchase_url
        self.api_key = settings.ancileo_api_key
        
        # Match exact headers from documentation
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key  # Lowercase as per docs
        }
    
    async def get_pricing(
        self,
        departure_date: str,  # YYYY-MM-DD
        return_date: str,  # YYYY-MM-DD
        departure_country: str = "SG",
        arrival_country: str = "CN",
        adults_count: int = 1,
        children_count: int = 0,
        trip_type: str = "RT"  # RT = Round Trip, ST = Single Trip
    ) -> Dict[str, Any]:
        """
        Get real-time pricing from Ancileo/MSIG API
        
        Args:
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD) 
            departure_country: ISO country code (default: SG)
            arrival_country: ISO country code for destination
            adults_count: Number of adults
            children_count: Number of children
            trip_type: "RT" (Round Trip) or "ST" (Single Trip)
            
        Returns:
            Pricing response from API with offer details
        """
        logger.info(
            "ancileo_pricing_request",
            departure_date=departure_date,
            arrival_country=arrival_country,
            adults=adults_count
        )
        
        payload = {
            "market": "SG",
            "languageCode": "en",
            "channel": "white-label",
            "deviceType": "DESKTOP",
            "context": {
                "tripType": trip_type,
                "departureDate": departure_date,
                "returnDate": return_date,
                "departureCountry": departure_country,
                "arrivalCountry": arrival_country,
                "adultsCount": adults_count,
                "childrenCount": children_count
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(
                    "ancileo_api_request",
                    url=self.pricing_url,
                    payload=payload,
                    headers={k: v[:20] + "..." if k == "x-api-key" and len(v) > 20 else v for k, v in self.headers.items()}
                )
                
                response = await client.post(
                    self.pricing_url,
                    json=payload,
                    headers=self.headers
                )
                
                logger.info(
                    "ancileo_api_response",
                    status=response.status_code,
                    headers=dict(response.headers),
                    body_preview=str(response.text)[:200]
                )
                
                response.raise_for_status()
                result = response.json()
                
                # offerCategories is a LIST, not a dict!
                offer_categories = result.get("offerCategories", [])
                offers_count = 0
                if offer_categories and isinstance(offer_categories, list) and len(offer_categories) > 0:
                    offers_count = len(offer_categories[0].get("offers", []))
                
                logger.info(
                    "ancileo_pricing_success",
                    quote_id=result.get("id"),
                    offers_count=offers_count
                )
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "ancileo_pricing_http_error",
                status_code=e.response.status_code,
                response_body=e.response.text,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("ancileo_pricing_error", error=str(e))
            raise
    
    def get_pricing_sync(
        self,
        departure_date: str,
        return_date: str,
        departure_country: str = "SG",
        arrival_country: str = "CN",
        adults_count: int = 1,
        children_count: int = 0,
        trip_type: str = "RT"
    ) -> Dict[str, Any]:
        """
        Synchronous version of get_pricing for non-async contexts
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.get_pricing(
                departure_date,
                return_date,
                departure_country,
                arrival_country,
                adults_count,
                children_count,
                trip_type
            )
        )
    
    def parse_pricing_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Ancileo pricing response into our format
        
        Returns:
            {
                "quote_id": "abc",
                "offers": [
                    {
                        "offer_id": "def",
                        "product_code": "TESTPRODUCT",
                        "product_name": "Premium Coverage",
                        "unit_price": 60,
                        "currency": "SGD",
                        "benefits": "...",
                        "passengers": [1, 2, 3]
                    }
                ]
            }
        """
        # offerCategories is a LIST of categories
        offer_categories_list = response.get("offerCategories", [])
        quote_id = response.get("id", "")
        
        offers = []
        
        # Iterate through each category (usually just one for travel insurance)
        for category in offer_categories_list:
            if not isinstance(category, dict):
                continue
                
            for offer in category.get("offers", []):
                product_info = offer.get("productInformation", {})
                
                parsed_offer = {
                    "offer_id": offer.get("id"),
                    "product_code": offer.get("productCode"),
                    "unit_price": offer.get("unitPrice"),
                    "currency": offer.get("currency", "SGD"),
                    "product_info": product_info,
                    "passengers": offer.get("passengers", [])
                }
                offers.append(parsed_offer)
        
        return {
            "quote_id": quote_id,
            "offers": offers,
            "default_selected": offer_categories_list[0].get("defaultSelectedOffer") if offer_categories_list else None,
            "opt_out_label": offer_categories_list[0].get("optOutLabel") if offer_categories_list else None
        }
    
    async def complete_purchase(
        self,
        quote_id: str,
        offer_id: str,
        product_code: str,
        unit_price: float,
        insureds: list,
        main_contact: dict
    ) -> Dict[str, Any]:
        """
        Complete insurance purchase via Ancileo API
        
        Args:
            quote_id: Quote ID from pricing call
            offer_id: Offer ID from pricing call
            product_code: Product code from offer
            unit_price: Price per unit
            insureds: List of insured persons
            main_contact: Main contact information
            
        Returns:
            Purchase confirmation response
        """
        logger.info("ancileo_purchase_request", quote_id=quote_id, offer_id=offer_id)
        
        payload = {
            "market": "SG",
            "languageCode": "en",
            "channel": "white-label",
            "quoteId": quote_id,
            "purchaseOffers": [
                {
                    "productType": "travel-insurance",
                    "offerId": offer_id,
                    "productCode": product_code,
                    "unitPrice": unit_price,
                    "currency": "SGD",
                    "quantity": 1,
                    "totalPrice": unit_price,
                    "isSendEmail": True
                }
            ],
            "insureds": insureds,
            "mainContact": main_contact
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.purchase_url,
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("ancileo_purchase_success", quote_id=quote_id)
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "ancileo_purchase_http_error",
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("ancileo_purchase_error", error=str(e))
            raise

