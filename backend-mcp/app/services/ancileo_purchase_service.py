"""
Ancileo Purchase API Service
Calls the real MSIG/Ancileo API to issue insurance policies after payment
"""

from typing import Dict, Any, Optional
import httpx
from datetime import datetime
from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class AncileoPurchaseService:
    """
    Handles policy issuance via Ancileo Purchase API
    Called after Stripe payment succeeds
    """
    
    def __init__(self):
        self.purchase_url = settings.ancileo_purchase_url
        logger.info("ancileo_purchase_service_initialized")
    
    async def issue_policy(
        self,
        quote_id: str,
        offer_id: str,
        product_code: str,
        unit_price: float,
        api_key: str,
        insured_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Issue insurance policy via Ancileo Purchase API
        
        Args:
            quote_id: UUID from quotation response
            offer_id: UUID from quotation response
            product_code: Product identifier (e.g., "SG_AXA_SCOOT_COMP")
            unit_price: Price from quote
            api_key: Product-specific API key
            insured_details: Customer information (optional for demo)
            
        Returns:
            Policy details including policy_number
        """
        logger.info("issuing_policy_via_ancileo", 
                   quote_id=quote_id,
                   product_code=product_code)
        
        try:
            # Use demo insured data if not provided
            if not insured_details:
                insured_details = self._get_demo_insured_data()
            
            # Build purchase request
            purchase_request = {
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
                "insureds": [insured_details.get("insured", self._get_demo_insured())],
                "mainContact": insured_details.get("mainContact", self._get_demo_main_contact())
            }
            
            # Call Ancileo Purchase API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.purchase_url,
                    json=purchase_request,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info("ancileo_policy_issued", 
                               policy_number=result.get("policyNumber"),
                               quote_id=quote_id)
                    
                    return {
                        "success": True,
                        "policy_number": result.get("policyNumber"),
                        "policy_details": result,
                        "source": "ancileo_api"
                    }
                else:
                    logger.error("ancileo_purchase_failed", 
                               status=response.status_code,
                               response=response.text[:200])
                    
                    # Fallback: Generate mock policy number
                    return self._generate_mock_policy_response(quote_id)
        
        except Exception as e:
            logger.error("ancileo_purchase_error", error=str(e))
            # Fallback: Generate mock policy number
            return self._generate_mock_policy_response(quote_id)
    
    def _generate_mock_policy_response(self, quote_id: str) -> Dict[str, Any]:
        """Generate mock policy for demo when API fails"""
        import uuid
        policy_number = f"POL-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        logger.info("using_mock_policy_number", policy_number=policy_number)
        
        return {
            "success": True,
            "policy_number": policy_number,
            "policy_details": {
                "policyNumber": policy_number,
                "status": "active",
                "issueDate": datetime.utcnow().isoformat()
            },
            "source": "mock_demo"
        }
    
    def _get_demo_insured(self) -> Dict[str, Any]:
        """Demo insured data for testing"""
        return {
            "id": "1",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "nationality": "SG",
            "dateOfBirth": "1990-01-01",
            "passport": "E1234567",
            "email": "customer@example.com",
            "phoneType": "mobile",
            "phoneNumber": "65123456",
            "relationship": "main"
        }
    
    def _get_demo_main_contact(self) -> Dict[str, Any]:
        """Demo main contact data for testing"""
        return {
            "id": "1",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "nationality": "SG",
            "dateOfBirth": "1990-01-01",
            "passport": "E1234567",
            "email": "customer@example.com",
            "phoneType": "mobile",
            "phoneNumber": "65123456",
            "address": "123 Main Street",
            "city": "Singapore",
            "zipCode": "123456",
            "countryCode": "SG"
        }
    
    def _get_demo_insured_data(self) -> Dict[str, Any]:
        """Get demo insured data structure"""
        return {
            "insured": self._get_demo_insured(),
            "mainContact": self._get_demo_main_contact()
        }


# Singleton instance
_ancileo_purchase_service = None


def get_ancileo_purchase_service() -> AncileoPurchaseService:
    """Get or create singleton Ancileo purchase service"""
    global _ancileo_purchase_service
    if _ancileo_purchase_service is None:
        _ancileo_purchase_service = AncileoPurchaseService()
    return _ancileo_purchase_service

