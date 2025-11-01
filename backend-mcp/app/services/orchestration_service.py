"""
TravelMate AI - Conversation Orchestration Service
Orchestrates multiple MCP tools to handle complex conversational flows
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session
from app.utils.logger import get_logger

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
        
        self.db = db
        self.tools = MCPTools(db)
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Initialize claims analytics
        try:
            claims_db = get_claims_db()
            claims_session = claims_db.get_session()
            self.claims_analytics = ClaimsAnalyticsService(claims_session)
        except Exception as e:
            logger.warning("claims_analytics_initialization_failed", error=str(e))
            self.claims_analytics = None
    
    def handle_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method - handles any user message intelligently
        
        Args:
            message: User's conversational message
            session_id: Optional session identifier
            context: Optional conversation context (includes conversation_history from OpenAI format)
            
        Returns:
            Comprehensive response with answer and metadata
        """
        logger.info("orchestrator_message_received", message_length=len(message), session_id=session_id)
        
        # Load conversation history from context if provided (for OpenAI compatibility)
        if context and "conversation_history" in context:
            self.conversation_history = context["conversation_history"]
            logger.info("orchestrator_loaded_history", history_length=len(self.conversation_history))
        else:
            # Reset for new conversation
            self.conversation_history = []
        
        # Step 1: Detect intent (use conversation history for better context)
        intent = self._detect_intent(message, self.conversation_history)
        logger.info("orchestrator_intent_detected", intent=intent)
        
        # Step 2: Route to appropriate flow
        if intent == "recommendation_request":
            return self._handle_recommendation_flow(message, context)
        
        elif intent == "trip_details":
            return self._handle_trip_details_flow(message, context)
        
        elif intent == "policy_question":
            return self._handle_policy_question_flow(message, context)
        
        elif intent == "compare_policies":
            return self._handle_comparison_flow(message, context)
        
        else:
            # Default: conversational extraction + general response
            return self._handle_general_flow(message, context)
    
    def _handle_recommendation_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
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
            "follow_up_questions": []
        }
        
        # Step 1: Extract trip details from conversation (Phase 3)
        logger.info("orchestrator_extracting_trip_details")
        
        # Build extraction context that includes:
        # 1. Previously extracted trip details (for incremental extraction)
        # 2. Conversation history (for understanding context)
        extraction_context = {}
        
        if context:
            # Get previously extracted trip details (if any)
            extraction_context = context.get("extracted_trip_details", {})
            
            # Add conversation history to help LLM understand context
            if "conversation_history" in context:
                extraction_context["conversation_history"] = context["conversation_history"]
        
        extraction = self.tools.extract_trip_from_conversation(message, extraction_context)
        
        response["trip_details"] = extraction.get("extracted", {})
        response["extraction_complete"] = extraction.get("is_complete", False)
        
        # If not complete, ask follow-up question
        if not extraction["is_complete"]:
            response["answer"] = extraction.get("follow_up_question", "Could you provide more details about your trip?")
            response["follow_up_questions"].append(extraction.get("follow_up_question"))
            
            # Update conversation history with current exchange
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response["answer"]})
            
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
        response["answer"] = self._generate_enhanced_answer(
            response["trip_details"],
            response["real_time_intelligence"],
            response["policy_recommendations"],
            response.get("quotes", [])
        )
        
        logger.info("orchestrator_recommendation_flow_complete")
        
        # Update conversation history with current exchange
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response["answer"]})
        
        # Store context for next turn
        response["context"] = {
            "conversation_history": self.conversation_history,
            "extracted_trip_details": response["trip_details"]
        }
        
        return response
    
    def _handle_trip_details_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle trip details extraction without recommendation"""
        logger.info("orchestrator_trip_details_flow")
        
        extraction = self.tools.extract_trip_from_conversation(message, context)
        
        return {
            "intent": "trip_details",
            "answer": extraction.get("follow_up_question", "Got it! What else would you like to know?"),
            "trip_details": extraction.get("extracted", {}),
            "is_complete": extraction.get("is_complete", False)
        }
    
    def _handle_policy_question_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle policy-specific questions"""
        logger.info("orchestrator_policy_question_flow")
        
        qa_result = self.tools.answer_policy_question(
            question=message,
            include_citations=True
        )
        
        return {
            "intent": "policy_question",
            "answer": qa_result.get("answer", "I couldn't find specific information about that."),
            "confidence": qa_result.get("confidence_score", 0),
            "citations": qa_result.get("citations", [])
        }
    
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
        
        return {
            "intent": "compare_policies",
            "answer": self._format_comparison_answer(comparison),
            "comparison": comparison
        }
    
    def _handle_general_flow(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle general conversational messages"""
        logger.info("orchestrator_general_flow")
        
        # Try to extract trip details for context building
        extraction = self.tools.extract_trip_from_conversation(message, context)
        
        return {
            "intent": "general",
            "answer": extraction.get("follow_up_question", "I'm here to help you find the perfect travel insurance. What would you like to know?"),
            "trip_details": extraction.get("extracted", {}),
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
        
        # If we have conversation history, check for contextual continuations
        # (e.g., "tell me more", "what about activities?", "yes")
        if conversation_history and len(conversation_history) > 0:
            last_assistant_msg = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg.get("content", "").lower()
                    break
            
            # Check if the last assistant response included policy recommendations
            # (indicates we already completed recommendation flow)
            if last_assistant_msg:
                has_policy_recommendations = any(
                    keyword in last_assistant_msg 
                    for keyword in ["scootsurance", "traveleasy", "recommended policies", "price:", "sgd $", "coverage highlights"]
                )
                
                # If user is asking follow-up questions about the recommended policies
                # Route to policy Q&A instead of re-running recommendation
                if has_policy_recommendations:
                    followup_question_patterns = [
                        "more details", "tell me more", "more info", "explain", "what does",
                        "how does", "what is", "what's", "details on", "about the policy",
                        "about this", "about that", "coverage", "benefits", "what are",
                        "can you explain", "what happens if", "does it cover"
                    ]
                    if any(pattern in message_lower for pattern in followup_question_patterns):
                        logger.info("intent_followup_question", previous_context="policy_recommendations")
                        return "policy_question"  # Route to Q&A about policies
            
            # If last assistant message was asking for trip details,
            # treat ANY user response as a continuation of recommendation flow
            if last_assistant_msg:
                trip_asking_keywords = ["where", "when", "how long", "how many", "destination", "travel", "trip", "old", "age"]
                if any(keyword in last_assistant_msg for keyword in trip_asking_keywords):
                    logger.info("intent_contextual_continuation", previous_context="recommendation_request")
                    return "recommendation_request"  # Continue the recommendation flow
            
            # Contextual continuation patterns (explicit confirmations)
            continuation_patterns = ["continue", "go on", "next"]
            if any(pattern in message_lower for pattern in continuation_patterns):
                # If last message was asking for trip details, continue that flow
                if last_assistant_msg and any(keyword in last_assistant_msg for keyword in ["trip", "travel", "destination", "when", "how many"]):
                    logger.info("intent_contextual_continuation", previous_context="trip_details")
                    return "recommendation_request"
        
        # Recommendation request indicators (CHECK FIRST - highest priority)
        recommendation_keywords = [
            "recommend", "suggest", "which policy", "best insurance",
            "which insurance", "what should i", "help me choose",
            "policy would you", "policy should i", "policy do you recommend",
            "what insurance", "need insurance", "get insurance"
        ]
        if any(keyword in message_lower for keyword in recommendation_keywords):
            return "recommendation_request"
        
        # Comparison indicators
        comparison_keywords = ["compare", "difference between", "versus", "vs"]
        if any(keyword in message_lower for keyword in comparison_keywords):
            return "compare_policies"
        
        # Policy question indicators
        question_keywords = [
            "what is", "what does", "how does", "tell me about",
            "explain", "does it cover", "is covered", "what's covered"
        ]
        if any(keyword in message_lower for keyword in question_keywords):
            return "policy_question"
        
        # Trip details indicators (lower priority - only if no recommendation request)
        trip_keywords = [
            "travelling to", "going to", "planning a trip", "visiting",
            "i'm going", "i will be", "trip to"
        ]
        if any(keyword in message_lower for keyword in trip_keywords):
            # If they mention trip details, default to recommendation
            # (people usually share trip details because they want a recommendation)
            return "recommendation_request"
        
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
        quotes: List[Dict[str, Any]] = None
    ) -> str:
        """Generate enhanced answer with Tavily real-time intelligence + pricing"""
        
        if quotes is None:
            quotes = []
        
        parts = []
        
        # Part 1: Personalized greeting with trip context
        destination = trip_details.get("destination_country", "your destination")
        activities = trip_details.get("planned_activities", [])
        duration = trip_details.get("trip_duration_days", 0)
        travelers = trip_details.get("travelers", [])
        
        parts.append(f"**Your Trip to {destination}**\n\n")
        
        trip_summary = []
        if duration:
            trip_summary.append(f"{duration}-day adventure")
        if activities:
            trip_summary.append(f"with {', '.join(activities)}")
        if travelers:
            trip_summary.append(f"{len(travelers)} traveler(s)")
        
        if trip_summary:
            parts.append(" • ".join(trip_summary))
            parts.append("\n\n")
        
        # Part 2: Real-Time Intelligence (Tavily + Historical Claims)
        has_intelligence = False
        dest_intel = real_time_intelligence.get("destination", {})
        risks = real_time_intelligence.get("risks", {})
        medical = real_time_intelligence.get("medical_costs", {})
        claims_data = real_time_intelligence.get("historical_claims", {})
        
        if (dest_intel and not dest_intel.get("error")) or (risks and not risks.get("error")) or (medical and not medical.get("error")) or (claims_data and not claims_data.get("error")):
            has_intelligence = True
            parts.append("**Travel Intelligence**\n\n")
            
            # Historical Claims Data (MSIG) - Show FIRST for credibility
            if claims_data and not claims_data.get("error"):
                dest_profile = claims_data.get("destination_profile", {})
                if dest_profile.get("total_claims", 0) > 0:
                    total_claims = dest_profile.get("total_claims", 0)
                    avg_claim = dest_profile.get("avg_claim_amount_sgd", 0)
                    risk_level = dest_profile.get("risk_level", "unknown").upper()
                    
                    parts.append(f"Historical Claims Data (Based on {total_claims:,} MSIG claims):\n")
                    parts.append(f"- Average Claim: SGD ${avg_claim:,.0f}\n")
                    parts.append(f"- Risk Level: {risk_level}\n")
                    
                    # Show top claim types
                    top_claims = dest_profile.get("top_claim_types", [])
                    if top_claims:
                        parts.append(f"- Most Common: {top_claims[0]['type']} ({top_claims[0]['percentage']}%)\n")
                    
                    parts.append("\n")
            
            # Destination insights
            if dest_intel and not dest_intel.get("error"):
                answer_text = dest_intel.get("answer", "")
                if answer_text:
                    # Extract first meaningful sentence
                    first_sentence = answer_text.split('.')[0] if '.' in answer_text else answer_text[:150]
                    parts.append(f"Current Situation: {first_sentence}.\n\n")
                
                findings = dest_intel.get("key_findings", [])
                if findings:
                    parts.append("Important Travel Requirements:\n")
                    for finding in findings[:3]:
                        parts.append(f"- {finding}\n")
                    parts.append("\n")
            
            # Risk analysis
            if risks and not risks.get("error"):
                risk_level = risks.get("overall_risk_level", "moderate").upper()
                parts.append(f"Risk Level: {risk_level}\n\n")
                
                key_risks = risks.get("key_risks", [])
                if key_risks:
                    parts.append("Things to Be Aware Of:\n")
                    for risk in key_risks[:3]:
                        parts.append(f"- {risk}\n")
                    parts.append("\n")
                
                recommendations = risks.get("recommendations", [])
                if recommendations:
                    parts.append("Our Recommendation:\n")
                    for rec in recommendations[:2]:
                        parts.append(f"- {rec}\n")
                    parts.append("\n")
            
            # Medical cost intelligence
            if medical and not medical.get("error"):
                cost_summary = medical.get("cost_summary", "")
                if cost_summary:
                    # Extract key insight
                    parts.append(f"Healthcare Insight: {cost_summary[:150]}...\n\n")
                
                coverage_recs = medical.get("coverage_recommendations", [])
                if coverage_recs:
                    for rec in coverage_recs[:1]:
                        parts.append(f"Note: {rec}\n\n")
        
        # Part 3: Policy recommendations with intelligent matching
        if policy_recommendations:
            if has_intelligence:
                parts.append("---\n\n")
            
            parts.append("**Recommended Policies**\n\n")
            parts.append("Based on your trip details and current travel conditions:\n\n")
            
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
        parts.append("**Next Steps**\n\n")
        parts.append("I can help you with:\n")
        parts.append("- Get detailed quotes with pricing\n")
        parts.append("- Compare specific benefits side-by-side\n")
        parts.append("- Answer questions about coverage\n")
        parts.append("- Start your purchase\n\n")
        parts.append("What would you like to do next?")
        
        return "".join(parts)
    
    def _format_comparison_answer(self, comparison: Dict[str, Any]) -> str:
        """Format comparison result as readable answer"""
        policies = comparison.get("policies", [])
        
        if not policies:
            return "No policies available for comparison."
        
        parts = [f"Here's a comparison of {len(policies)} insurance policies:\n\n"]
        
        for policy in policies:
            parts.append(f"**{policy.get('policy_name')}:**\n")
            
            # Format coverage with proper number formatting
            max_coverage = policy.get('max_coverage', 'N/A')
            if isinstance(max_coverage, (int, float)):
                parts.append(f"- Coverage: ${max_coverage:,}\n")
            else:
                parts.append(f"- Coverage: {max_coverage}\n")
            
            parts.append(f"- Benefits: {len(policy.get('benefits', []))} covered\n\n")
        
        recommendation = comparison.get("recommendation")
        if recommendation:
            parts.append(f"\n💡 **Recommendation:** {recommendation}")
        
        return "".join(parts)

