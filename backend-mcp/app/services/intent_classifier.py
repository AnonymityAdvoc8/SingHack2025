"""
Intent Classification Service
Uses Groq LLM to intelligently detect user intent
Much more robust than keyword matching
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from groq import Groq
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IntentClassification:
    """Result of intent classification"""
    intent: str
    confidence: float
    reasoning: str
    sub_intent: Optional[str] = None


class IntentClassifier:
    """
    LLM-based intent classification
    Understands user intent better than keyword matching
    """
    
    def __init__(self):
        """Initialize with Groq client"""
        from app.config import get_settings
        self.settings = get_settings()
        api_key = self.settings.groq_api_key
        
        self.groq_client = Groq(api_key=api_key) if api_key else None
        self.use_llm = api_key is not None
        
        if self.use_llm:
            logger.info("llm_intent_classification_enabled", model=self.settings.groq_model)
        else:
            logger.warning("groq_api_key_missing", message="Falling back to keyword-based intent")
    
    def classify_intent(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        trip_context: Optional[Dict[str, Any]] = None
    ) -> IntentClassification:
        """
        Classify user intent using LLM
        
        Args:
            message: Current user message
            conversation_history: Previous conversation turns
            trip_context: Current trip information we have
            
        Returns:
            IntentClassification with intent and reasoning
        """
        if self.use_llm and self.groq_client:
            try:
                return self._classify_with_llm(message, conversation_history, trip_context)
            except Exception as e:
                logger.warning("llm_intent_classification_failed", error=str(e))
                # Fall back to keywords
        
        # Fallback to keyword-based
        return self._classify_with_keywords(message)
    
    def _classify_with_llm(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        trip_context: Optional[Dict] = None
    ) -> IntentClassification:
        """Use Groq LLM for intent classification"""
        
        # Build context for LLM
        context_info = []
        
        if conversation_history and len(conversation_history) > 0:
            last_bot_msg = next((m['content'] for m in reversed(conversation_history) if m.get('role') == 'assistant'), None)
            if last_bot_msg:
                context_info.append(f"Last bot message: {last_bot_msg[:150]}")
        
        if trip_context:
            has_destination = trip_context.get('destination_country')
            has_dates = trip_context.get('departure_date') or trip_context.get('trip_duration_days')
            has_ages = trip_context.get('travelers') and all(t.get('age') for t in trip_context.get('travelers', []))
            
            context_info.append(f"Trip info collected: Destination={bool(has_destination)}, Dates={bool(has_dates)}, Ages={bool(has_ages)}")
        
        context_str = "\n".join(context_info) if context_info else "No prior context"
        
        prompt = f"""You are analyzing user intent in a travel insurance conversation.

Context:
{context_str}

User Message: "{message}"

Classify the user's PRIMARY intent:

1. **recommendation_request** - User wants policy recommendations or is starting insurance process
   Examples: "I need insurance", "Which policy should I get?", "Recommend something"

2. **scan_email** - User wants to scan their email for booking details
   Examples: "Scan my email", "Check my gmail", "Find my bookings in email", "Look in my inbox", 
   "Connect to my gmail", "Fetch my trip details from gmail", "Can you connect to my email?", 
   "Get my bookings from email", "Pull my trip from gmail"

3. **trip_details** - User is providing information about their trip
   Examples: "Going to Japan", "For 2 weeks", "I'm 35 years old", "December 15-20"

4. **policy_question** - User asking about coverage, policies, or insurance concepts
   Examples: "What's covered?", "Explain pre-existing", "How much is deductible?", "Give me details on the policy"

5. **compare_policies** - User wants to compare specific policies
   Examples: "Compare these policies", "What's the difference between", "Which is better"

6. **general** - Casual conversation, greetings, or unclear intent
   Examples: "Thanks", "Hello", "Hmm", casual responses

**Rules:**
- ANY mention of "connect to gmail/email" OR "fetch from gmail/email" OR "scan gmail/email" → scan_email (HIGHEST PRIORITY!)
- "I need insurance" OR "help me find coverage" OR "assist me with insurance" → recommendation_request (starting process)
- "Can you provide details about the policy?" AFTER seeing recommendations → policy_question
- If user asks about specific coverage/benefits/terms → policy_question
- If last bot was asking for trip info AND user provides info → trip_details
- If last bot showed recommendations AND user asks "what's included?" → policy_question
- Providing trip information (ages, dates, duration) WITHOUT mentioning email → trip_details

CRITICAL: If user mentions "gmail", "email", "inbox", "connect", or "fetch" in context of getting trip details, 
it's ALWAYS scan_email, NOT trip_details or recommendation_request!

Respond in JSON:
{{
  "intent": "one of the 5 options above",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}}
"""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model=self.settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            import re
            
            # Handle markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            intent = result.get("intent", "general")
            confidence = float(result.get("confidence", 0.7))
            reasoning = result.get("reasoning", "")
            
            logger.info("llm_intent_classified",
                       intent=intent,
                       confidence=confidence,
                       reasoning=reasoning[:100])
            
            return IntentClassification(
                intent=intent,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error("llm_intent_classification_error", error=str(e))
            return self._classify_with_keywords(message)
    
    def _classify_with_keywords(self, message: str) -> IntentClassification:
        """Fallback keyword-based classification"""
        message_lower = message.lower()
        
        # Gmail/Email scan (HIGHEST PRIORITY - check first!)
        if any(word in message_lower for word in ["gmail", "email", "inbox", "scan my"]):
            if any(word in message_lower for word in ["connect", "fetch", "scan", "check", "get", "pull", "find"]):
                return IntentClassification(
                    intent="scan_email",
                    confidence=0.95,
                    reasoning="keyword: gmail/email scan request"
                )
        
        # Policy questions
        if any(word in message_lower for word in ["what", "why", "how", "explain", "details", "provide", "tell me"]):
            if any(word in message_lower for word in ["policy", "cover", "benefit", "claim", "deductible"]):
                return IntentClassification(
                    intent="policy_question",
                    confidence=0.8,
                    reasoning="keyword: question about policy"
                )
        
        # Recommendation
        if any(phrase in message_lower for phrase in ["need insurance", "want insurance", "recommend", "which policy"]):
            return IntentClassification(
                intent="recommendation_request",
                confidence=0.9,
                reasoning="keyword: insurance request"
            )
        
        # Compare
        if any(word in message_lower for word in ["compare", "difference", "versus", "vs"]):
            return IntentClassification(
                intent="compare_policies",
                confidence=0.85,
                reasoning="keyword: comparison"
            )
        
        # Default: trip details or general
        return IntentClassification(
            intent="trip_details",
            confidence=0.6,
            reasoning="keyword: fallback to trip details"
        )

