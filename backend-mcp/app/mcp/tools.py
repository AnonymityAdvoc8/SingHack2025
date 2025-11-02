"""
TravelMate AI - MCP Tools Layer
Wraps services as MCP tools for the protocol
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.comparison_service import PolicyComparisonService
from app.services.eligibility_service import EligibilityService
from app.services.question_service import QuestionAnsweringService
from app.services.quote_service import QuoteService
from app.services.tavily_service import TavilyIntelligenceService
from app.services.conversational_service import ConversationalExtractionService
from app.services.gmail_agent import GmailAgent
from app.services.flight_api_agent import FlightAPIAgent
from app.schemas.trip import TripDetailsSchema, QuoteRequestSchema
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPTools:
    """MCP Tools Layer - Wraps business logic as callable tools"""
    
    def __init__(self, db: Session):
        self.db = db
        self.comparison_service = PolicyComparisonService(db)
        self.eligibility_service = EligibilityService(db)
        self.question_service = QuestionAnsweringService(db)
        self.quote_service = QuoteService(db)
        self.tavily_service = TavilyIntelligenceService()  # NEW: Phase 3
        self.conversational_service = ConversationalExtractionService()  # NEW: Phase 3
        self.gmail_agent = GmailAgent()  # NEW: Agentic AI
        self.flight_api_agent = FlightAPIAgent()  # NEW: Agentic AI
    
    # Tool 1: Compare Policies
    def compare_policies(
        self,
        policy_ids: List[str],
        comparison_criteria: Optional[List[str]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple insurance policies
        
        Args:
            policy_ids: List of policy IDs to compare
            comparison_criteria: Specific aspects to compare
            user_context: User's trip details for personalized comparison
            
        Returns:
            Comprehensive comparison with recommendation
        """
        logger.info("tool_compare_policies", policy_ids=policy_ids)
        
        result = self.comparison_service.compare_policies(
            policy_ids,
            comparison_criteria,
            user_context
        )
        
        return result.dict()
    
    # Tool 2: Answer Policy Question
    def answer_policy_question(
        self,
        question: str,
        policy_id: Optional[str] = None,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Answer questions about insurance policies with citations
        
        Args:
            question: User's question
            policy_id: Specific policy to query (optional)
            include_citations: Whether to include policy citations
            
        Returns:
            Answer with confidence score and citations
        """
        logger.info("tool_answer_question", question_length=len(question))
        
        result = self.question_service.answer_question(
            question,
            policy_id,
            include_citations
        )
        
        return result.dict()
    
    # Tool 3: Check Eligibility
    def check_eligibility(
        self,
        trip_details: Dict[str, Any],
        policy_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Check user eligibility for insurance policies
        
        Args:
            trip_details: User's trip information
            policy_id: Specific policy to check (optional)
            
        Returns:
            List of eligibility results for each policy
        """
        logger.info("tool_check_eligibility", policy_id=policy_id)
        
        # Parse trip details
        trip_schema = TripDetailsSchema(**trip_details)
        
        results = self.eligibility_service.check_eligibility(
            trip_schema,
            policy_id
        )
        
        return [r.dict() for r in results]
    
    # Tool 4: Analyze Scenario
    def analyze_scenario(
        self,
        scenario_description: str,
        trip_details: Optional[Dict[str, Any]] = None,
        policy_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze 'what if' coverage scenarios
        
        Args:
            scenario_description: Description of the scenario
            trip_details: Optional trip context
            policy_ids: Specific policies to analyze
            
        Returns:
            Coverage analysis with gaps and recommendations
        """
        logger.info("tool_analyze_scenario", scenario=scenario_description[:100])
        
        # Use question service to analyze the scenario
        # This is a clever reuse - we treat the scenario as a complex question
        full_question = f"Coverage scenario analysis: {scenario_description}"
        
        if trip_details:
            full_question += f"\n\nTrip context: {trip_details}"
        
        policy_id = policy_ids[0] if policy_ids and len(policy_ids) == 1 else None
        
        result = self.question_service.answer_question(
            full_question,
            policy_id,
            include_citations=True
        )
        
        return {
            "scenario_description": scenario_description,
            "analysis": result.answer,
            "citations": result.citations,
            "confidence": result.confidence,
            "related_policies": result.related_policies
        }
    
    # Tool 5: Get Quote
    def get_quote(
        self,
        trip_details: Dict[str, Any],
        policy_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate insurance quotes
        
        Args:
            trip_details: User's trip information
            policy_ids: Specific policies to quote (optional)
            
        Returns:
            Quote with pricing and recommendations
        """
        logger.info("tool_get_quote", policies=policy_ids)
        
        # Parse request
        trip_schema = TripDetailsSchema(**trip_details)
        quote_request = QuoteRequestSchema(
            trip_details=trip_schema,
            policy_ids=policy_ids
        )
        
        result = self.quote_service.generate_quote(quote_request)
        
        return result.dict()
    
    # Tool 6-8 will be added in Phase 4 (payment) and later
    # For now, let's add placeholders that guide to Phase 4
    
    def purchase_policy(
        self,
        quote_id: str,
        selected_policy_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Initiate policy purchase (Phase 4 - Payment Integration)
        
        Args:
            quote_id: Quote reference
            selected_policy_id: Policy to purchase
            user_id: User identifier
            
        Returns:
            Payment checkout URL and details
        """
        logger.info("tool_purchase_policy", quote_id=quote_id)
        
        # This will be fully implemented in Phase 4
        return {
            "status": "pending_implementation",
            "message": "Purchase flow will be implemented in Phase 4 with Stripe integration",
            "quote_id": quote_id,
            "policy_id": selected_policy_id,
            "next_phase": "Phase 4: Purchase Flow"
        }
    
    def check_payment_status(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Check payment status (Phase 4 - Payment Integration)
        
        Args:
            payment_intent_id: Payment reference
            
        Returns:
            Payment status and policy details
        """
        logger.info("tool_check_payment_status", payment_id=payment_intent_id)
        
        # This will be fully implemented in Phase 4
        return {
            "status": "pending_implementation",
            "message": "Payment status checking will be implemented in Phase 4",
            "payment_intent_id": payment_intent_id,
            "next_phase": "Phase 4: Purchase Flow"
        }
    
    def analyze_trip_risk(
        self,
        trip_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze trip risk using claims data (Phase 5 - Claims Intelligence)
        
        Args:
            trip_details: Trip information
            
        Returns:
            Risk analysis with claims-based recommendations
        """
        logger.info("tool_analyze_trip_risk")
        
        # This will be fully implemented in Phase 5
        return {
            "status": "pending_implementation",
            "message": "Risk analysis will be implemented in Phase 5 with historical claims data",
            "next_phase": "Phase 5: Claims Intelligence"
        }
    
    # Phase 3 Tools: Intelligent Data Collection 🔥 NEW!
    
    def extract_trip_from_conversation(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract trip details from natural conversation (Phase 3)
        
        Args:
            message: User's conversational message
            context: Existing conversation context
            
        Returns:
            Extracted details + follow-up question if needed
        """
        logger.info("tool_conversational_extraction", message_length=len(message))
        
        extraction_result = self.conversational_service.extract_from_message(
            message,
            context
        )
        
        # Generate follow-up question if not complete
        if not extraction_result["is_complete"]:
            extraction_result["follow_up_question"] = self.conversational_service.generate_follow_up_question(
                extraction_result["missing"],
                extraction_result["extracted"]
            )
        else:
            extraction_result["follow_up_question"] = "Great! I have all the details I need. Let me generate your quote."
        
        return extraction_result
    
    def get_destination_intelligence(
        self,
        destination: str,
        travel_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get real-time destination intelligence using Tavily (Phase 3)
        
        Args:
            destination: Travel destination
            travel_date: Optional travel date for temporal context
            
        Returns:
            Real-time intelligence with citations
        """
        logger.info("tool_destination_intelligence", destination=destination)
        
        return self.tavily_service.get_destination_intelligence(
            destination,
            travel_date
        )
    
    def analyze_real_time_risks(
        self,
        destination: str,
        activities: List[str],
        travel_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze real-time travel risks using Tavily (Phase 3)
        
        Args:
            destination: Travel destination
            activities: Planned activities
            travel_date: Optional travel date
            
        Returns:
            Risk analysis with current conditions and citations
        """
        logger.info("tool_realtime_risk_analysis", destination=destination, activities=activities)
        
        return self.tavily_service.analyze_real_time_risks(
            destination,
            activities,
            travel_date
        )
    
    def get_medical_cost_intelligence(
        self,
        destination: str
    ) -> Dict[str, Any]:
        """
        Get real-time medical cost intelligence using Tavily (Phase 3)
        
        Args:
            destination: Travel destination
            
        Returns:
            Medical cost information with recommendations
        """
        logger.info("tool_medical_cost_intelligence", destination=destination)
        
        return self.tavily_service.get_medical_cost_intelligence(destination)
    
    # NEW AGENTIC AI TOOLS
    
    async def scan_gmail_for_trips(self, auth_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan user's Gmail for booking confirmations (Agentic AI)
        
        Args:
            auth_code: OAuth authorization code (if first time)
            
        Returns:
            Found bookings with extracted trip details
        """
        logger.info("tool_scan_gmail")
        
        try:
            # If auth_code provided, authorize first
            if auth_code:
                auth_result = await self.gmail_agent.authorize_user(auth_code)
                if not auth_result.get("authorized"):
                    return {"error": "Gmail authorization failed", "auth_result": auth_result}
            
            # Search for bookings
            bookings = await self.gmail_agent.search_for_bookings()
            
            if not bookings:
                return {
                    "found_bookings": False,
                    "count": 0,
                    "message": "No booking confirmations found in your recent emails."
                }
            
            # Format for display
            formatted = self.gmail_agent.format_bookings_for_display(bookings)
            
            return {
                "found_bookings": True,
                "count": len(bookings),
                "bookings": [
                    {
                        "email_id": b.email_id,
                        "subject": b.subject,
                        "booking_type": b.booking_type,
                        "confidence": b.confidence,
                        "extracted_data": b.extracted_data
                    }
                    for b in bookings
                ],
                "display_message": formatted
            }
        
        except Exception as e:
            logger.error("gmail_scan_failed", error=str(e))
            return {"error": f"Failed to scan Gmail: {str(e)}"}
    
    async def lookup_flight_booking(self, booking_ref: str) -> Dict[str, Any]:
        """
        Look up flight booking by reference number (Agentic AI)
        
        Args:
            booking_ref: Flight booking reference/PNR
            
        Returns:
            Flight booking details with extracted trip information
        """
        logger.info("tool_lookup_flight", booking_ref=booking_ref)
        
        try:
            # Look up booking
            booking = await self.flight_api_agent.lookup_booking(booking_ref)
            
            if not booking:
                return {
                    "found": False,
                    "error": "Booking not found. Please check your reference number and try again."
                }
            
            # Extract trip details for insurance
            trip_details = self.flight_api_agent.extract_trip_details(booking)
            
            # Format for display
            formatted = self.flight_api_agent.format_booking_for_display(booking)
            
            return {
                "found": True,
                "booking_ref": booking_ref,
                "airline": booking.get("airline"),
                "booking_details": booking,
                "trip_details": trip_details,
                "display_message": formatted
            }
        
        except Exception as e:
            logger.error("flight_lookup_failed", error=str(e), booking_ref=booking_ref)
            return {"error": f"Failed to lookup flight: {str(e)}"}
    
    async def select_gmail_booking(self, email_id: str, bookings: List[Any]) -> Dict[str, Any]:
        """
        User selected a booking from Gmail scan results
        
        Args:
            email_id: ID of selected email
            bookings: List of found bookings
            
        Returns:
            Extracted trip details from selected booking
        """
        logger.info("tool_select_gmail_booking", email_id=email_id)
        
        # Find the selected booking
        selected = next((b for b in bookings if b.email_id == email_id), None)
        
        if not selected:
            return {"error": "Selected booking not found"}
        
        # Extract trip details
        trip_details = self.gmail_agent.extract_trip_details_from_booking(selected)
        
        return {
            "success": True,
            "trip_details": trip_details,
            "booking_type": selected.booking_type,
            "message": f"Perfect! I've extracted the details from your {selected.booking_type} booking. Let me find the best coverage! ✨"
        }


