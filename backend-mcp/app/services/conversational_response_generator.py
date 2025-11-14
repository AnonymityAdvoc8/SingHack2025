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
        self.settings = get_settings()
        api_key = self.settings.groq_api_key
        
        self.groq_client = Groq(api_key=api_key) if api_key else None
        self.use_llm = api_key is not None
        
        if self.use_llm:
            logger.info("conversational_response_generator_enabled", model=self.settings.groq_model)
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
                model=self.settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # More creative for natural responses
                max_tokens=500  # Plenty of room for generation
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Remove quotes if LLM wrapped response in them
            if response.startswith('"') and response.endswith('"'):
                response = response[1:-1]
            
            # Safety: If LLM returned empty, use fallback
            if not response or len(response) < 10:
                logger.warning("llm_returned_empty_using_fallback", 
                             response_length=len(response),
                             emotion=emotion)
                return self._generate_template_followup(missing_fields, trip_context)
            
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
        """Build the prompt for LLM response generation with warmth and empathy"""
        
        # Determine what to ask for
        next_question = self._determine_next_question(missing_fields, trip_context)
        
        # Build rich context description
        context_parts = []
        
        if special_context.get('occasion'):
            context_parts.append(f"🎉 Special occasion: {special_context['occasion']}")
        
        if special_context.get('has_concerns'):
            context_parts.append("😟 User has concerns about coverage")
        
        if special_context.get('demographic'):
            context_parts.append(f"👥 Demographic: {special_context['demographic']}")
        
        if trip_context.get('destination_country'):
            destination = trip_context['destination_country']
            city = trip_context.get('destination_city', '')
            if city:
                context_parts.append(f"✈️ Destination: {city}, {destination}")
            else:
                context_parts.append(f"✈️ Destination: {destination}")
        
        context_str = "\n".join(context_parts) if context_parts else "Normal trip planning"
        
        # Build prompt - Optimized for warmth, empathy, and personalization
        prompt = f"""You are TravelMate - a warm, empathetic travel insurance advisor who genuinely cares about people's trips.

USER'S MESSAGE:
"{user_message}"

CONTEXT:
{context_str}

USER'S EMOTION: {emotion}
WHAT YOU NEED TO ASK: {next_question}

YOUR GOAL: Generate a warm, natural response (1-2 sentences) that:
1. CELEBRATES special moments genuinely (anniversaries, honeymoons, family trips)
2. EMPATHIZES with concerns or worries  
3. MATCHES their enthusiasm if they're excited
4. ASKS for the needed information naturally
5. Feels like a caring friend, not a bot

EXAMPLES OF EXCEPTIONAL RESPONSES:

50th Anniversary:
✅ "Congratulations on 50 beautiful years together - what an incredible milestone! ❤️ Paris is the perfect place to celebrate. How long will you both be there?"
✅ "Wow, 50 years! That's absolutely wonderful - and Paris is so romantic! 💕 How long are you celebrating for?"

Honeymoon:
✅ "How exciting - congratulations on getting married! 💕 A honeymoon in Bali sounds absolutely perfect. When do you leave?"
✅ "Honeymoon in the Maldives - that's going to be magical! 🏝️ How long will you be there?"

Family Vacation:
✅ "A family trip to Tokyo - that's going to create such amazing memories! How many of you are going?"
✅ "Disney with the kids - they're going to love it! 🎢 How old are the little ones?"

Elderly Travelers:
✅ "A cruise sounds lovely - perfect way to see multiple places! How long is the voyage?"
✅ "Visiting family in Australia - that's so special. How long will you be staying?"

Solo Adventure:
✅ "Solo backpacking through Southeast Asia - brave and exciting! How long is your adventure?"
✅ "Hiking in Nepal on your own - wow! When do you depart?"

Worried/Concerned User:
✅ "I completely understand your concern - let me help you find coverage that gives you true peace of mind. How old are you both?"
✅ "I hear you - trip insurance can feel confusing. I'll make this simple. How long is your trip?"

Confused/Overwhelmed User:
✅ "I totally get it - insurance can feel overwhelming! Let me simplify this for you. Where are you planning to backpack?"
✅ "I understand the confusion - there IS a lot out there. I'll make it super simple. Where are you heading?"

Elderly/Health Concerns:
✅ "Visiting your grandkids in Australia sounds wonderful! I'll make sure to find coverage that addresses your health needs. How long will you be staying?"
✅ "A family visit - that's so special. With health considerations, I'll find the right plan for you both. How long is your trip?"

Business Trip (Impatient):
✅ "Singapore next week - got it. I can get you a quote in 2 minutes. How many days?"
✅ "Quick business trip - understood. How long will you be in Singapore?"

TONE RULES:
✅ Lead with WARMTH and CELEBRATION for special occasions
✅ Use appropriate emojis: ❤️ 💕 for love/celebration, ✈️ 🏝️ 🎢 for travel  
✅ Be specific ("50 beautiful years" not just "50th")
✅ Connect destination to trip type ("Paris is perfect for celebrating")
✅ Show you're listening (mention specific details they shared)
✅ Be genuinely happy for them
✅ Keep it concise (max 2 sentences)

✗ Don't be fake or over-the-top ("I'm absolutely honored and thrilled!!!")
✗ Don't use corporate speak ("I'd be delighted to assist you today")
✗ Don't restate what they just said ("You're going to France")

Now generate YOUR response (just the text, no quotes or explanation):"""
        
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

