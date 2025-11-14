"""
TravelMate AI - Conversation Orchestration Service
Orchestrates multiple MCP tools to handle complex conversational flows
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session
from datetime import datetime
from app.utils.logger import get_logger
from app.services.session_store import get_session_store

if TYPE_CHECKING:
    from app.mcp.tools import MCPTools

logger = get_logger(__name__)


class ConversationOrchestrator:
    """
    Orchestrates conversational flow with intelligent tool calling
    Automatically triggers appropriate tools based on user intent
    """
    
    def __init__(self, db: Session):
        # Import here to avoid circular dependency
        from app.mcp.tools import MCPTools
        from app.mcp.resources import MCPResources
        from app.services.claims_analytics_service import ClaimsAnalyticsService
        from app.claims.claims_db import get_claims_db
        # NEW: Dynamic LLM-powered services (no hardcoded if-statements!)
        from app.services.enhanced_emotional_intelligence import get_enhanced_emotional_intelligence
        from app.services.dynamic_proactive_service import get_dynamic_proactive_service
        from app.services.dynamic_personality_service import get_dynamic_personality_service
        from app.services.trip_context import TripContext
        from app.services.trip_discovery_agent import TripDiscoveryAgent
        from app.services.gmail_agent import GmailAgent
        from app.services.flight_api_agent import FlightAPIAgent
        from app.services.intent_classifier import IntentClassifier
        from app.services.conversational_response_generator import ConversationalResponseGenerator
        # TAXONOMY: Real policy data from populated JSON
        from app.services.taxonomy_service import get_taxonomy_service
        # MULTI-PRODUCT PRICING: Real pricing from Ancileo API
        from app.services.multi_product_pricing import get_multi_product_pricing_service
        
        self.db = db
        self.tools = MCPTools(db)
        self.resources = MCPResources(db)  # NEW: Direct access to taxonomy
        self.taxonomy_service = get_taxonomy_service()  # NEW: Taxonomy service
        self.multi_pricing_service = get_multi_product_pricing_service()  # NEW: Multi-product pricing
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_store = get_session_store()
        
        # Initialize trip context (persistent state)
        self.trip_context = TripContext()
        
        # Initialize discovery agents
        self.gmail_agent = GmailAgent()
        self.flight_agent = FlightAPIAgent()
        self.discovery_agent = TripDiscoveryAgent(
            gmail_agent=self.gmail_agent,
            flight_agent=self.flight_agent
        )
        
        # Initialize claims analytics
        try:
            claims_db = get_claims_db()
            claims_session = claims_db.get_session()
            self.claims_analytics = ClaimsAnalyticsService(claims_session)
        except Exception as e:
            logger.warning("claims_analytics_initialization_failed", error=str(e))
            self.claims_analytics = None
        
        # Initialize AI services - UPGRADED to Dynamic LLM Services! 🚀
        self.intent_classifier = IntentClassifier()  # LLM-based intent classification
        self.emotional_intelligence = get_enhanced_emotional_intelligence()  # ✅ Detects ANY emotion
        self.proactive_intelligence = get_dynamic_proactive_service()  # ✅ Handles ANY activity/country
        self.personality_service = get_dynamic_personality_service()  # ✅ NEW: Dynamic personality
        self.response_generator = ConversationalResponseGenerator()  # LLM-generated responses
    
    async def handle_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method - handles any user message intelligently
        
        Args:
            message: User's conversational message
            session_id: Optional session identifier for persistence
            context: Optional conversation context (includes conversation_history from OpenAI format)
            
        Returns:
            Comprehensive response with answer and metadata
        """
        logger.info("orchestrator_message_received", message_length=len(message), session_id=session_id)
        
        # Load conversation history from persistent storage if session_id provided
        if session_id:
            saved_session = self.session_store.load_session(session_id)
            if saved_session:
                self.conversation_history = saved_session.get("conversation_history", [])
                logger.info("session_loaded_from_storage", 
                           session_id=session_id, 
                           history_length=len(self.conversation_history))
                
                # Load trip context (CRITICAL: preserves all trip data)
                if saved_session.get("trip_context"):
                    from app.services.trip_context import TripContext
                    self.trip_context = TripContext.from_dict(saved_session["trip_context"])
                    logger.info("trip_context_restored", 
                               completeness=f"{self.trip_context.calculate_completeness():.0%}",
                               destination=self.trip_context.destination_country)
                
                # Check if Gmail scan results are waiting and add to context
                if saved_session.get("gmail_scan_results"):
                    if not context:
                        context = {}
                    context["gmail_scan_results"] = saved_session.get("gmail_scan_results")
                    logger.info("gmail_scan_results_loaded_from_session", 
                               count=len(saved_session.get("gmail_scan_results", [])))
                
                # Also load extracted trip details if available (backwards compatibility)
                if not context:
                    context = {}
                if "extracted_trip_details" not in context and saved_session.get("extracted_trip_details"):
                    context["extracted_trip_details"] = saved_session["extracted_trip_details"]
                
                # Load recommendation data for comparison flow
                if saved_session.get("taxonomy_comparison"):
                    context["taxonomy_comparison"] = saved_session["taxonomy_comparison"]
                    logger.info("taxonomy_comparison_loaded_from_session")
                
                if saved_session.get("eligible_products"):
                    context["eligible_products"] = saved_session["eligible_products"]
                    logger.info("eligible_products_loaded_from_session", 
                               count=len(saved_session["eligible_products"]))
                
                if saved_session.get("quotes"):
                    context["quotes"] = saved_session["quotes"]
                    logger.info("quotes_loaded_from_session", 
                               count=len(saved_session["quotes"]))
                
                if saved_session.get("real_time_intelligence"):
                    context["real_time_intelligence"] = saved_session["real_time_intelligence"]
                    logger.info("real_time_intelligence_loaded_from_session")
        
        # Load conversation history from context if provided (for OpenAI compatibility)
        # BUT: Only if it's longer than what we loaded from storage (to avoid overwriting with empty history)
        if context and "conversation_history" in context:
            context_history = context["conversation_history"]
            if len(context_history) > len(self.conversation_history):
                # Context has more history, use it
                self.conversation_history = context_history
                logger.info("orchestrator_using_context_history", history_length=len(self.conversation_history))
            else:
                # Session storage has equal or more history, keep it
                logger.info("orchestrator_keeping_session_history", 
                           session_length=len(self.conversation_history),
                           context_length=len(context_history))
        elif not self.conversation_history:
            # Reset for new conversation
            self.conversation_history = []
        
        # PRIORITY 0: Check if user is selecting a booking from Gmail scan results
        if context and context.get("gmail_scan_results"):
            # Check if user message is a number (selecting a booking)
            if message.strip().isdigit():
                booking_num = int(message.strip())
                scan_results = context["gmail_scan_results"]
                
                if 1 <= booking_num <= len(scan_results):
                    logger.info("gmail_booking_selected", booking_num=booking_num)
                    
                    # Get selected booking
                    selected_booking_dict = scan_results[booking_num - 1]
                    
                    # Convert dict to EmailBooking object for processing
                    from app.services.gmail_agent import EmailBooking
                    selected_booking = EmailBooking(
                        email_id=selected_booking_dict.get("email_id", ""),
                        subject=selected_booking_dict.get("subject", ""),
                        sender="",
                        date=datetime.now(),
                        booking_type=selected_booking_dict.get("booking_type", "unknown"),
                        extracted_data=selected_booking_dict.get("extracted_data", {}),
                        confidence=selected_booking_dict.get("extracted_data", {}).get("confidence", 0.7),
                        raw_body=""
                    )
                    
                    # Extract trip details
                    trip_details = self.gmail_agent.extract_trip_details_from_booking(selected_booking)
                    
                    # Merge into trip_context
                    self.trip_context.merge(trip_details)
                    
                    logger.info("gmail_booking_merged_to_context",
                               destination=trip_details.get("destination_country"),
                               source=trip_details.get("source"))
                    
                    # Clear scan results (already selected)
                    if context:
                        context["gmail_scan_results"] = None
                    
                    # Detect emotion for this message (DYNAMIC!)
                    emotional_profile = self.emotional_intelligence.analyze_emotional_state(
                        message=message,
                        conversation_history=self.conversation_history
                    )
                    
                    # Auto-proceed to generate quote
                    logger.info("gmail_booking_selected_auto_quote")
                    return await self._handle_recommendation_flow(message, context, emotional_profile)
                else:
                    # Invalid number
                    return {
                        "intent": "scan_email",
                        "answer": f"Please select a number between 1 and {len(scan_results)}.",
                        "bookings": scan_results
                    }
            else:
                # User sent a non-number message - check if it's an insurance request
                message_lower = message.lower()
                is_insurance_request = any(phrase in message_lower for phrase in [
                    "insurance", "find", "recommend", "quote", "policy", "coverage",
                    "travel to", "traveling to", "trip to", "need", "i'm going", "i am going"
                ])
                
                if is_insurance_request:
                    # User wants insurance - extract trip from Gmail results and proceed
                    logger.info("gmail_auto_using_scan_results_for_insurance")
                    
                    # Get all bookings and extract trip details
                    from app.services.gmail_agent import EmailBooking
                    scan_results = context["gmail_scan_results"]
                    
                    # Use first booking to extract trip details
                    if scan_results:
                        first_booking_dict = scan_results[0]
                        selected_booking = EmailBooking(
                            email_id=first_booking_dict.get("email_id", ""),
                            subject=first_booking_dict.get("subject", ""),
                            sender="",
                            date=datetime.now(),
                            booking_type=first_booking_dict.get("booking_type", "unknown"),
                            extracted_data=first_booking_dict.get("extracted_data", {}),
                            confidence=first_booking_dict.get("extracted_data", {}).get("confidence", 0.7),
                            raw_body=""
                        )
                        
                        # Extract trip details from booking
                        trip_details = self.gmail_agent.extract_trip_details_from_booking(selected_booking)
                        
                        # Merge into trip context
                        self.trip_context.merge(trip_details)
                        
                        logger.info("gmail_trip_auto_extracted", trip_details=str(trip_details)[:200])
                        
                        # Clear scan results (used)
                        context["gmail_scan_results"] = None
                    
                    # Let normal intent detection proceed
                    intent_result = self.intent_classifier.classify_intent(
                        message=message,
                        conversation_history=self.conversation_history,
                        trip_context=self.trip_context.to_dict()
                    )
                    intent = intent_result.intent
                else:
                    # Not an insurance request - show scan results again
                    logger.info("gmail_scan_results_waiting_auto_displaying")
                    intent = "scan_email"
                    intent_result = type('obj', (object,), {
                        'intent': 'scan_email',
                        'confidence': 1.0,
                        'reasoning': 'Gmail scan results from OAuth callback'
                    })()
        else:
            # Step 1: Detect intent using LLM (smarter than keywords!)
            intent_result = self.intent_classifier.classify_intent(
                message=message,
                conversation_history=self.conversation_history,
                trip_context=self.trip_context.to_dict()
            )
            intent = intent_result.intent
        
        logger.info("orchestrator_intent_detected", 
                   intent=intent,
                   confidence=intent_result.confidence,
                   reasoning=intent_result.reasoning[:80] if hasattr(intent_result, 'reasoning') else 'auto')
        
        # Step 1.5: Detect emotional context for empathetic responses (DYNAMIC!)
        emotional_profile = self.emotional_intelligence.analyze_emotional_state(
            message=message,
            conversation_history=self.conversation_history
        )
        logger.info("orchestrator_emotion_detected", 
                   emotion=emotional_profile.primary_emotion,
                   intensity=emotional_profile.intensity,
                   confidence=emotional_profile.confidence)
        
        response = {}
        # Step 2: Route to appropriate flow (pass emotional_profile for natural responses)
        if intent == "recommendation_request":
            response = await self._handle_recommendation_flow(message, context, emotional_profile)
        
        elif intent == "scan_email":
            response = await self._handle_email_scan_flow(message, context, session_id)
        
        elif intent == "trip_details":
            response = await self._handle_trip_details_flow(message, context, emotional_profile)
        
        elif intent == "policy_question":
            response = await self._handle_policy_question_flow(message, context)
        
        elif intent == "compare_policies":
            response = self._handle_comparison_flow(message, context)
        
        else:
            # Default: conversational extraction + general response
            response = self._handle_general_flow(message, context, emotional_profile)
        
        # Step 3: Adapt response based on emotional intelligence (DYNAMIC!)
        # SKIP for data collection - LLM already generates contextual responses
        if response.get("answer"):
            original_answer = response["answer"]
            
            # Determine context type
            is_collecting_data = not response.get("extraction_complete", True)
            is_policy_question = response.get("intent") == "policy_question"
            is_recommendation = "recommend" in original_answer.lower() or "policy" in original_answer.lower()
            
            if is_collecting_data:
                # SKIP emotional adaptation - LLM response generator already handles it
                logger.info("skipping_emotional_adaptation_for_data_collection", 
                           emotion=emotional_profile.primary_emotion)
                response["emotional_context"] = {
                    "detected_emotion": emotional_profile.primary_emotion,
                    "intensity": emotional_profile.intensity,
                    "confidence": emotional_profile.confidence
                }
            elif is_policy_question or is_recommendation:
                # DISABLED: Emotional adaptation was corrupting responses
                # Keep original response as-is
                response["answer"] = original_answer
                response["emotional_context"] = {
                    "detected_emotion": emotional_profile.primary_emotion,
                    "intensity": emotional_profile.intensity,
                    "secondary_emotions": emotional_profile.secondary_emotions,
                    "concerns": emotional_profile.detected_concerns,
                    "confidence": emotional_profile.confidence
                }
                logger.info("orchestrator_emotional_context_added", 
                           emotion=emotional_profile.primary_emotion,
                           intensity=emotional_profile.intensity)

        # Update conversation history with current exchange
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response.get("answer", "")})
        
        # Store context for next turn
        response["context"] = {
            "conversation_history": self.conversation_history,
            "extracted_trip_details": response.get("trip_details", {})
        }
        
        # Save session to persistent storage if session_id provided
        if session_id:
            # Preserve gmail_scan_results if they exist
            gmail_scan_results = response.get("bookings") or (context.get("gmail_scan_results") if context else None)
            
            self.session_store.save_session(
                session_id=session_id,
                conversation_history=self.conversation_history,
                extracted_trip_details=response.get("trip_details", {}),
                trip_context=self.trip_context.to_dict(),  # CRITICAL: Save trip context
                gmail_scan_results=gmail_scan_results,  # Persist scan results
                taxonomy_comparison=response.get("taxonomy_comparison"),  # Save for comparisons
                eligible_products=response.get("eligible_products"),  # Save for UI
                quotes=response.get("quotes"),  # Save pricing data
                real_time_intelligence=response.get("real_time_intelligence")  # Save claims/risk data
            )
            logger.info("session_saved_to_storage", 
                       session_id=session_id, 
                       history_length=len(self.conversation_history),
                       trip_completeness=f"{self.trip_context.calculate_completeness():.0%}",
                       has_gmail_results=bool(gmail_scan_results),
                       has_recommendations=bool(response.get("eligible_products")))
        
        return response
    
    async def _handle_recommendation_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        emotional_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Handle recommendation requests with full Tavily intelligence
        This is the PRIMARY flow that uses Phase 3 tools
        """
        logger.info("orchestrator_recommendation_flow_started")
        
        response = {
            "intent": "recommendation_request",
            "answer": "",
            "trip_details": {},
            "real_time_intelligence": {},
            "policy_recommendations": [],
            "follow_up_questions": [],
            "agent_activities": []  # Track what agents are doing
        }
        
        # Step 0: Auto-discovery check (INNOVATION!)
        # If user says "I need insurance" and we have no trip data, proactively offer discovery
        # BUT: Don't trigger for urgent/business travelers who want quick answers
        is_initial_request = any(phrase in message.lower() for phrase in ["need insurance", "want insurance", "buy insurance", "looking for insurance"])
        has_minimal_data = self.trip_context.calculate_completeness() < 0.3
        is_urgent = any(word in message.lower() for word in ["quick", "fast", "urgent", "asap", "next week", "tomorrow", "business trip"])
        
        if is_initial_request and has_minimal_data and not is_urgent:
            logger.info("auto_discovery_offered", reason="initial_insurance_request")
            
            # Check if user mentioned a booking reference
            booking_ref_match = self._extract_booking_reference(message)
            
            if booking_ref_match:
                # User provided booking reference - offer to look it up
                response["answer"] = f"""Great! I can look up your booking {booking_ref_match} to get all the details automatically. ✈️

