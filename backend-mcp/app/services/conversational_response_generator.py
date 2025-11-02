"""
Conversational Response Generator
Uses Groq LLM to generate natural, context-aware responses
Makes the bot feel like talking to a knowledgeable friend
"""

from typing import Dict, Any, List, Optional
from groq import Groq
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationalResponseGenerator:
    """
    Generates natural, contextual responses using LLM
    Much better than templates - adapts to any situation
    """
    
    def __init__(self):
        """Initialize with Groq client"""
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.groq_api_key
        
        self.groq_client = Groq(api_key=api_key) if api_key else None
        self.use_llm = api_key is not None
        
        if self.use_llm:
            logger.info("conversational_response_generator_enabled", model="llama-3.3-70b-versatile")
        else:
            logger.warning("groq_api_key_missing", message="Using template responses")
    
    def generate_followup_question(
        self,
        user_message: str,
        emotion: str,
        missing_fields: List[str],
        trip_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a natural follow-up question that feels human
        
        Args:
            user_message: What the user just said
            emotion: Detected emotional state
            missing_fields: What data we still need
            trip_context: What we know about the trip so far
            conversation_history: Recent conversation turns
            
        Returns:
            Natural, contextual response with follow-up question
        """
        if not self.use_llm:
            return self._generate_template_followup(missing_fields, trip_context)
        
        try:
            # Detect special occasions or context
            special_context = self._detect_special_context(user_message, trip_context)
            
            # Build prompt for LLM
            prompt = self._build_followup_prompt(
                user_message,
                emotion,
                missing_fields,
                trip_context,
                special_context
            )
            
            # Generate response
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # More creative for natural responses
                max_tokens=200
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Remove quotes if LLM wrapped response in them
            if response.startswith('"') and response.endswith('"'):
                response = response[1:-1]
            
            logger.info("conversational_response_generated",
                       length=len(response),
                       emotion=emotion,
                       special_context=special_context)
            
            return response
            
        except Exception as e:
            logger.error("conversational_generation_failed", error=str(e))
            return self._generate_template_followup(missing_fields, trip_context)
    
    def _detect_special_context(self, message: str, trip_context: Dict) -> Dict[str, Any]:
        """Detect special occasions or important context"""
        message_lower = message.lower()
        
        special = {}
        
        # Occasions
        if "anniversary" in message_lower:
            # Extract which anniversary
            import re
            match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:wedding\s*)?anniversary', message_lower)
            if match:
                special['occasion'] = f"{match.group(1)}th anniversary"
            else:
                special['occasion'] = "anniversary"
        
        if "honeymoon" in message_lower:
            special['occasion'] = "honeymoon"
        
        if "wedding" in message_lower and "anniversary" not in message_lower:
            special['occasion'] = "wedding trip"
        
        # Trip types
        if any(word in message_lower for word in ["business", "work", "conference"]):
            special['trip_type'] = "business"
        
        if "family reunion" in message_lower or "visiting family" in message_lower:
            special['trip_type'] = "family"
        
        # Age-related context
        if trip_context.get('travelers'):
            ages = [t.get('age') for t in trip_context['travelers'] if t.get('age')]
            if ages:
                avg_age = sum(ages) / len(ages)
                if avg_age > 70:
                    special['demographic'] = "elderly_travelers"
                elif avg_age < 25:
                    special['demographic'] = "young_travelers"
        
        # Concerns mentioned
        if any(word in message_lower for word in ["worried", "concerned", "nervous", "make sure", "protected"]):
            special['has_concerns'] = True
        
        return special
    
    def _build_followup_prompt(
        self,
        user_message: str,
        emotion: str,
        missing_fields: List[str],
        trip_context: Dict,
        special_context: Dict
    ) -> str:
        """Build the prompt for LLM response generation"""
        
        # Determine what to ask for
        next_question = self._determine_next_question(missing_fields, trip_context)
        
        # Build context description
        context_parts = []
        
        if special_context.get('occasion'):
            context_parts.append(f"Special occasion: {special_context['occasion']}")
        
        if special_context.get('has_concerns'):
            context_parts.append("User has expressed concern about coverage")
        
        if special_context.get('demographic'):
            context_parts.append(f"Demographic: {special_context['demographic']}")
        
        if trip_context.get('destination_country'):
            context_parts.append(f"Destination: {trip_context['destination_country']}")
        
        context_str = " | ".join(context_parts) if context_parts else "Normal trip planning"
        
        # Build prompt
        prompt = f"""You are TravelMate, a helpful travel insurance advisor. Respond naturally - warm but not excessive.

USER: "{user_message}"
CONTEXT: {context_str}
EMOTION: {emotion}
ASK FOR: {next_question}

Generate 1-2 sentences that feel natural:

IF SPECIAL OCCASION:
- "Congratulations on your 50th! How old are you both?"
- "Honeymoon - how exciting! How long will you be there?"
- "Family reunion in Australia sounds lovely. How old are the travelers?"

IF WORRIED/CONCERNED:
- "I understand. I'll make sure you're properly covered. How old are you both?"
- "I can help with that. How long is your trip?"

IF THEY JUST PROVIDED INFO:
- "Perfect! How old are you both?" (don't restate what they said)
- "Got it. When are you traveling?"

IF NEUTRAL/NORMAL:
- "How long will you be in Paris?"
- "How old are you both?"
- "When are you traveling?"

TONE:
✓ Be warm and friendly (like talking to a friend)
✓ Acknowledge special moments genuinely
✓ Be concise - max 2 sentences
✓ DON'T restate what they just told you ("You're going to France for 2 weeks")
✓ DON'T use generic fluff ("wonderful", "suits your needs", "I'd love to")
✓ DO show you listened (acknowledge occasion, concern)
✓ DO get to the question

GOOD EXAMPLES:
- "Congratulations on your 50th! How old are you both?"
- "Business trip to Tokyo - got it. How long will you be there?"
- "Perfect! How old are you both?"
- "I understand your concern. How old are you both?"

BAD (restating obvious):
- "You're traveling to France for 2 weeks. How old are you both?"

BAD (too verbose):
- "What a wonderful milestone! I'm honored to help..."

Response (just the text):"""
        
        return prompt
    
    def _determine_next_question(self, missing_fields: List[str], trip_context: Dict) -> str:
        """Determine what question to ask based on missing fields"""
        
        if not missing_fields:
            return "We have everything needed"
        
        # Priority order
        if 'destination_country' in missing_fields:
            return "destination country"
        
        if 'return_date_or_duration' in missing_fields:
            if trip_context.get('destination_country'):
                return f"how long they'll be in {trip_context['destination_country']}"
            return "trip duration"
        
        if 'traveler_1_age' in missing_fields or 'traveler_2_age' in missing_fields:
            num = len([f for f in missing_fields if 'age' in f])
            if num == 1:
                return "their age"
            return "ages of both travelers"
        
        if 'departure_date' in missing_fields:
            return "when they're traveling"
        
        return "more trip details"
    
    def _generate_template_followup(self, missing_fields: List[str], trip_context: Dict) -> str:
        """Fallback template-based response"""
        if 'traveler_1_age' in missing_fields or 'traveler_2_age' in missing_fields:
            return "How old are you both?"
        
        if 'destination_country' in missing_fields:
            return "Where are you traveling to?"
        
        if 'return_date_or_duration' in missing_fields:
            if trip_context.get('destination_country'):
                return f"How long will you be in {trip_context.get('destination_country')}?"
            return "How long is your trip?"
        
        return "Could you tell me more about your trip?"

