"""
Multi-Product Pricing Service
Gets real pricing from Ancileo API for all three products using their respective API keys
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.ancileo_client import AncileoAPIClient
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MultiProductPricingService:
    """
    Get pricing for all three taxonomy products using their respective API keys
    Maps Product A/B/C to SCOOT/MAG/TRIP API keys
    """
    
    def __init__(self):
        self.product_mapping = {
            "Product A": "scoot",  # Scootsurance
            "Product B": "mag",    # MH Insure
            "Product C": "trip"    # International Travel
        }
    
    async def get_all_product_pricing(
        self,
        trip_details: Dict[str, Any],
        eligible_products: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get pricing for all eligible products from Ancileo API
        
        Args:
            trip_details: Trip information
            eligible_products: List of eligible products (Product A, B, C)
                             If None, tries all products
        
        Returns:
            {
                "Product A": {pricing_data},
                "Product B": {pricing_data},
                "Product C": {pricing_data}
            }
        """
        if eligible_products is None:
            eligible_products = ["Product A", "Product B", "Product C"]
        
        logger.info("multi_product_pricing_started",
                   products=eligible_products,
                   destination=trip_details.get("destination_country"))
        
        # Prepare API request parameters from trip details
        api_params = self._prepare_api_params(trip_details)
        
        # Get pricing for each product concurrently
        tasks = []
        for product_key in eligible_products:
            task = self._get_product_pricing(product_key, api_params)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build results dict
        pricing_results = {}
        for i, product_key in enumerate(eligible_products):
            result = results[i]
            if isinstance(result, Exception):
                logger.error("product_pricing_failed",
                           product=product_key,
                           error=str(result))
                pricing_results[product_key] = {"error": str(result)}
            else:
                pricing_results[product_key] = result
        
        logger.info("multi_product_pricing_complete",
                   products_with_pricing=len([k for k, v in pricing_results.items() if not v.get("error")]))
        
        return pricing_results
    
    async def _get_product_pricing(
        self,
        product_key: str,
        api_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get pricing for a single product"""
        try:
            # Create client with product-specific API key
            client = AncileoAPIClient(product_key=product_key)
            
            # Check if API key is configured
            if not client.api_key:
                logger.warning("product_api_key_not_configured", product=product_key)
                return {
                    "error": "API key not configured",
                    "product_key": product_key
                }
            
            # Call Ancileo API
            response = await client.get_pricing(**api_params)
            
            # Parse response
            parsed = client.parse_pricing_response(response)
            
            logger.info("product_pricing_success",
                       product=product_key,
                       offers=len(parsed.get("offers", [])))
            
            return {
                "product_key": product_key,
                "quote_id": parsed.get("quote_id"),
                "offers": parsed.get("offers", []),
                "raw_response": response
            }
            
        except Exception as e:
            logger.error("product_pricing_failed",
                        product=product_key,
                        error=str(e))
            return {
                "error": str(e),
                "product_key": product_key
            }
    
    def _prepare_api_params(self, trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert trip details to Ancileo API parameters
        
        Args:
            trip_details: Internal trip details format
            
        Returns:
            Parameters for Ancileo API
        """
        # Extract dates
        departure_date = trip_details.get("departure_date")
        return_date = trip_details.get("return_date")
        
        # If dates not provided, use defaults
        if not departure_date:
            from datetime import datetime, timedelta
            departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        if not return_date:
            from datetime import datetime, timedelta
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
            duration = trip_details.get("trip_duration_days", 7)
            return_date = (dep_date + timedelta(days=duration)).strftime("%Y-%m-%d")
        
        # Extract traveler counts
        travelers = trip_details.get("travelers", [])
        adults_count = len([t for t in travelers if t.get("age", 18) >= 18])
        children_count = len([t for t in travelers if t.get("age", 18) < 18])
        
        # Default to 1 adult if no travelers
        if adults_count == 0 and children_count == 0:
            adults_count = 1
        
        # Determine trip type
        has_return = bool(return_date)
        trip_type = "RT" if has_return else "ST"
        
        # Get destination country code
        destination = trip_details.get("destination_country", "JP")
        # Convert country names to ISO codes if needed
        country_code_map = {
            "Japan": "JP",
            "China": "CN",
            "Thailand": "TH",
            "Malaysia": "MY",
            "Indonesia": "ID",
            "USA": "US",
            "United States": "US",
            "UK": "GB",
            "United Kingdom": "GB",
            "Australia": "AU",
            "New Zealand": "NZ"
        }
        arrival_country = country_code_map.get(destination, destination)
        
        params = {
            "departure_date": departure_date,
            "return_date": return_date,
            "departure_country": "SG",
            "arrival_country": arrival_country,
            "adults_count": adults_count,
            "children_count": children_count,
            "trip_type": trip_type
        }
        
        logger.info("api_params_prepared",
                   trip_type=trip_type,
                   destination=arrival_country,
                   adults=adults_count,
                   children=children_count)
        
        return params


# Singleton instance
_multi_pricing_service = None

def get_multi_product_pricing_service() -> MultiProductPricingService:
    """Get singleton instance"""
    global _multi_pricing_service
    if _multi_pricing_service is None:
        _multi_pricing_service = MultiProductPricingService()
    return _multi_pricing_service

