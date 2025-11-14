"""
Stripe Payment Service - Simple Demo Mode
Handles payment processing using Stripe Checkout
Uses JSON file for payment tracking (no Docker/DynamoDB needed)
"""

from typing import Dict, Any, Optional
import stripe
import json
from datetime import datetime
import uuid
from pathlib import Path
from app.config import get_settings
from app.utils.logger import get_logger
from app.services.ancileo_purchase_service import get_ancileo_purchase_service

settings = get_settings()
logger = get_logger(__name__)


class StripePaymentService:
    """
    Manages Stripe payment processing for insurance purchases
    Simple demo mode: Uses JSON file for payment tracking
    """
    
    def __init__(self):
        """Initialize Stripe client and payment storage"""
        # Initialize Stripe
        stripe.api_key = settings.stripe_api_key
        
        # Use simple JSON file for payment tracking (no Docker needed!)
        self.payments_file = Path(".payments_db.json")
        
        # Create file if it doesn't exist
        if not self.payments_file.exists():
            self._save_payments({})
        
        logger.info("stripe_payment_service_initialized", mode="simple_json")
    
    def _load_payments(self) -> Dict[str, Any]:
        """Load payments from JSON file"""
        try:
            with open(self.payments_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_payments(self, payments: Dict[str, Any]):
        """Save payments to JSON file"""
        with open(self.payments_file, 'w') as f:
            json.dump(payments, f, indent=2)
    
    def create_payment_checkout(
        self,
        quote_id: str,
        policy_name: str,
        premium: float,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment checkout session for insurance purchase
        
        Args:
            quote_id: Quote identifier from Ancileo API
            policy_name: Name of the policy being purchased
            premium: Premium amount in SGD
            user_id: User identifier
            metadata: Additional metadata (trip details, etc.)
            
        Returns:
            Payment checkout details with URL
        """
        logger.info("creating_payment_checkout", 
                   quote_id=quote_id, 
                   premium=premium,
                   policy=policy_name)
        
        try:
            # Generate unique payment intent ID
            payment_intent_id = f"payment_{uuid.uuid4().hex[:12]}"
            
            # Convert premium to cents (Stripe uses smallest currency unit)
            amount_cents = int(premium * 100)
            
            # Step 1: Create payment record in JSON file with 'pending' status
            payment_record = {
                'payment_intent_id': payment_intent_id,
                'user_id': user_id,
                'quote_id': quote_id,
                'payment_status': 'pending',
                'amount': amount_cents,
                'currency': 'SGD',
                'product_name': policy_name,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            payments = self._load_payments()
            payments[payment_intent_id] = payment_record
            self._save_payments(payments)
            
            logger.info("payment_record_created", payment_id=payment_intent_id)
            
            # Step 2: Create Stripe Checkout Session  
            # Success URL shows simple page that auto-closes
            success_page_url = f'http://localhost:8080/payment/success-callback?payment_id={payment_intent_id}'
            cancel_page_url = f'http://localhost:8080/payment/cancel-callback'
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'sgd',
                        'unit_amount': amount_cents,
                        'product_data': {
                            'name': policy_name,
                            'description': f'Travel Insurance Policy - Quote {quote_id}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_page_url,
                cancel_url=cancel_page_url,
                client_reference_id=payment_intent_id,  # Links to our payment record
                metadata={
                    'quote_id': quote_id,
                    'user_id': user_id,
                    'policy_name': policy_name,
                    'payment_intent_id': payment_intent_id
                }
            )
            
            # Step 3: Update payment record with Stripe session ID
            payment_record['stripe_session_id'] = checkout_session.id
            payment_record['updated_at'] = datetime.utcnow().isoformat()
            payments[payment_intent_id] = payment_record
            self._save_payments(payments)
            
            logger.info("stripe_checkout_created", 
                       session_id=checkout_session.id,
                       payment_id=payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "checkout_url": checkout_session.url,
                "stripe_session_id": checkout_session.id,
                "amount": premium,
                "currency": "SGD",
                "status": "pending",
                "expires_at": datetime.fromtimestamp(checkout_session.expires_at).isoformat() if checkout_session.expires_at else None
            }
            
        except Exception as e:
            logger.error("payment_checkout_creation_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create payment checkout"
            }
    
    def check_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Check the current status of a payment
        
        Args:
            payment_intent_id: Payment identifier
            
        Returns:
            Payment status and details
        """
        logger.info("checking_payment_status", payment_id=payment_intent_id)
        
        try:
            # Load payments from JSON file
            payments = self._load_payments()
            
            payment = payments.get(payment_intent_id)
            
            if not payment:
                logger.warning("payment_not_found", payment_id=payment_intent_id)
                return {
                    "success": False,
                    "error": "Payment not found",
                    "payment_intent_id": payment_intent_id
                }
            
            # Check Stripe for actual payment status
            stripe_session_id = payment.get('stripe_session_id')
            if stripe_session_id and payment.get('payment_status') != 'completed':
                try:
                    session = stripe.checkout.Session.retrieve(stripe_session_id)
                    
                    # Update status based on Stripe session
                    if session.payment_status == 'paid':
                        payment['payment_status'] = 'completed'
                        payment['updated_at'] = datetime.utcnow().isoformat()
                        payment['stripe_payment_intent'] = session.payment_intent
                        
                        # Generate policy number if not already set
                        if not payment.get('policy_number'):
                            payment['policy_number'] = self.generate_policy_number(payment.get('quote_id', ''))
                        
                        # Mark that policy needs to be issued
                        payment['needs_policy_issuance'] = True
                        
                        payments[payment_intent_id] = payment
                        self._save_payments(payments)
                        
                        logger.info("payment_completed_needs_policy_issuance", 
                                   payment_id=payment_intent_id,
                                   policy_number=payment['policy_number'])
                except Exception as stripe_err:
                    logger.warning("stripe_session_check_failed", error=str(stripe_err))
            
            # Extract status
            status = payment.get('payment_status', 'unknown')
            
            logger.info("payment_status_retrieved", 
                       payment_id=payment_intent_id,
                       status=status)
            
            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "status": status,
                "quote_id": payment.get('quote_id'),
                "amount": payment.get('amount', 0) / 100,  # Convert from cents
                "currency": payment.get('currency', 'SGD'),
                "product_name": payment.get('product_name'),
                "created_at": payment.get('created_at'),
                "updated_at": payment.get('updated_at'),
                "policy_number": payment.get('policy_number'),
                "stripe_session_id": payment.get('stripe_session_id')
            }
            
        except Exception as e:
            logger.error("payment_status_check_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "payment_intent_id": payment_intent_id
            }
    
    async def complete_policy_issuance(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Complete policy issuance by calling Ancileo Purchase API
        Called after payment is confirmed
        
        Args:
            payment_intent_id: Payment identifier
            
        Returns:
            Policy details
        """
        logger.info("completing_policy_issuance", payment_id=payment_intent_id)
        
        try:
            payments = self._load_payments()
            payment = payments.get(payment_intent_id)
            
            if not payment:
                return {"success": False, "error": "Payment not found"}
            
            if payment.get('payment_status') != 'completed':
                return {"success": False, "error": "Payment not completed"}
            
            # Check if policy already issued
            if payment.get('policy_issued'):
                return {
                    "success": True,
                    "policy_number": payment.get('policy_number'),
                    "already_issued": True
                }
            
            # Get quote details from metadata
            metadata = payment.get('metadata', {})
            quote_id = payment.get('quote_id', '')
            
            # Get product-specific API key
            policy_id = metadata.get('policy_id', 'Product B')
            api_key = settings.get_product_api_key(policy_id)
            
            # For demo: Use mock policy issuance if no API key
            if not api_key:
                logger.info("no_api_key_using_mock_policy")
                policy_number = payment.get('policy_number') or self.generate_policy_number(quote_id)
                
                payment['policy_issued'] = True
                payment['policy_number'] = policy_number
                payment['policy_issue_date'] = datetime.utcnow().isoformat()
                payments[payment_intent_id] = payment
                self._save_payments(payments)
                
                return {
                    "success": True,
                    "policy_number": policy_number,
                    "source": "mock_demo"
                }
            
            # Call Ancileo Purchase API
            # Note: We'd need offer_id and product_code from the original quote
            # For now, generate mock policy
            policy_number = payment.get('policy_number') or self.generate_policy_number(quote_id)
            
            payment['policy_issued'] = True
            payment['policy_number'] = policy_number
            payment['policy_issue_date'] = datetime.utcnow().isoformat()
            payments[payment_intent_id] = payment
            self._save_payments(payments)
            
            logger.info("policy_issued", 
                       payment_id=payment_intent_id,
                       policy_number=policy_number)
            
            return {
                "success": True,
                "policy_number": policy_number,
                "quote_id": quote_id,
                "policy_name": payment.get('product_name'),
                "amount": payment.get('amount', 0) / 100
            }
            
        except Exception as e:
            logger.error("policy_issuance_failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    def generate_policy_number(self, quote_id: str) -> str:
        """
        Generate a unique policy number
        Format: POL-YYYYMMDD-XXXX
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:4].upper()
        return f"POL-{date_str}-{unique_id}"


# Singleton instance
_stripe_service = None


def get_stripe_payment_service() -> StripePaymentService:
    """Get or create singleton Stripe payment service"""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripePaymentService()
    return _stripe_service

