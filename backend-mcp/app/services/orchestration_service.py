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
        from app.services.claims_analytics_service import ClaimsAnalyticsService
        from app.claims.claims_db import get_claims_db
        from app.services.emotional_intelligence_service import EmotionalIntelligenceService
        from app.services.proactive_intelligence_service import ProactiveIntelligenceService
        from app.services.trip_context import TripContext
        from app.services.trip_discovery_agent import TripDiscoveryAgent
        from app.services.gmail_agent import GmailAgent
        from app.services.flight_api_agent import FlightAPIAgent
        from app.services.intent_classifier import IntentClassifier
        from app.services.conversational_response_generator import ConversationalResponseGenerator
        
        self.db = db
        self.tools = MCPTools(db)
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
        
        # Initialize AI services
        self.intent_classifier = IntentClassifier()  # LLM-based intent
        self.emotional_intelligence = EmotionalIntelligenceService()  # LLM-based emotion
        self.proactive_intelligence = ProactiveIntelligenceService()
        self.response_generator = ConversationalResponseGenerator()  # NEW: LLM-generated responses!
    
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
                    
                    # Auto-proceed to generate quote
                    logger.info("gmail_booking_selected_auto_quote")
                    return await self._handle_recommendation_flow(message, context, emotional_context)
                else:
                    # Invalid number
                    return {
                        "intent": "scan_email",
                        "answer": f"Please select a number between 1 and {len(scan_results)}.",
                        "bookings": scan_results
                    }
            else:
                # Not a number - show scan results again
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
        
        # Step 1.5: Detect emotional context for empathetic responses
        emotional_context = self.emotional_intelligence.detect_emotion(message, self.conversation_history)
        logger.info("orchestrator_emotion_detected", 
                   emotion=emotional_context.state,
                   confidence=emotional_context.confidence)
        
        response = {}
        # Step 2: Route to appropriate flow (pass emotional_context for natural responses)
        if intent == "recommendation_request":
            response = self._handle_recommendation_flow(message, context, emotional_context)
        
        elif intent == "scan_email":
            response = await self._handle_email_scan_flow(message, context, session_id)
        
        elif intent == "trip_details":
            response = self._handle_trip_details_flow(message, context, emotional_context)
        
        elif intent == "policy_question":
            response = self._handle_policy_question_flow(message, context)
        
        elif intent == "compare_policies":
            response = self._handle_comparison_flow(message, context)
        
        else:
            # Default: conversational extraction + general response
            response = self._handle_general_flow(message, context, emotional_context)
        
        # Step 3: Adapt response based on emotional intelligence
        # SKIP for data collection - LLM already generates contextual responses
        if response.get("answer"):
            original_answer = response["answer"]
            
            # Determine context type
            is_collecting_data = not response.get("extraction_complete", True)
            is_policy_question = response.get("intent") == "policy_question"
            is_recommendation = "recommend" in original_answer.lower() or "policy" in original_answer.lower()
            
            if is_collecting_data:
                # SKIP emotional adaptation - LLM response generator already handles it
                # This prevents adding extra fluff on top of already-good LLM responses
                logger.info("skipping_emotional_adaptation_for_data_collection", 
                           emotion=emotional_context.state)
                response["emotional_context"] = {
                    "detected_emotion": emotional_context.state,
                    "confidence": emotional_context.confidence
                }
            elif is_policy_question or is_recommendation:
                # Only adapt for policy Q&A and recommendations (not data collection)
                context_type = "policy_question" if is_policy_question else "recommendation"
                
                adapted_answer = self.emotional_intelligence.adapt_response(
                    original_answer, 
                    emotional_context,
                    context_type=context_type
                )
                response["answer"] = adapted_answer
                response["emotional_context"] = {
                    "detected_emotion": emotional_context.state,
                    "confidence": emotional_context.confidence
                }
                logger.info("orchestrator_response_adapted", 
                           emotion=emotional_context.state,
                           context_type=context_type,
                           original_length=len(original_answer),
                           adapted_length=len(adapted_answer))

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
                gmail_scan_results=gmail_scan_results  # NEW: Persist scan results
            )
            logger.info("session_saved_to_storage", 
                       session_id=session_id, 
                       history_length=len(self.conversation_history),
                       trip_completeness=f"{self.trip_context.calculate_completeness():.0%}",
                       has_gmail_results=bool(gmail_scan_results))
        
        return response
    
    def _handle_recommendation_flow(
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
        is_initial_request = any(phrase in message.lower() for phrase in ["need insurance", "want insurance", "buy insurance", "looking for insurance"])
        has_minimal_data = self.trip_context.calculate_completeness() < 0.3
        
        if is_initial_request and has_minimal_data:
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
            
            # Use passed emotional_context or detect if not provided
            if not emotional_context:
                emotional_context = self.emotional_intelligence.detect_emotion(last_user_message, self.conversation_history)
            
            # Generate natural, contextual follow-up using LLM
            follow_up = self.response_generator.generate_followup_question(
                user_message=last_user_message,
                emotion=emotional_context.state,
                missing_fields=missing_critical,
                trip_context=self.trip_context.to_dict(),
                conversation_history=self.conversation_history
            )
            
            # Add proactive insights based on partial data
            proactive_insights = self.proactive_intelligence.generate_insights(
                trip_data=response["trip_details"],
                claims_data=None,  # Don't have full claims data yet
                tavily_data=None,
                policy_recommendations=None
            )
            
            # Add high-priority insights to follow-up question
            if proactive_insights:
                high_priority = [i for i in proactive_insights if i.priority == "high"]
                if high_priority:
                    insight_text = "\n\n".join([f"{i.emoji} **{i.message}**" for i in high_priority[:2]])
                    follow_up = f"{insight_text}\n\n{follow_up}"
            
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
        
        # Step 3: Check eligibility for all policies
        logger.info("orchestrator_checking_eligibility")
        
        # Normalize trip details before validation
        normalized_trip_details = self._normalize_trip_details(response["trip_details"])
        
        eligibility_results = self.tools.check_eligibility(
            trip_details=normalized_trip_details
        )
        
        eligible_policies = [
            e["policy_id"] for e in eligibility_results if e.get("is_eligible", False)
        ]
        
        logger.info("orchestrator_eligible_policies_found", count=len(eligible_policies))
        
        # Step 4: Compare eligible policies with real-time context
        if eligible_policies:
            logger.info("orchestrator_comparing_policies", policy_count=len(eligible_policies))
            
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
            
            # Step 5: Generate actual quotes with pricing 💰
            logger.info("orchestrator_generating_quotes", policy_count=len(eligible_policies))
            
            try:
                quote_result = self.tools.get_quote(
                    trip_details=normalized_trip_details,
                    policy_ids=eligible_policies
                )
                
                response["quotes"] = quote_result.get("quotes", [])
                response["total_premium"] = quote_result.get("total_premium", 0)
                
                logger.info(
                    "orchestrator_quotes_generated",
                    quote_count=len(response["quotes"]),
                    total_premium=response["total_premium"]
                )
            except Exception as e:
                logger.error("orchestrator_quote_generation_failed", error=str(e))
                response["quotes"] = []
        
        # Step 6: Generate enhanced answer with Tavily insights + pricing
        # Determine if this is first-time recommendation (show full) or follow-up (show concise)
        is_first_recommendation = not any(
            indicator in str(self.conversation_history).lower()
            for indicator in ["scootsurance", "traveleasy", "recommended policies", "sgd $"]
        )
        
        response["answer"] = self._generate_enhanced_answer(
            response["trip_details"],
            response["real_time_intelligence"],
            response["policy_recommendations"],
            response.get("quotes", []),
            show_full_intelligence=is_first_recommendation  # Only show full intelligence on first recommendation
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
        auth_url = self.gmail_agent.get_authorization_url(session_id or "no_session")
        
        return {
            "intent": "scan_email",
            "answer": f"""To scan your Gmail, I need your permission to access your inbox. 🔒

I'll only look for booking confirmations (flights, hotels) and won't access any other emails.

Click the button below to authorize Gmail access:""",
            "suggested_actions": [
                {"type": "authorize_gmail", "label": "🔐 Connect Gmail", "icon": "📧", "data": auth_url}
            ],
            "agent_activities": [
                {"agent": "gmail", "status": "waiting_for_auth"}
            ]
        }
    
    def _handle_trip_details_flow(
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
            
            # Use passed emotional_context or detect if not provided
            if not emotional_context:
                emotional_context = self.emotional_intelligence.detect_emotion(message, self.conversation_history)
            
            # Generate LLM-based natural follow-up
            answer = self.response_generator.generate_followup_question(
                user_message=message,
                emotion=emotional_context.state,
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
            return self._handle_recommendation_flow(message, context)
    
    def _handle_policy_question_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle policy-specific questions"""
        logger.info("orchestrator_policy_question_flow")
        
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
        
        if not policy_ids:
            # Default to comparing all policies
            policy_ids = None
        
        comparison = self.tools.compare_policies(
            policy_ids=policy_ids,
            user_context=context
        )
        
        # Try to extract pricing from conversation history to include in comparison
        pricing_info = self._extract_pricing_from_history()
        
        return {
            "intent": "compare_policies",
            "answer": self._format_comparison_answer(comparison, pricing_info),
            "comparison": comparison,
            "pricing": pricing_info
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
        show_full_intelligence: bool = True
    ) -> str:
        """
        Generate enhanced answer with Tavily real-time intelligence + pricing
        
        Args:
            trip_details: Extracted trip information
            real_time_intelligence: Tavily + claims data
            policy_recommendations: Matched policies
            quotes: Pricing information
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
        
        # Part 2.5: Generate proactive insights (NEW!)
        proactive_insights = self.proactive_intelligence.generate_insights(
            trip_data=trip_details,
            claims_data=claims_data,
            tavily_data={
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
        
        # Part 3: Policy recommendations with intelligent matching
        if policy_recommendations:
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

