"""
Dynamic Personality Service
Uses LLM to generate contextual, personalized responses for ANY situation
No hardcoded if-statements - fully adaptive to any country, emotion, or context
"""

from typing import Dict, Any, Optional
from groq import Groq
from app.config import get_settings
from app.utils.logger import get_logger
import json

settings = get_settings()
logger = get_logger(__name__)


class DynamicPersonalityService:
    """
    LLM-powered personality system that adapts to ANY context dynamically
    No hardcoded responses - generates fresh, contextual responses every time
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        
        # Core personality traits (the ONLY hardcoded part - defines WHO we are)
        self.core_personality = """
You are TravelMate, a warm, knowledgeable travel insurance advisor.

CORE TRAITS:
- Friendly like a helpful friend, not a salesperson
- Enthusiastic about travel and genuinely excited for users
- Empathetic and emotionally intelligent
- Proactive with data-driven insights
- Clear, jargon-free, and transparent
- Uses appropriate emojis (✈️ 🏥 💡 ⚠️) sparingly for warmth

APPROACH:
1. Acknowledge emotions FIRST (empathy before data)
2. Provide data-driven recommendations with reasoning
3. Always explain "why" (transparency builds trust)
4. End with helpful questions to guide conversation
5. Celebrate user decisions

TONE: Professional yet warm, like a knowledgeable friend who genuinely cares.
"""
    
    def generate_contextual_response(
        self,
        message: str,
        response_type: str,
        context: Dict[str, Any],
        emotional_state: Optional[str] = None,
        detected_concerns: Optional[list] = None
    ) -> str:
        """
        Generate a fully contextualized response using LLM
        No templates - adapts to ANY situation dynamically
        
        Args:
            message: User's original message
            response_type: Type of response (greeting, acknowledgment, insight, etc.)
            context: Full context including trip data, conversation history, etc.
            emotional_state: Detected emotion (stressed, excited, worried, etc.)
            detected_concerns: List of user concerns detected
            
        Returns:
            Contextually-appropriate response
        """
        try:
            prompt = self._build_response_prompt(
                message, response_type, context, emotional_state, detected_concerns
            )
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": self.core_personality
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Higher for creative, warm responses
                max_tokens=500
            )
            
            generated = response.choices[0].message.content.strip()
            
            logger.info("personality_response_generated", 
                       response_type=response_type,
                       emotional_state=emotional_state,
                       length=len(generated))
            
            return generated
            
        except Exception as e:
            logger.error("personality_generation_failed", error=str(e))
            # Fallback to simple response
            return self._fallback_response(response_type, context)
    
    def generate_activity_insight(
        self,
        activities: list,
        destination: str,
        claims_data: Optional[Dict] = None
    ) -> str:
        """
        Generate activity-specific insights dynamically using LLM
        Works for ANY activity, not just pre-programmed ones
        
        Args:
            activities: List of planned activities
            destination: Destination country
            claims_data: Historical claims data if available
            
        Returns:
            Personalized activity insight
        """
        try:
            activities_str = ", ".join(activities)
            claims_context = ""
            
            if claims_data and claims_data.get("activity_claims"):
                claims_context = f"\n\nHistorical Data: {json.dumps(claims_data['activity_claims'], indent=2)}"
            
            prompt = f"""Generate a helpful, friendly insight about these activities for a traveler.

ACTIVITIES: {activities_str}
DESTINATION: {destination}{claims_context}

Generate a short (2-3 sentences) proactive insight that:
1. Identifies key risks or considerations for these activities
2. Ties to insurance coverage importance
3. Includes relevant data if available
4. Feels warm and helpful, not scary
5. Starts with an appropriate emoji

Focus on being genuinely helpful, not salesy. Use specific details about the activities.

Example good output:
"⛷️ Quick heads up: Skiing at high altitudes can increase injury risk, especially for beginners. Equipment rental protection is worth considering - historical data shows 68% of skiing claims involve gear damage or loss!"