Should I pull up that booking, or would you prefer to tell me about your trip?"""
                response["suggested_actions"] = [
                    {"type": "lookup_booking", "label": f"Look up {booking_ref_match}", "icon": "🔍", "data": booking_ref_match},
                    {"type": "manual_entry", "label": "I'll tell you", "icon": "💬"}
                ]
                return response
            
            # Proactive discovery offer with Gmail authorization
            # Generate Gmail auth URL for user
            gmail_auth_url = self.gmail_agent.get_authorization_url(session_id or "no_session")
            
            response["answer"] = f"""I can help! I can find your trip details in a few ways:

1. 📧 **Scan your email** - Connect your Gmail to find bookings automatically
2. ✈️ **Booking reference** - Enter your flight/hotel confirmation number  
3. 💬 **Tell me manually** - Just describe your trip

Which would you prefer?"""
            
            response["suggested_actions"] = [
                {"type": "authorize_gmail", "label": "Connect Gmail", "icon": "📧", "data": gmail_auth_url},
                {"type": "enter_booking_ref", "label": "Enter Booking #", "icon": "✈️"},
                {"type": "manual_entry", "label": "Tell You Manually", "icon": "💬"}
            ]
            return response
        
        # Step 1: Extract trip details from conversation (Phase 3)
        logger.info("orchestrator_extracting_trip_details")
        
        # Build extraction context that includes:
        # 1. CURRENT trip_context (source of truth!)
        # 2. Conversation history (for understanding context)
        extraction_context = self.trip_context.to_dict()  # Start with what we already know!
        
        if context:
            # Add conversation history to help LLM understand context
            if "conversation_history" in context:
                extraction_context["conversation_history"] = context["conversation_history"]
        
        extraction = self.tools.extract_trip_from_conversation(message, extraction_context)
        
        # CRITICAL: Merge into trip_context (never lose data)
        extracted_data = extraction.get("extracted", {})
        
        logger.info("before_merge",
                   extracted_duration=extracted_data.get('trip_duration_days'),
                   current_duration=self.trip_context.trip_duration_days,
                   extracted_destination=extracted_data.get('destination_country'),
                   current_destination=self.trip_context.destination_country)
        
        self.trip_context.merge(extracted_data)
        
        logger.info("after_merge",
                   duration=self.trip_context.trip_duration_days,
                   destination=self.trip_context.destination_country,
                   travelers=len(self.trip_context.travelers))
        
        # Check completeness based on ACTUAL critical fields
        missing_critical = self.trip_context.get_missing_critical_fields()
        
        # To generate a quote, we MUST have: destination, duration OR dates, and ages
        # Don't claim we're "complete" if we're missing critical data
        has_destination = bool(self.trip_context.destination_country)
        has_duration_or_dates = bool(self.trip_context.trip_duration_days or (self.trip_context.departure_date and self.trip_context.return_date))
        has_ages = self.trip_context.travelers and all(t.get('age') for t in self.trip_context.travelers)
        
        is_complete = has_destination and has_duration_or_dates and has_ages
        
        # Use trip_context as source of truth
        response["trip_details"] = self.trip_context.to_dict()
        response["extraction_complete"] = is_complete
        
        logger.info("trip_context_final",
                   completeness=f"{self.trip_context.calculate_completeness():.0%}",
                   missing_fields=missing_critical,
                   trip_dict=str(self.trip_context.to_dict())[:200])
        
        # If not complete, ask SMART follow-up based on what's ACTUALLY missing
        if not is_complete:
            # Get the user's last message from conversation history
            last_user_message = next(
                (msg['content'] for msg in reversed(self.conversation_history) if msg.get('role') == 'user'),
                message
            )
            
            # Use passed emotional_profile or detect if not provided
            if not emotional_context:
                emotional_context = self.emotional_intelligence.analyze_emotional_state(
                    message=last_user_message,
                    conversation_history=self.conversation_history
                )
            
            # Generate natural, contextual follow-up using LLM
            follow_up = self.response_generator.generate_followup_question(
                user_message=last_user_message,
                emotion=emotional_context.primary_emotion,
                missing_fields=missing_critical,
                trip_context=self.trip_context.to_dict(),
                conversation_history=self.conversation_history
            )
            
            # Skip proactive insights during data collection
            # We don't want to bombard users with travel warnings while celebrating
            # their anniversary or asking basic questions. Save insights for recommendations.
            # 
            # BEFORE: Showed "🚨 Travel advisory..." during data collection
            # AFTER: Just warm, natural questions. Insights come later with recommendations.
            
            response["answer"] = follow_up
            response["follow_up_questions"].append(follow_up)
            
            # Early return - conversation history will be updated by handle_message
            # Store extracted trip details in context for next turn
            response["context"] = {
                "conversation_history": self.conversation_history,
                "extracted_trip_details": response["trip_details"]
            }
            
            return response
        
        # Step 2: Get real-time intelligence (Phase 3 - Tavily) 🔥
        destination = response["trip_details"].get("destination_country")
        activities = response["trip_details"].get("planned_activities", [])
        travel_date = response["trip_details"].get("departure_date")
        
        if destination:
            logger.info("orchestrator_fetching_tavily_intelligence", destination=destination)
            
            # Get destination intelligence
            try:
                dest_intel = self.tools.get_destination_intelligence(destination, travel_date)
                response["real_time_intelligence"]["destination"] = dest_intel
                logger.info("orchestrator_destination_intel_success", findings=len(dest_intel.get("key_findings", [])))
            except Exception as e:
                logger.error("orchestrator_destination_intel_failed", error=str(e))
                response["real_time_intelligence"]["destination"] = {"error": str(e)}
            
            # Analyze real-time risks
            if activities:
                try:
                    risk_analysis = self.tools.analyze_real_time_risks(destination, activities, travel_date)
                    response["real_time_intelligence"]["risks"] = risk_analysis
                    logger.info("orchestrator_risk_analysis_success", risk_level=risk_analysis.get("overall_risk_level"))
                except Exception as e:
                    logger.error("orchestrator_risk_analysis_failed", error=str(e))
                    response["real_time_intelligence"]["risks"] = {"error": str(e)}
            
            # Get medical cost intelligence
            try:
                medical_intel = self.tools.get_medical_cost_intelligence(destination)
                response["real_time_intelligence"]["medical_costs"] = medical_intel
                logger.info("orchestrator_medical_intel_success")
            except Exception as e:
                logger.error("orchestrator_medical_intel_failed", error=str(e))
                response["real_time_intelligence"]["medical_costs"] = {"error": str(e)}
            
            # Get historical claims intelligence (Phase 5 - MSIG Data) 🔥
            if self.claims_analytics:
                try:
                    logger.info("orchestrator_fetching_claims_intelligence", destination=destination)
                    
                    # Map activities to claim types for analysis
                    claim_types = []
                    if activities:
                        if any(act.lower() in ['skiing', 'hiking', 'extreme_sports'] for act in activities):
                            claim_types.append("Medical")
                        claim_types.append("Baggage")  # Common for all trips
                    
                    claims_analysis = self.claims_analytics.get_comprehensive_risk_analysis(
                        destination=destination,
                        claim_types=claim_types if claim_types else None
                    )
                    
                    response["real_time_intelligence"]["historical_claims"] = claims_analysis
                    logger.info(
                        "orchestrator_claims_intel_success",
                        total_claims=claims_analysis.get("destination_profile", {}).get("total_claims", 0),
                        avg_claim=claims_analysis.get("destination_profile", {}).get("avg_claim_amount_sgd", 0)
                    )
                except Exception as e:
                    logger.error("orchestrator_claims_intel_failed", error=str(e))
                    response["real_time_intelligence"]["historical_claims"] = {"error": str(e)}
        
        # Step 3: Check eligibility using TAXONOMY (real policy data)
        logger.info("orchestrator_checking_taxonomy_eligibility")
        
        # Normalize trip details before validation
        normalized_trip_details = self._normalize_trip_details(response["trip_details"])
        
        # NEW: Use taxonomy-based eligibility check for real policy data
        try:
            taxonomy_comparison = self.resources.compare_taxonomy_products(
                product_keys=None,  # Check all products (A, B, C)
                trip_details=normalized_trip_details
            )
            
            # Get eligible products from taxonomy
            eligible_products = [
                product_key 
                for product_key, eligibility in taxonomy_comparison.get("eligibility", {}).items()
                if eligibility.get("is_eligible", False)
            ]
            
            logger.info("orchestrator_taxonomy_eligibility_complete", 
                       eligible_count=len(eligible_products),
                       products=eligible_products)
            
            # Store taxonomy comparison for later use
            response["taxonomy_comparison"] = taxonomy_comparison
            response["eligible_products"] = eligible_products
            
        except Exception as e:
            logger.error("orchestrator_taxonomy_check_failed", error=str(e))
            eligible_products = []
        
        # Fallback: Also check database policies if needed
        eligibility_results = self.tools.check_eligibility(
            trip_details=normalized_trip_details
        )
        
        eligible_policies = [
            e["policy_id"] for e in eligibility_results if e.get("is_eligible", False)
        ]
        
        logger.info("orchestrator_total_eligible_found", 
                   taxonomy_count=len(eligible_products),
                   database_count=len(eligible_policies))
        
        # Step 4: Compare eligible policies with real-time context
        # Prioritize taxonomy products (they have real data)
        if eligible_products or eligible_policies:
            logger.info("orchestrator_comparing_policies", 
                       taxonomy_count=len(eligible_products),
                       database_count=len(eligible_policies))
            
            # Build enhanced user context with Tavily intelligence
            enhanced_context = {
                **response["trip_details"],
                "real_time_intelligence": response["real_time_intelligence"]
            }
            
            comparison = self.tools.compare_policies(
                policy_ids=eligible_policies,
                comparison_criteria=["coverage_limits", "benefits", "price"],
                user_context=enhanced_context
            )
            
            response["policy_recommendations"] = comparison.get("policies", [])
            response["comparison_summary"] = comparison.get("summary", {})
            
            # Step 5: Generate actual quotes with REAL API pricing for taxonomy products 💰
            logger.info("orchestrator_generating_quotes", 
                       database_count=len(eligible_policies),
                       taxonomy_count=len(eligible_products))
            
            # Try to get real pricing for taxonomy products first
            taxonomy_quotes = []
            if eligible_products:
                try:
                    logger.info("orchestrator_fetching_real_api_pricing", products=eligible_products)
                    pricing_results = await self.multi_pricing_service.get_all_product_pricing(
                        trip_details=normalized_trip_details,
                        eligible_products=eligible_products
                    )
                    
                    # Convert pricing results to quote format
                    for product_key, pricing_data in pricing_results.items():
                        if not pricing_data.get("error"):
                            offers = pricing_data.get("offers", [])
                            for offer in offers:
                                taxonomy_quotes.append({
                                    "product_key": product_key,
                                    "quote_id": pricing_data.get("quote_id"),
                                    "offer_id": offer.get("offer_id"),
                                    "product_code": offer.get("product_code"),
                                    "premium": offer.get("unit_price", 0),
                                    "currency": offer.get("currency", "SGD"),
                                    "is_real_pricing": True,
                                    "source": "ancileo_api"
                                })
                    
                    logger.info("orchestrator_real_pricing_success", 
                               quotes=len(taxonomy_quotes))
                    
                except Exception as e:
                    logger.error("orchestrator_real_pricing_failed", error=str(e))
            
            # Also get database quotes as fallback/additional
            database_quotes = []
            try:
                quote_result = self.tools.get_quote(
                    trip_details=normalized_trip_details,
                    policy_ids=eligible_policies
                )
                
                database_quotes = quote_result.get("quotes", [])
                
                logger.info(
                    "orchestrator_database_quotes_generated",
                    quote_count=len(database_quotes)
                )
            except Exception as e:
                logger.error("orchestrator_quote_generation_failed", error=str(e))
            
            # Combine quotes (prioritize real API pricing)
            response["quotes"] = taxonomy_quotes + database_quotes
            response["real_pricing_count"] = len(taxonomy_quotes)
            response["total_premium"] = sum(q.get("premium", 0) for q in response["quotes"])
        
        # Step 6: Generate enhanced answer with Tavily insights + TAXONOMY + pricing
        # Determine if this is first-time recommendation (show full) or follow-up (show concise)
        is_first_recommendation = not any(
            indicator in str(self.conversation_history).lower()
            for indicator in ["scootsurance", "traveleasy", "recommended policies", "sgd $"]
        )
        
        # Include taxonomy recommendations in the answer
        # If we have taxonomy products, the UI will show visual components, so keep text minimal
        has_visual_component = len(response.get("eligible_products", [])) > 0
        
        if has_visual_component:
            # Concise but informative message when visual component will be shown
            destination = response["trip_details"].get("destination_country", "your destination")
            duration = response["trip_details"].get("trip_duration_days", 0)
            num_products = len(response.get("eligible_products", []))
            
            # Get the recommended product
            recommended_product = response.get("taxonomy_comparison", {}).get("recommendation", "")
            
            # Get risk level from claims data
            claims_data = response.get("real_time_intelligence", {}).get("historical_claims", {})
            dest_profile = claims_data.get("destination_profile", {})
            risk_level = dest_profile.get("risk_level", "").upper() if dest_profile.get("total_claims", 0) > 0 else ""
            
            # Simple, clean message - all details are in the visual component
            response["answer"] = f"Perfect! I found {num_products} insurance {'option' if num_products == 1 else 'options'} for your {duration}-day trip to {destination}."
        else:
            # Full detailed answer if no visual component
            response["answer"] = self._generate_enhanced_answer(
                response["trip_details"],
                response["real_time_intelligence"],
                response["policy_recommendations"],
                response.get("quotes", []),
                show_full_intelligence=is_first_recommendation,  # Only show full intelligence on first recommendation
                taxonomy_products=response.get("eligible_products", []),  # NEW: Taxonomy-based products
                taxonomy_recommendation=response.get("taxonomy_comparison", {}).get("recommendation")  # NEW: Recommended product
            )
        
        logger.info("orchestrator_recommendation_flow_complete")
        
        # Conversation history will be updated by handle_message
        # Store context for next turn
        response["context"] = {
            "conversation_history": self.conversation_history,
            "extracted_trip_details": response["trip_details"]
        }
        
        return response
    
    async def _handle_email_scan_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Handle email scanning request
        User explicitly asked to scan their email
        """
        logger.info("orchestrator_email_scan_flow")
        
        # Check if we have Google OAuth credentials configured
        from app.config import get_settings
        settings = get_settings()
        
        has_google_oauth = bool(settings.google_client_id and settings.google_client_secret)
        
        # If no OAuth configured, use mock data
        if not has_google_oauth:
            logger.info("gmail_using_mock_no_oauth_configured")
            
            bookings = await self.gmail_agent.search_for_bookings(credentials=None, use_mock=True)
            formatted = self.gmail_agent.format_bookings_for_display(bookings)
            formatted = f"**(Demo Mode: Showing sample bookings)**\n\n{formatted}"
            
            return {
                "intent": "scan_email",
                "answer": formatted,
                "bookings": [{"email_id": b.email_id, "subject": b.subject, "booking_type": b.booking_type, "extracted_data": b.extracted_data} for b in bookings],
                "agent_activities": [{"agent": "gmail", "status": "complete"}]
            }
        
        # Check if Gmail scan results are already in session (from OAuth callback)
        scan_results = context.get("gmail_scan_results") if context else None
        
        if scan_results and len(scan_results) > 0:
            # Results already available from OAuth callback!
            logger.info("gmail_using_cached_scan_results", count=len(scan_results))
            
            # Reconstruct EmailBooking objects for formatting
            from app.services.gmail_agent import EmailBooking
            bookings = []
            for result in scan_results:
                booking = EmailBooking(
                    email_id=result["email_id"],
                    subject=result["subject"],
                    sender="",
                    date=datetime.now(),
                    booking_type=result["booking_type"],
                    extracted_data=result["extracted_data"],
                    confidence=result["extracted_data"].get("confidence", 0.7),
                    raw_body=""
                )
                bookings.append(booking)
            
            formatted = self.gmail_agent.format_bookings_for_display(bookings)
            formatted = f"**(Found in your Gmail!)**\n\n{formatted}"
            
            return {
                "intent": "scan_email",
                "answer": formatted,
                "bookings": scan_results,
                "agent_activities": [{"agent": "gmail", "status": "complete", "ref": f"{len(bookings)} found"}]
            }
        
        # Check if user has already authorized (credentials exist for this session)
        credentials = self.gmail_agent.gmail_oauth.credentials_cache.get(session_id or "")
        
        if credentials:
            # User is authorized! Scan their real Gmail
            logger.info("gmail_scanning_with_real_credentials", session=session_id)
            
            bookings = await self.gmail_agent.search_for_bookings(credentials=credentials, use_mock=False)
            
            if not bookings:
                return {
                    "intent": "scan_email",
                    "answer": "I scanned your Gmail but didn't find any booking confirmations in the last 90 days. Could you tell me about your trip instead?",
                    "bookings": []
                }
            
            formatted = self.gmail_agent.format_bookings_for_display(bookings)
            formatted = f"**(Scanned your Gmail!)**\n\n{formatted}"
            
            return {
                "intent": "scan_email",
                "answer": formatted,
                "bookings": [{"email_id": b.email_id, "subject": b.subject, "booking_type": b.booking_type, "extracted_data": b.extracted_data} for b in bookings],
                "agent_activities": [{"agent": "gmail", "status": "complete", "ref": f"{len(bookings)} found"}]
            }
        
        # Not authorized yet - prompt for authorization
        # BUT FIRST: Extract any trip details they mentioned and add emotional context!
        logger.info("gmail_auth_needed_extracting_context")
        
        # Extract trip details from their message
        extraction_context = self.trip_context.to_dict()
        if context and "conversation_history" in context:
            extraction_context["conversation_history"] = context["conversation_history"]
        
        extraction = self.tools.extract_trip_from_conversation(message, extraction_context)
        extracted_data = extraction.get("extracted", {})
        self.trip_context.merge(extracted_data)
        
        # Detect emotional context
        emotional_profile = self.emotional_intelligence.analyze_emotional_state(
            message=message,
            conversation_history=self.conversation_history
        )
        
        # Build personalized response with emotional warmth
        answer_parts = []
        
        # Add emotional/contextual greeting if we detected something special
        destination = self.trip_context.destination_country or extracted_data.get("destination_country")
        trip_purpose = extracted_data.get("trip_purpose") or ""
        
        if emotional_profile.primary_emotion in ["excited", "happy", "celebratory"]:
            if "birthday" in message.lower():
                if destination:
                    answer_parts.append(f"How exciting - celebrating your birthday in {destination}! 🎂✨ ")
                else:
                    answer_parts.append("What a wonderful way to celebrate your birthday! 🎂 ")
            elif "honeymoon" in message.lower():
                answer_parts.append("Congratulations on your honeymoon! 💍 ")
            elif "anniversary" in message.lower():
                answer_parts.append("Happy anniversary! What a special trip! 🎊 ")
            else:
                if destination:
                    answer_parts.append(f"{destination} is such an exciting destination! ✨ ")
        elif destination:
            answer_parts.append(f"Perfect! I can help with your {destination} trip. ")
        
        # Add Gmail authorization request
        answer_parts.append("Let me connect to your Gmail to fetch your booking details automatically.\n\n")
        answer_parts.append("🔒 I'll only access booking confirmations (flights, hotels) - no other emails.\n\n")
        answer_parts.append("Click below to authorize:")
        
        auth_url = self.gmail_agent.get_authorization_url(session_id or "no_session")
        
        return {
            "intent": "scan_email",
            "answer": "".join(answer_parts),
            "trip_details": self.trip_context.to_dict(),  # Include extracted trip context
            "suggested_actions": [
                {"type": "authorize_gmail", "label": "🔐 Connect Gmail", "icon": "📧", "data": auth_url}
            ],
            "agent_activities": [
                {"agent": "gmail", "status": "waiting_for_auth"}
            ]
        }
    
    async def _handle_trip_details_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        emotional_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle trip details extraction without recommendation"""
        logger.info("orchestrator_trip_details_flow")
        
        # Build context from trip_context
        extraction_context = self.trip_context.to_dict()
        if context and "conversation_history" in context:
            extraction_context["conversation_history"] = context["conversation_history"]
        
        extraction = self.tools.extract_trip_from_conversation(message, extraction_context)
        
        # CRITICAL: Merge into trip_context (same as recommendation flow!)
        extracted_data = extraction.get("extracted", {})
        self.trip_context.merge(extracted_data)
        
        # Check if actually complete (destination + duration + ages)
        has_destination = bool(self.trip_context.destination_country)
        has_duration_or_dates = bool(self.trip_context.trip_duration_days or (self.trip_context.departure_date and self.trip_context.return_date))
        has_ages = self.trip_context.travelers and all(t.get('age') for t in self.trip_context.travelers)
        is_complete = has_destination and has_duration_or_dates and has_ages
        
        # Generate smart follow-up or proceed to quote if complete
        if not is_complete:
            missing_fields = self.trip_context.get_missing_critical_fields()
            
            # Use passed emotional_profile or detect if not provided
            if not emotional_context:
                emotional_context = self.emotional_intelligence.analyze_emotional_state(
                    message=message,
                    conversation_history=self.conversation_history
                )
            
            # Generate LLM-based natural follow-up
            answer = self.response_generator.generate_followup_question(
                user_message=message,
                emotion=emotional_context.primary_emotion,
                missing_fields=missing_fields,
                trip_context=self.trip_context.to_dict(),
                conversation_history=self.conversation_history
            )
            
            return {
                "intent": "trip_details",
                "answer": answer,
                "trip_details": self.trip_context.to_dict(),
                "extraction_complete": False
            }
        else:
            # Complete! Auto-switch to recommendation flow and generate quote
            logger.info("trip_complete_auto_generating_quote")
            return await self._handle_recommendation_flow(message, context)
    
    async def _handle_policy_question_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle policy-specific questions - NOW WITH TAXONOMY SUPPORT!"""
        logger.info("orchestrator_policy_question_flow")
        
        # NEW: Check if this is really a coverage/recommendation question that should use taxonomy
        message_lower = message.lower()
        is_coverage_inquiry = any(
            phrase in message_lower
            for phrase in ["do you have", "insurance that covers", "coverage for", 
                          "policies that cover", "insurance for", "need insurance"]
        )
        
        # If user has trip context and asking about coverage, use taxonomy!
        if is_coverage_inquiry and self.trip_context.calculate_completeness() > 0.3:
            logger.info("policy_question_redirecting_to_taxonomy_recommendation")
            # Redirect to recommendation flow which uses taxonomy
            return await self._handle_recommendation_flow(message, context)
        
        # Check if this is a pricing question and we have recent quotes in conversation
        message_lower = message.lower()
        is_pricing_question = any(
            keyword in message_lower 
            for keyword in ["price", "cost", "how much", "premium", "pricing", "quote"]
        )
        
        # Check if this is also a comparison request
        is_comparison_request = any(
            keyword in message_lower 
            for keyword in ["compare", "comparison", "difference", "between", "versus", "vs", "vs."]
        )
        
        # Handle compound request: pricing + comparison
        if is_pricing_question and is_comparison_request:
            logger.info("compound_request_pricing_and_comparison")
            
            # Get pricing from history
            pricing_info = self._extract_pricing_from_history()
            
            # Get comparison
            comparison = self.tools.compare_policies(
                policy_ids=None,  # Compare all
                user_context=context
            )
            
            # Merge both answers
            answer_parts = []
            
            # Part 1: Pricing
            if pricing_info:
                answer_parts.append("## Pricing\n\n")
                for policy_name, premium in pricing_info.items():
                    answer_parts.append(f"**{policy_name}:** SGD ${premium:,.2f}\n")
                answer_parts.append("\n---\n\n")
            
            # Part 2: Comparison
            answer_parts.append(self._format_comparison_answer(comparison))
            
            return {
                "intent": "policy_question_compound",
                "answer": "".join(answer_parts),
                "pricing": pricing_info,
                "comparison": comparison
            }
        
        # Check if user wants to know WHAT'S INCLUDED (benefits/coverage) not just price
        is_benefits_question = any(
            phrase in message_lower
            for phrase in ["what is included", "what's included", "what does it cover", 
                          "what's covered", "benefits", "coverage details", "what do i get"]
        )
        
        # Handle benefits/coverage question
        if is_benefits_question or (is_pricing_question and "include" in message_lower):
            # User wants to know what's covered for the price, not just the price
            # Get the recommended policy from recent conversation
            recommended_policy = self._extract_recommended_policy_from_history()
            
            if recommended_policy:
                # Show detailed benefits for that policy
                qa_result = self.tools.answer_policy_question(
                    question=f"What benefits and coverage are included in the {recommended_policy} policy? List all the key coverage items.",
                    include_citations=True
                )
                
                answer = f"Here's what's included in the **{recommended_policy}** policy:\n\n{qa_result.get('answer', '')}"
                
                return {
                    "intent": "policy_question",
                    "answer": answer,
                    "confidence": qa_result.get("confidence_score", 0),
                    "citations": qa_result.get("citations", [])
                }
        
        # Handle pricing-only question (just want the price number)
        if is_pricing_question:
            # Try to extract pricing from conversation history
            pricing_info = self._extract_pricing_from_history()
            
            if pricing_info:
                logger.info("pricing_question_answered_from_context", policies_found=len(pricing_info))
                
                # Generate answer from pricing info
                answer_parts = ["Based on your trip details, here are the prices:\n\n"]
                
                for policy_name, premium in pricing_info.items():
                    answer_parts.append(f"**{policy_name}:** SGD ${premium:,.2f}\n")
                
                answer_parts.append("\nThese prices are calculated based on your destination, trip duration, age, and activities.")
                answer_parts.append("\n\nWould you like to proceed with purchasing one of these policies?")
                
                return {
                    "intent": "policy_question",
                    "answer": "".join(answer_parts),
                    "confidence": 1.0,
                    "source": "conversation_context"
                }
        
        # Fall back to Q&A from policy documents
        qa_result = self.tools.answer_policy_question(
            question=message,
            include_citations=True
        )
        
        # Format answer with citations
        answer = qa_result.get("answer", "I couldn't find specific information about that.")
        citations = qa_result.get("citations", [])
        
        # Append citations to answer if available
        if citations and len(citations) > 0:
            answer += "\n\n---\n\n### Sources\n\n"
            for i, citation in enumerate(citations[:5], 1):  # Show top 5 citations
                # Citations can be strings or dicts
                if isinstance(citation, dict):
                    policy_id = citation.get("policy_id", "Unknown")
                    page = citation.get("page", "N/A")
                    excerpt = citation.get("text", "")[:150]  # First 150 chars
                    
                    answer += f"{i}. **{policy_id}** (Page {page})\n"
                    if excerpt:
                        answer += f"   > \"{excerpt}...\"\n"
                    answer += "\n"
                elif isinstance(citation, str):
                    # Citation is already formatted as string
                    answer += f"{i}. {citation}\n"
                else:
                    # Unknown format, skip
                    pass
        
        return {
            "intent": "policy_question",
            "answer": answer,
            "confidence": qa_result.get("confidence_score", 0),
            "citations": citations
        }
    
    def _extract_recommended_policy_from_history(self) -> Optional[str]:
        """
        Extract the recommended policy name from conversation history
        Looks for "Best Match" or first recommended policy
        """
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                
                # Look for recommended policy pattern
                import re
                
                # Pattern: **1. PolicyName** (Best Match)
                match = re.search(r'\*\*1\.\s*([^*]+?)\*\*\s*\(Best Match\)', content)
                if match:
                    policy_name = match.group(1).strip()
                    return policy_name
                
                # Fallback: Just find first policy mentioned
                match = re.search(r'\*\*1\.\s*([^*]+?)\*\*', content)
                if match:
                    policy_name = match.group(1).strip()
                    return policy_name
        
        return None
    
    def _extract_pricing_from_history(self) -> dict:
        """
        Extract pricing information from conversation history
        Returns dict of {policy_name: premium}
        """
        pricing_info = {}
        
        # Look through conversation history for pricing information
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                
                # Look for pricing patterns like "Price: SGD $450.00"
                # Pattern: **{PolicyName}** ... **Price: SGD ${amount}**
                import re
                
                # Find policy names and their prices
                policy_price_pattern = r'\*\*(?:1\.|2\.)\s*([^*]+?)\*\*.*?\*\*Price:\s*SGD\s*\$([0-9,]+\.[0-9]{2})\*\*'
                matches = re.findall(policy_price_pattern, content, re.DOTALL)
                
                for policy_name, price_str in matches:
                    policy_name = policy_name.strip().replace(" (Best Match)", "").replace(" (Alternative Option)", "")
                    try:
                        price = float(price_str.replace(",", ""))
                        pricing_info[policy_name] = price
                    except ValueError:
                        continue
                
                # If we found pricing, return it (most recent)
                if pricing_info:
                    logger.info("extracted_pricing_from_history", policies=list(pricing_info.keys()))
                    return pricing_info
        
        return pricing_info
    
    def _handle_comparison_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle policy comparison requests"""
        logger.info("orchestrator_comparison_flow")
        
        # Extract policy IDs from context or message
        policy_ids = context.get("policy_ids", []) if context else []
        
        # If user asked to compare same policy with itself (or no specific policies mentioned),
        # default to showing all available taxonomy products from the current recommendation
        if not policy_ids:
            # Check if we have eligible products from a previous recommendation
            if context and context.get("eligible_products"):
                # User already saw recommendations - just return them with comparison data
                logger.info("comparison_using_existing_recommendations",
                           products=context.get("eligible_products"))
                
                return {
                    "intent": "compare_policies",
                    "answer": f"Here's your side-by-side comparison of {len(context['eligible_products'])} insurance options:",
                    "eligible_products": context.get("eligible_products", []),
                    "taxonomy_comparison": context.get("taxonomy_comparison"),
                    "quotes": context.get("quotes", []),
                    "trip_details": self.trip_context.to_dict(),
                    "real_time_intelligence": context.get("real_time_intelligence", {})
                }
            
            # Default to comparing all policies
            policy_ids = None
        
        comparison = self.tools.compare_policies(
            policy_ids=policy_ids,
            user_context=context
        )
        
        # Try to extract pricing from conversation history to include in comparison
        pricing_info = self._extract_pricing_from_history()
        
        # Check if we have taxonomy products in context (from previous recommendation)
        # OR if the policies being compared are taxonomy products (Product A/B/C)
        eligible_products = context.get("eligible_products", []) if context else []
        
        # Also check if the policies are taxonomy products by name
        policies = comparison.get("policies", [])
        is_taxonomy_comparison = any(
            policy.get("policy_name") in ["Scootsurance", "TravelEasy Standard", "TravelEasy Pre-Existing"]
            for policy in policies
        )
        
        has_visual_component = len(eligible_products) > 0 or is_taxonomy_comparison
        
        if has_visual_component:
            # Simple message when visual component is shown
            num_products = len(eligible_products) if eligible_products else len(policies)
            answer = f"Here's your side-by-side comparison of {num_products} insurance options:"
        else:
            # Full detailed comparison table if no visual component
            answer = self._format_comparison_answer(comparison, pricing_info)
        
        # Check if we have taxonomy data in trip_context (from previous recommendation)
        # Include it so the UI can show the visual comparison component
        taxonomy_comparison = None
        quotes = []
        trip_details = None
        real_time_intelligence = None
        
        # Try to get taxonomy data from the current session
        if is_taxonomy_comparison:
            # We're comparing taxonomy products - get the eligible products list
            if not eligible_products:
                # Extract from policies being compared
                eligible_products = [
                    policy.get("policy_id") 
                    for policy in policies 
                    if policy.get("policy_name") in ["Scootsurance", "TravelEasy Standard", "TravelEasy Pre-Existing"]
                ]
            
            # Include trip details and any cached intelligence
            trip_details = self.trip_context.to_dict()
            
            # Try to get taxonomy comparison data if we have it
            # This would come from a previous recommendation in the same session
            if context:
                taxonomy_comparison = context.get("taxonomy_comparison")
                quotes = context.get("quotes", [])
                real_time_intelligence = context.get("real_time_intelligence", {})
        
        return {
            "intent": "compare_policies",
            "answer": answer,
            "comparison": comparison,
            "pricing": pricing_info,
            "eligible_products": eligible_products,  # For UI
            "taxonomy_comparison": taxonomy_comparison,  # For UI highlighting
            "quotes": quotes,  # For pricing display
            "trip_details": trip_details,  # For trip summary
            "real_time_intelligence": real_time_intelligence  # For risk level
        }
    
    def _handle_general_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        emotional_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle general conversational messages"""
        logger.info("orchestrator_general_flow")
        
        # Build context from trip_context
        extraction_context = self.trip_context.to_dict()
        if context and "conversation_history" in context:
            extraction_context["conversation_history"] = context["conversation_history"]
        
        # Try to extract trip details for context building
        extraction = self.tools.extract_trip_from_conversation(message, extraction_context)
        
        # CRITICAL: Merge into trip_context!
        extracted_data = extraction.get("extracted", {})
        self.trip_context.merge(extracted_data)
        
        return {
            "intent": "general",
            "answer": extraction.get("follow_up_question", "I'm here to help you find the perfect travel insurance. What would you like to know?"),
            "trip_details": self.trip_context.to_dict(),  # Use merged context
            "suggestions": [
                "Get a quote for your trip",
                "Compare policy benefits",
                "Ask about specific coverage"
            ]
        }
    
    def _detect_intent(self, message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Detect user intent from message
        Uses conversation history for better context understanding
        
        Args:
            message: Current user message
            conversation_history: Previous conversation turns
        """
        message_lower = message.lower()
        
        # PRIORITY 0: Check for recommendation requests (even if phrased as questions)
        # "Which insurance should I get?" is a recommendation request, not a policy Q&A!
        recommendation_question_patterns = [
            "which insurance should", "which policy should", "what insurance should",
            "what policy should", "which should i", "which should we",
            "recommend", "suggest", "best insurance", "best policy"
        ]
        
        if any(pattern in message_lower for pattern in recommendation_question_patterns):
            logger.info("intent_recommendation_question", message_preview=message[:50])
            return "recommendation_request"
        
        # PRIORITY 1: Check for explicit policy questions (highest priority)
        # These should ALWAYS be routed to Q&A, regardless of context
        explicit_question_patterns = [
            "why", "how", "what is", "what does", "what are", "what's",
            "which one", "which policy", "which insurance",
            "explain", "tell me about", "does it cover", "is it covered",
            "is covered", "what's covered", "coverage", "covered",
            "how much", "how does", "when is", "who is", "where is",
            "can you provide", "provide me", "give me details", "more details",
            "additional details", "more information", "tell me more"
        ]
        
        # Check if message starts with a question word or contains explicit question patterns
        is_explicit_question = (
            any(message_lower.startswith(pattern) for pattern in explicit_question_patterns) or
            any(f" {pattern} " in f" {message_lower} " for pattern in explicit_question_patterns)
        )
        
        if is_explicit_question:
            # Check if it's a policy-related question (not trip planning)
            policy_related_keywords = [
                "pre-existing", "medical", "coverage", "benefit", "claim", "policy",
                "insur", "cover", "exclude", "include", "limit", "deductible",
                "premium", "accident", "emergency", "hospital", "treatment"
            ]
            
            if any(keyword in message_lower for keyword in policy_related_keywords):
                logger.info("intent_explicit_policy_question", message_preview=message[:50])
                return "policy_question"
        
        # PRIORITY 2: Check conversation context
        if conversation_history and len(conversation_history) > 0:
            last_assistant_msg = None
            second_last_assistant_msg = None
            assistant_msg_count = 0
            
            for msg in reversed(conversation_history):
                if msg.get("role") == "assistant":
                    if assistant_msg_count == 0:
                        last_assistant_msg = msg.get("content", "").lower()
                        assistant_msg_count += 1
                    elif assistant_msg_count == 1:
                        second_last_assistant_msg = msg.get("content", "").lower()
                        break
            
            # Check if recommendations have already been provided
            if last_assistant_msg or second_last_assistant_msg:
                recommendation_indicators = [
                    "scootsurance", "traveleasy", "recommended policies", 
                    "price:", "sgd $", "coverage highlights", "why we recommend",
                    "best match", "alternative option"
                ]
                
                has_recent_recommendations = any(
                    indicator in (last_assistant_msg or "") or indicator in (second_last_assistant_msg or "")
                    for indicator in recommendation_indicators
                )
                
                # If recommendations were provided, route most questions to Q&A
                if has_recent_recommendations:
                    # Check if asking for detailed quote/comparison
                    detailed_request = any(
                        pattern in message_lower
                        for pattern in ["detailed quote", "full quote", "complete quote", "more details about", "breakdown", "full breakdown"]
                    )
                    
                    if detailed_request:
                        logger.info("intent_detailed_comparison_request", context="after_recommendations")
                        return "compare_policies"
                    
                    # Only go back to recommendation flow if explicitly asking for new recommendation
                    explicit_new_recommendation = any(
                        pattern in message_lower 
                        for pattern in ["different policy", "other options", "what else", "other policies", "re-quote", "new quote"]
                    )
                    
                    if not explicit_new_recommendation:
                        # Check if it's a clarification/detail request
                        clarification_patterns = [
                            "more info", "tell me more", "explain",
                            "about", "coverage", "benefits", "why", "how", "what"
                        ]
                        if any(pattern in message_lower for pattern in clarification_patterns):
                            logger.info("intent_post_recommendation_question", context="policy_qa")
                            return "policy_question"
            
            # Check if assistant is actively collecting trip details
            if last_assistant_msg:
                is_asking_trip_details = any(
                    keyword in last_assistant_msg 
                    for keyword in ["where", "when", "how long", "how many", "destination", "dates", "old", "age", "travelers", "who"]
                )
                
                # Only continue trip collection if the response is actually answering those questions
                # Not if they're asking a different question
                if is_asking_trip_details and not is_explicit_question:
                    logger.info("intent_contextual_continuation", previous_context="trip_collection")
                    return "recommendation_request"
        
        # PRIORITY 3: Check for explicit recommendation requests
        recommendation_keywords = [
            "recommend", "suggest", "which policy", "best insurance",
            "which insurance", "what should i", "help me choose",
            "policy would you", "policy should i", "policy do you recommend",
            "what insurance", "need insurance", "get insurance", "want insurance",
            "looking for", "need a policy", "want a policy"
        ]
        if any(keyword in message_lower for keyword in recommendation_keywords):
            logger.info("intent_explicit_recommendation_request")
            return "recommendation_request"
        
        # PRIORITY 4: Check for comparison requests
        comparison_keywords = ["compare", "difference between", "versus", "vs", "vs."]
        if any(keyword in message_lower for keyword in comparison_keywords):
            logger.info("intent_comparison_request")
            return "compare_policies"
        
        # PRIORITY 5: Check for trip detail sharing (only if NO question pattern detected)
        if not is_explicit_question:
            trip_keywords = [
                "travelling to", "going to", "planning a trip", "visiting",
                "i'm going", "i will be", "trip to", "travel to", "heading to",
                "with my family", "with my wife", "with my husband", "with my kids"
            ]
            if any(keyword in message_lower for keyword in trip_keywords):
                logger.info("intent_trip_details_shared")
                return "recommendation_request"
        
        # DEFAULT: Route to general (which will try to intelligently handle it)
        logger.info("intent_default_general", message_preview=message[:50])
        return "general"
    
    def _normalize_trip_details(self, trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize trip details to match schema requirements
        Maps free-form data from LLM extraction to strict schema types
        """
        normalized = trip_details.copy()
        
        # Normalize activities to match ActivityType enum
        if "planned_activities" in normalized and normalized["planned_activities"]:
            normalized_activities = []
            activity_mapping = {
                # Map common activities to enum values
                "ski": "skiing",
                "skiing": "skiing",
                "snowboard": "skiing",
                "dive": "scuba_diving",
                "diving": "scuba_diving",
                "scuba": "scuba_diving",
                "snorkel": "water_sports",
                "surfing": "water_sports",
                "kayak": "water_sports",
                "sailing": "water_sports",
                "swim": "water_sports",
                "hike": "hiking",
                "hiking": "hiking",
                "trek": "hiking",
                "trekking": "hiking",
                "climb": "extreme_sports",
                "climbing": "extreme_sports",
                "bungee": "extreme_sports",
                "skydive": "extreme_sports",
                "parachute": "extreme_sports",
                "mountain": "extreme_sports"
            }
            
            for activity in normalized["planned_activities"]:
                activity_lower = str(activity).lower()
                # Check if activity matches any mapping
                mapped = "general"  # default
                for key, value in activity_mapping.items():
                    if key in activity_lower:
                        mapped = value
                        break
                normalized_activities.append(mapped)
            
            # Remove duplicates and keep at least one activity
            normalized["planned_activities"] = list(set(normalized_activities)) if normalized_activities else ["general"]
        elif "planned_activities" not in normalized:
            normalized["planned_activities"] = ["general"]
        
        # Normalize travelers - ensure required fields have defaults
        if "travelers" in normalized and normalized["travelers"]:
            normalized_travelers = []
            for traveler in normalized["travelers"]:
                if isinstance(traveler, dict):
                    # Ensure age is set (default to 35 if None)
                    if traveler.get("age") is None:
                        traveler["age"] = 35
                    # Ensure has_pre_existing_conditions is boolean
                    if traveler.get("has_pre_existing_conditions") is None:
                        traveler["has_pre_existing_conditions"] = False
                    normalized_travelers.append(traveler)
            normalized["travelers"] = normalized_travelers if normalized_travelers else [{"age": 35, "has_pre_existing_conditions": False}]
        elif "travelers" not in normalized or not normalized["travelers"]:
            # Default to one adult traveler
            normalized["travelers"] = [{"age": 35, "has_pre_existing_conditions": False}]
        
        return normalized
    
    def _generate_enhanced_answer(
        self,
        trip_details: Dict[str, Any],
        real_time_intelligence: Dict[str, Any],
        policy_recommendations: List[Dict[str, Any]],
        quotes: List[Dict[str, Any]] = None,
        show_full_intelligence: bool = True,
        taxonomy_products: List[str] = None,  # NEW: Taxonomy-based products
        taxonomy_recommendation: str = None  # NEW: Recommended product from taxonomy
    ) -> str:
        """
        Generate enhanced answer with Tavily real-time intelligence + TAXONOMY + pricing
        
        Args:
            trip_details: Extracted trip information
            real_time_intelligence: Tavily + claims data
            policy_recommendations: Matched policies
            quotes: Pricing information
            taxonomy_products: Eligible products from taxonomy (Product A, B, C)
            taxonomy_recommendation: Recommended product from taxonomy
            show_full_intelligence: If False, show concise version without all intelligence
        """
        
        if quotes is None:
            quotes = []
        
        parts = []
        
        # Part 1: Personalized greeting with trip context
        destination = trip_details.get("destination_country", "your destination")
        activities = trip_details.get("planned_activities", [])
        duration = trip_details.get("trip_duration_days", 0)
        travelers = trip_details.get("travelers", [])
        
        parts.append(f"## Your Trip to {destination}\n\n")
        
        trip_summary = []
        if duration:
            trip_summary.append(f"{duration}-day adventure")
        if activities and activities != ["general"]:
            trip_summary.append(f"with {', '.join(activities)}")
        if travelers:
            trip_summary.append(f"{len(travelers)} traveler(s)")
        
        if trip_summary:
            parts.append(" • ".join(trip_summary))
            parts.append("\n\n")
        
        # Extract intelligence data (used throughout)
        dest_intel = real_time_intelligence.get("destination", {})
        risks = real_time_intelligence.get("risks", {})
        medical = real_time_intelligence.get("medical_costs", {})
        claims_data = real_time_intelligence.get("historical_claims", {})
        
        # Part 2: Real-Time Intelligence (Only if show_full_intelligence is True)
        if show_full_intelligence:
            if (dest_intel and not dest_intel.get("error")) or (risks and not risks.get("error")) or (medical and not medical.get("error")) or (claims_data and not claims_data.get("error")):
                has_intelligence = True
                parts.append("### Travel Intelligence\n\n")
                
                # Historical Claims Data (MSIG) - Show FIRST for credibility (but concise)
                if claims_data and not claims_data.get("error"):
                    dest_profile = claims_data.get("destination_profile", {})
                    if dest_profile.get("total_claims", 0) > 0:
                        risk_level = dest_profile.get("risk_level", "unknown").upper()
                        parts.append(f"**Risk Level:** {risk_level}\n\n")
                
                # Skip detailed Tavily data - it's too much
                # Only show critical alerts if any
                if risks and not risks.get("error"):
                    key_risks = risks.get("key_risks", [])
                    if key_risks and len(key_risks) > 0:
                        parts.append(f"⚠️ **Important:** {key_risks[0]}\n\n")
        else:
            # Concise mode: Only show critical risk level
            if claims_data and not claims_data.get("error"):
                dest_profile = claims_data.get("destination_profile", {})
                if dest_profile.get("total_claims", 0) > 0:
                    risk_level = dest_profile.get("risk_level", "unknown").upper()
                    parts.append(f"**Risk Level:** {risk_level}\n\n")
        
        # Determine if we showed intelligence (for formatting)
        has_intelligence = show_full_intelligence or (
            real_time_intelligence.get("historical_claims", {}).get("destination_profile", {}).get("total_claims", 0) > 0
        )
        
        # Part 2.5: Generate proactive insights (DYNAMIC - handles ANY activity/destination!)
        proactive_insights = self.proactive_intelligence.generate_all_insights(
            trip_data=trip_details,
            claims_data=claims_data,
            realtime_data={
                "health_alerts": risks.get("health_alerts", []) if risks and not risks.get("error") else [],
                "travel_restrictions": dest_intel.get("travel_restrictions") if dest_intel and not dest_intel.get("error") else None,
                "weather_alerts": risks.get("weather_alerts") if risks and not risks.get("error") else None
            },
            policy_recommendations=policy_recommendations
        )
        
        # Display high-priority insights before policy recommendations
        if proactive_insights and show_full_intelligence:
            high_priority_insights = [i for i in proactive_insights if i.priority == "high"]
            if high_priority_insights:
                parts.append("\n")
                for insight in high_priority_insights[:3]:  # Max 3 high-priority alerts
                    parts.append(f"{insight.emoji} **{insight.message}**\n\n")
                parts.append("\n")
        
        # Part 3: TAXONOMY-BASED Recommendations (Priority)
        if taxonomy_products or taxonomy_recommendation:
            if has_intelligence or proactive_insights:
                parts.append("---\n\n")
            
            parts.append("### 🎯 Recommended Coverage (Based on Real Policy Data)\n\n")
            
            # Add friendly personality intro
            if activities and any(act in ["skiing", "diving", "hiking"] for act in activities):
                parts.append(f"Perfect! I found coverage ideal for your {', '.join(activities)} adventure: ✨\n\n")
            else:
                parts.append("Great news! Based on your trip details, here's what I recommend: ✨\n\n")
            
            # Show taxonomy recommendation
            if taxonomy_recommendation:
                parts.append(f"**Top Recommendation: {taxonomy_recommendation}**\n\n")
                
                # Find real pricing for this product (if available)
                real_price = None
                for quote in quotes:
                    if quote.get("product_key") == taxonomy_recommendation and quote.get("is_real_pricing"):
                        real_price = quote.get("premium")
                        break
                
                # Show price if available
                if real_price:
                    parts.append(f"**💰 Price: SGD ${real_price:,.2f}** (Real-time API pricing)\n\n")
                
                # Get detailed product info from taxonomy
                product_data = self.taxonomy_service.get_product_data(taxonomy_recommendation)
                benefits = product_data.get("layer_2_benefits", [])
                conditions = product_data.get("layer_1_conditions", [])
                
                parts.append(f"**Coverage Details:**\n")
                parts.append(f"- Total Benefits: {len(benefits)}\n")
                
                # Show key coverage amounts
                for benefit in benefits:
                    if benefit["benefit_name"] in ["overseas_medical_expenses", "trip_cancellation", "delayed_baggage", "personal_liability"]:
                        params = benefit.get("parameters", {})
                        coverage = params.get("coverage_limit")
                        if coverage and isinstance(coverage, (int, float)):
                            name = benefit["benefit_name"].replace("_", " ").title()
                            parts.append(f"- {name}: Up to ${coverage:,} SGD\n")
                
                # Show why it's recommended
                parts.append(f"\n**Why {taxonomy_recommendation}?**\n")
                for condition in conditions[:3]:  # Show top 3 reasons
                    if condition["condition"] == "age_eligibility":
                        params = condition.get("parameters", {})
                        if "min_age" in params:
                            parts.append(f"- Age range: {params.get('min_age')}-{params.get('max_age', 'N/A')} years\n")
                    elif condition["condition"] == "trip_start_singapore":
                        parts.append("- Covers trips starting from Singapore\n")
                
                parts.append("\n")
            
            # Show other eligible products with their pricing
            if taxonomy_products and len(taxonomy_products) > 1:
                other_products = [p for p in taxonomy_products if p != taxonomy_recommendation]
                if other_products:
                    parts.append(f"**Other Eligible Options:**\n\n")
                    for product in other_products:
                        # Find pricing
                        product_price = None
                        for quote in quotes:
                            if quote.get("product_key") == product and quote.get("is_real_pricing"):
                                product_price = quote.get("premium")
                                break
                        
                        if product_price:
                            parts.append(f"- **{product}**: SGD ${product_price:,.2f}\n")
                        else:
                            parts.append(f"- **{product}**: Quote available\n")
                    parts.append("\n")
        
        # Part 3.5: Database Policy recommendations (Fallback/Additional)
        elif policy_recommendations:
            if has_intelligence or proactive_insights:
                parts.append("---\n\n")
            
            parts.append("### Recommended Policies\n\n")
            
            # Add friendly personality intro
            if activities and any(act in ["skiing", "diving", "hiking"] for act in activities):
                parts.append(f"Perfect! I found coverage ideal for your {', '.join(activities)} adventure: ✨\n\n")
            else:
                parts.append("Great news! Here's what I recommend for your trip: ✨\n\n")
            
            for i, policy in enumerate(policy_recommendations[:2], 1):
                policy_name = policy.get('policy_name', 'Unknown Policy')
                policy_id = policy.get('policy_id', '')
                
                # Find matching quote for pricing
                policy_quote = None
                for quote in quotes:
                    if quote.get('policy_id') == policy_id:
                        policy_quote = quote
                        break
                
                # Add ranking
                if i == 1:
                    parts.append(f"**{i}. {policy_name}** (Best Match)\n\n")
                else:
                    parts.append(f"**{i}. {policy_name}** (Alternative Option)\n\n")
                
                # Show pricing if available
                if policy_quote:
                    premium = policy_quote.get('premium', 0)  # field is 'premium' not 'premium_sgd'
                    parts.append(f"**Price: SGD ${premium:,.2f}**\n\n")
                
                # Get benefit count and calculate total coverage
                benefits = policy.get('benefits', [])
                total_medical = 0
                total_accident = 0
                has_evacuation = False
                
                for benefit in benefits:
                    benefit_name = benefit.get('benefit_name', '').lower()
                    coverage = benefit.get('coverage_limit', 0) or 0
                    
                    if 'medical' in benefit_name and coverage > 0:
                        total_medical = max(total_medical, coverage)
                    if 'accident' in benefit_name or 'death' in benefit_name:
                        if coverage > 0:
                            total_accident = max(total_accident, coverage)
                    if 'evacuation' in benefit_name:
                        has_evacuation = True
                
                # Display coverage
                parts.append("Coverage Highlights:\n")
                if total_medical > 0:
                    parts.append(f"- Medical: Up to ${total_medical:,.0f} SGD\n")
                if total_accident > 0:
                    parts.append(f"- Accident: Up to ${total_accident:,.0f} SGD\n")
                if has_evacuation:
                    parts.append(f"- Emergency Evacuation: Covered\n")
                parts.append(f"- Total Benefits: {len(benefits)}\n\n")
                
                # Why this policy fits (intelligent matching)
                general_conditions = policy.get('general_conditions', {})
                parts.append("Why We Recommend This:\n")
                
                # Age match
                if general_conditions:
                    age_min = general_conditions.get('age_min', 0)
                    age_max = general_conditions.get('age_max', 100)
                    traveler_age = travelers[0].get('age') if travelers else None
                    if traveler_age:
                        parts.append(f"- Matches your age range ({age_min}-{age_max} years)\n")
                    
                    # Pre-existing conditions
                    if general_conditions.get('pre_existing_covered'):
                        parts.append(f"- Covers pre-existing medical conditions\n")
                
                # Activity-specific
                if activities:
                    for activity in activities:
                        if activity.lower() in ['hiking', 'skiing', 'diving', 'climbing']:
                            parts.append(f"- Suitable for {activity} activities\n")
                            break
                
                # Risk-based recommendation from Tavily
                if risks and not risks.get("error"):
                    risk_level = risks.get("overall_risk_level", "").lower()
                    if risk_level == "high" and total_medical >= 50000:
                        parts.append(f"- High medical coverage for elevated risk destination\n")
                
                # Claims-based recommendation (Historical Data)
                if claims_data and not claims_data.get("error"):
                    dest_profile = claims_data.get("destination_profile", {})
                    avg_claim = dest_profile.get("avg_claim_amount_sgd", 0)
                    
                    if avg_claim > 0:
                        # Compare policy coverage to historical average
                        if total_medical > avg_claim * 10:
                            parts.append(f"- Coverage exceeds 10x average claim for this destination\n")
                        elif total_medical > avg_claim * 5:
                            parts.append(f"- Strong coverage for typical claims (5x+ average)\n")
                        
                        # Recommendation from claims analysis
                        recommendation = claims_data.get("recommendation", {})
                        recommended_limit = recommendation.get("recommended_medical_limit_sgd", 0)
                        if recommended_limit > 0 and total_medical >= recommended_limit:
                            parts.append(f"- Meets recommended coverage based on claims history\n")
                
                parts.append("\n")
        else:
            parts.append("Unfortunately, I couldn't find policies matching your trip requirements.\n")
        
        # Part 4: Personalized call to action
        parts.append("---\n\n")
        parts.append("### Next Steps\n\n")
        parts.append("I can help you with:\n")
        parts.append("- Get detailed quotes with pricing\n")
        parts.append("- Compare specific benefits side-by-side\n")
        parts.append("- Answer questions about coverage\n")
        parts.append("- Start your purchase\n\n")
        parts.append("What would you like to do next?")
        
        return "".join(parts)
    
    def _format_comparison_answer(self, comparison: Dict[str, Any], pricing_info: Optional[Dict[str, float]] = None) -> str:
        """Format comparison result as readable answer with table and clear sections"""
        policies = comparison.get("policies", [])
        
        if not policies:
            return "No policies available for comparison."
        
        parts = []
        
        # Header with better spacing
        parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        parts.append(f"   POLICY COMPARISON: {len(policies)} Options\n")
        parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        
        # Add pricing section if available
        if pricing_info and len(pricing_info) > 0:
            parts.append("### Pricing\n\n")
            for policy_name, premium in pricing_info.items():
                parts.append(f"**{policy_name}:** SGD ${premium:,.2f}\n")
            parts.append("\n---\n\n")
        
        # Quick Summary Table
        parts.append("### Quick Comparison\n\n")
        parts.append("| Feature | " + " | ".join([p.get('policy_name', 'Unknown')[:20] for p in policies]) + " |\n")
        parts.append("|" + "---|" * (len(policies) + 1) + "\n")
        
        # Age Range
        age_ranges = []
        for policy in policies:
            gc = policy.get('general_conditions', {})
            age_min = gc.get('age_min', 'N/A')
            age_max = gc.get('age_max', 'N/A')
            age_ranges.append(f"{age_min}-{age_max} yrs" if age_min != 'N/A' else 'N/A')
        parts.append("| **Age Range** | " + " | ".join(age_ranges) + " |\n")
        
        # Trip Duration
        durations = []
        for policy in policies:
            gc = policy.get('general_conditions', {})
            max_days = gc.get('max_trip_duration_days', 'N/A')
            durations.append(f"Up to {max_days} days" if max_days != 'N/A' else 'N/A')
        parts.append("| **Trip Duration** | " + " | ".join(durations) + " |\n")
        
        # Medical Coverage
        medical_coverages = []
        for policy in policies:
            benefits = policy.get('benefits', [])
            medical_max = 0
            for b in benefits:
                if 'medical' in b.get('benefit_name', '').lower():
                    coverage = b.get('coverage_limit', 0) or 0
                    medical_max = max(medical_max, coverage)
            medical_coverages.append(f"${medical_max:,}" if medical_max > 0 else 'N/A')
        parts.append("| **Medical Coverage** | " + " | ".join(medical_coverages) + " |\n")
        
        # Pre-existing Conditions
        pre_existing = []
        for policy in policies:
            gc = policy.get('general_conditions', {})
            covered = "✅ Yes" if gc.get('pre_existing_covered') else "❌ No"
            pre_existing.append(covered)
        parts.append("| **Pre-existing Covered** | " + " | ".join(pre_existing) + " |\n")
        
        # Total Benefits
        benefit_counts = []
        for policy in policies:
            count = len(policy.get('benefits', []))
            benefit_counts.append(str(count))
        parts.append("| **Total Benefits** | " + " | ".join(benefit_counts) + " |\n")
        
        parts.append("\n")
        
        # Detailed Breakdown
        parts.append("### Detailed Breakdown\n\n")
        
        for i, policy in enumerate(policies, 1):
            policy_name = policy.get('policy_name', 'Unknown Policy')
            parts.append(f"#### {i}. {policy_name}\n\n")
            
            # General Conditions
            gc = policy.get('general_conditions', {})
            if gc:
                parts.append("**Eligibility:**\n")
                parts.append(f"- Age: {gc.get('age_min', 'N/A')}-{gc.get('age_max', 'N/A')} years\n")
                parts.append(f"- Max trip duration: {gc.get('max_trip_duration_days', 'N/A')} days\n")
                parts.append(f"- Pre-existing conditions: {'✅ Covered' if gc.get('pre_existing_covered') else '❌ Not covered'}\n")
                
                if gc.get('high_risk_activities_covered'):
                    parts.append(f"- High-risk activities: ✅ Covered\n")
                
                parts.append("\n")
            
            # Key Benefits
            benefits = policy.get('benefits', [])
            if benefits:
                parts.append("**Key Coverage:**\n")
                
                # Group benefits by category
                medical_benefits = []
                travel_benefits = []
                other_benefits = []
                
                for benefit in benefits:
                    b_name = benefit.get('benefit_name', '')
                    b_limit = benefit.get('coverage_limit', 0) or 0
                    
                    if any(keyword in b_name.lower() for keyword in ['medical', 'hospital', 'emergency', 'dental']):
                        if b_limit > 0:
                            medical_benefits.append(f"  - {b_name}: ${b_limit:,}")
                    elif any(keyword in b_name.lower() for keyword in ['cancel', 'delay', 'baggage', 'loss']):
                        if b_limit > 0:
                            travel_benefits.append(f"  - {b_name}: ${b_limit:,}")
                    elif b_limit > 0:
                        other_benefits.append(f"  - {b_name}: ${b_limit:,}")
                
                if medical_benefits:
                    parts.append("- **Medical & Emergency:**\n")
                    for b in medical_benefits[:5]:  # Show top 5
                        parts.append(b + "\n")
                    if len(medical_benefits) > 5:
                        parts.append(f"  - ...and {len(medical_benefits) - 5} more\n")
                
                if travel_benefits:
                    parts.append("- **Travel Protection:**\n")
                    for b in travel_benefits[:5]:  # Show top 5
                        parts.append(b + "\n")
                    if len(travel_benefits) > 5:
                        parts.append(f"  - ...and {len(travel_benefits) - 5} more\n")
                
                if other_benefits:
                    parts.append("- **Other Coverage:**\n")
                    for b in other_benefits[:3]:  # Show top 3
                        parts.append(b + "\n")
                    if len(other_benefits) > 3:
                        parts.append(f"  - ...and {len(other_benefits) - 3} more\n")
            
            parts.append("\n")
        
        # Recommendation
        parts.append("---\n\n")
        parts.append("### Our Recommendation\n\n")
        
        recommendation = comparison.get("recommendation")
        if recommendation:
            parts.append(f"{recommendation}\n\n")
        else:
            # Generate simple recommendation
            parts.append("**Choose based on your needs:**\n\n")
            for policy in policies:
                policy_name = policy.get('policy_name', 'Unknown')
                gc = policy.get('general_conditions', {})
                
                if gc.get('pre_existing_covered'):
                    parts.append(f"- **{policy_name}:** Best if you have pre-existing medical conditions\n")
                else:
                    benefits_count = len(policy.get('benefits', []))
                    if benefits_count > 30:
                        parts.append(f"- **{policy_name}:** Best for comprehensive coverage ({benefits_count} benefits)\n")
                    else:
                        parts.append(f"- **{policy_name}:** Best for basic coverage and budget-conscious travelers\n")
        
        parts.append("\nWould you like pricing for any of these policies?")
        
        return "".join(parts)
    
    def _extract_booking_reference(self, message: str) -> Optional[str]:
        """
        Extract booking reference from message
        Looks for patterns like: ABC123, SQ7X9K, etc.
        
        Returns:
            Booking reference or None
        """
        import re
        
        # Common patterns for booking references
        patterns = [
            r'\b([A-Z]{2,3}\d{3,6})\b',  # ABC123, SQ7X9K
            r'\b([A-Z]{6})\b',  # ABCDEF
            r'(?:booking|reference|ref|PNR)[:\s]+([A-Z0-9]{5,8})',  # "booking: ABC123"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _generate_smart_followup(self, missing_fields: List[str], trip_context: Any) -> str:
        """
        Generate intelligent follow-up question based on ACTUAL missing fields
        Natural and concise - no fake enthusiasm during data collection
        
        Args:
            missing_fields: List of missing critical fields
            trip_context: Current trip context state
            
        Returns:
            Smart follow-up question (concise and natural)
        """
        # SAFEGUARD: Log what we have to debug
        logger.info("generating_smart_followup",
                   missing=missing_fields,
                   has_destination=trip_context.destination_country,
                   has_duration=trip_context.trip_duration_days,
                   has_dates=f"{trip_context.departure_date}/{trip_context.return_date}",
                   num_travelers=len(trip_context.travelers) if trip_context.travelers else 0)
        
        # If we have destination and dates but missing traveler age
        if 'traveler_1_age' in missing_fields or ('travelers_count' in missing_fields and not trip_context.travelers):
            # Just ask age - no fluff
            return "How old are you both?"
        
        # If missing destination
        if 'destination_country' in missing_fields:
            return "Where are you traveling to?"
        
        # If missing dates
        if 'departure_date' in missing_fields:
            if trip_context.destination_country:
                return f"When are you going to {trip_context.destination_country}?"
            return "When are you traveling?"
        
        # SAFEGUARD: Double-check we don't already have duration before asking
        if 'return_date_or_duration' in missing_fields:
            if trip_context.trip_duration_days:
                # We have duration! Don't ask again - skip to next missing field
                logger.info("skip_duration_already_have", 
                           duration=trip_context.trip_duration_days,
                           still_missing=missing_fields)
                # Remove this from missing and ask for next thing
                remaining = [f for f in missing_fields if f != 'return_date_or_duration']
                if remaining:
                    # Still have other missing fields - ask for them
                    return self._generate_smart_followup(remaining, trip_context)
                else:
                    # Nothing critical missing - ready for quote
                    return f"Perfect! Let me find the best coverage for your {trip_context.trip_duration_days}-day {trip_context.destination_country} trip."
            
            if trip_context.destination_country:
                return f"How long will you be in {trip_context.destination_country}?"
            return "How long is your trip?"
        
        # If NO critical fields missing at all, we're ready!
        if not missing_fields:
            return f"Perfect! Let me find the best coverage for you."
        
        # Default fallback - should rarely hit this
        return "What else can you tell me about your trip?"