Your insight:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": self.core_personality},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("activity_insight_generation_failed", error=str(e))
            return f"💡 Great choice with {', '.join(activities)}! I'll make sure your coverage includes these activities."
    
    def generate_destination_insight(
        self,
        destination: str,
        travel_dates: Optional[str] = None,
        claims_data: Optional[Dict] = None,
        realtime_data: Optional[Dict] = None
    ) -> str:
        """
        Generate destination-specific insights dynamically
        Works for ANY country, not just pre-programmed ones
        
        Args:
            destination: Destination country/city
            travel_dates: Travel date range
            claims_data: Historical claims statistics
            realtime_data: Current travel advisories, weather, etc.
            
        Returns:
            Personalized destination insight
        """
        try:
            context_parts = [f"DESTINATION: {destination}"]
            
            if travel_dates:
                context_parts.append(f"TRAVEL DATES: {travel_dates}")
            
            if claims_data:
                context_parts.append(f"\nHISTORICAL CLAIMS DATA:\n{json.dumps(claims_data, indent=2)}")
            
            if realtime_data:
                context_parts.append(f"\nCURRENT ADVISORIES:\n{json.dumps(realtime_data, indent=2)}")
            
            context_str = "\n".join(context_parts)
            
            prompt = f"""Generate a helpful destination-specific insight for a traveler.

{context_str}

Generate a short (2-3 sentences) proactive insight that:
1. Highlights important considerations for this destination
2. Uses real data if provided (claims stats, current advisories)
3. Connects to insurance importance naturally
4. Feels warm and informative, not alarmist
5. Starts with an appropriate emoji (country flag or relevant icon)

Be specific to THIS destination - no generic advice.

Your insight:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": self.core_personality},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=250
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("destination_insight_generation_failed", error=str(e))
            return f"✈️ {destination} is a wonderful destination! Let me find the right coverage for your trip."
    
    def adapt_tone_for_emotion(
        self,
        original_response: str,
        emotional_state: str,
        user_message: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Dynamically adapt response tone based on detected emotion
        Works for ANY emotional state, not just pre-defined ones
        
        Args:
            original_response: The factual response to adapt
            emotional_state: Detected emotion (any string description)
            user_message: User's original message
            context: Full conversation context
            
        Returns:
            Emotionally-adapted response
        """
        try:
            prompt = f"""Adapt this response to match the user's emotional state.

USER MESSAGE: "{user_message}"
DETECTED EMOTION: {emotional_state}

ORIGINAL RESPONSE:
{original_response}

Your task:
1. Keep ALL factual information intact
2. Adjust tone and framing to match the user's emotional state
3. Add empathetic opening if appropriate
4. Simplify jargon if user seems confused/stressed
5. Add reassurance if user seems worried
6. Match enthusiasm if user is excited
7. Add transparency if user seems skeptical

Return ONLY the adapted response, no meta-commentary.

Adapted response:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": self.core_personality},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            adapted = response.choices[0].message.content.strip()
            
            logger.info("tone_adapted_for_emotion",
                       emotion=emotional_state,
                       original_length=len(original_response),
                       adapted_length=len(adapted))
            
            return adapted
            
        except Exception as e:
            logger.error("tone_adaptation_failed", error=str(e))
            # Return original if adaptation fails
            return original_response
    
    def generate_followup_question(
        self,
        missing_fields: list,
        current_context: Dict[str, Any],
        emotional_state: Optional[str] = None,
        conversation_flow: Optional[str] = None
    ) -> str:
        """
        Generate contextual follow-up question dynamically
        Adapts to conversation flow and emotional state
        
        Args:
            missing_fields: List of missing field names
            current_context: What we know so far
            emotional_state: User's current emotional state
            conversation_flow: Description of conversation progress
            
        Returns:
            Natural, contextual follow-up question
        """
        try:
            context_summary = json.dumps({
                k: v for k, v in current_context.items()
                if k not in ['conversation_history', 'gmail_scan_results']
            }, indent=2)
            
            prompt = f"""Generate a natural follow-up question to collect missing trip information.

CURRENT CONTEXT:
{context_summary}

MISSING FIELDS: {', '.join(missing_fields)}
USER EMOTIONAL STATE: {emotional_state or 'neutral'}
CONVERSATION FLOW: {conversation_flow or 'early in conversation'}

Generate ONE follow-up question that:
1. Asks for the most important missing field
2. Feels natural and conversational (not robotic)
3. Builds on what was already shared (reference context)
4. Matches the user's emotional state (simple if stressed, enthusiastic if excited)
5. Is concise (1-2 sentences max)

Do NOT ask multiple questions at once.
Do NOT list all missing fields.
Do ask in a warm, natural way.

Your follow-up question:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": self.core_personality},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("followup_generation_failed", error=str(e))
            # Simple fallback
            if "destination_country" in missing_fields:
                return "Where are you traveling to? ✈️"
            elif "departure_date" in missing_fields:
                return "When are you planning to depart?"
            elif any("age" in f for f in missing_fields):
                return "How old are you and anyone traveling with you?"
            else:
                return "Could you tell me a bit more about your trip?"
    
    def _build_response_prompt(
        self,
        message: str,
        response_type: str,
        context: Dict[str, Any],
        emotional_state: Optional[str],
        concerns: Optional[list]
    ) -> str:
        """Build comprehensive prompt for response generation"""
        
        # Extract key context
        destination = context.get('destination_country', 'your destination')
        activities = context.get('planned_activities', [])
        
        prompt_parts = [
            f"RESPONSE TYPE: {response_type}",
            f"USER MESSAGE: \"{message}\"",
            f"DESTINATION: {destination}",
        ]
        
        if activities and activities != ['general']:
            prompt_parts.append(f"ACTIVITIES: {', '.join(activities)}")
        
        if emotional_state:
            prompt_parts.append(f"USER EMOTIONAL STATE: {emotional_state}")
        
        if concerns:
            prompt_parts.append(f"USER CONCERNS: {', '.join(concerns)}")
        
        prompt_parts.append(f"\nGenerate a {response_type} response that:")
        prompt_parts.append("1. Feels warm and natural (like a helpful friend)")
        prompt_parts.append("2. Addresses their emotional state appropriately")
        prompt_parts.append("3. Is specific to their trip context")
        prompt_parts.append("4. Uses appropriate emojis sparingly")
        prompt_parts.append("5. Builds trust through transparency")
        
        prompt_parts.append("\nYour response (2-4 sentences):")
        
        return "\n".join(prompt_parts)
    
    def _fallback_response(self, response_type: str, context: Dict) -> str:
        """Simple fallback if LLM fails"""
        destination = context.get('destination_country', 'your destination')
        
        fallbacks = {
            "greeting": f"I'd love to help you find the perfect travel insurance for {destination}! ✈️",
            "acknowledgment": "Got it! Let me help you with that.",
            "insight": "Let me find the best coverage options for your trip.",
            "question": "Could you tell me more about your travel plans?"
        }
        
        return fallbacks.get(response_type, "I'm here to help! Let me know what you need.")


# Singleton instance
_dynamic_personality_service = None


def get_dynamic_personality_service() -> DynamicPersonalityService:
    """Get singleton instance of dynamic personality service"""
    global _dynamic_personality_service
    if _dynamic_personality_service is None:
        _dynamic_personality_service = DynamicPersonalityService()
    return _dynamic_personality_service

