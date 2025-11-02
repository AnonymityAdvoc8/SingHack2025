"""
Emotional Intelligence Service
Detects user emotional state and adapts conversation accordingly
Uses Groq LLM for sophisticated emotional understanding
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import random
import os
from groq import Groq
from app.services.personality import EMOTIONAL_ACKNOWLEDGMENTS, simplify_jargon
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EmotionalContext:
    """Represents detected emotional state of user"""
    state: str  # stressed, worried, excited, frustrated, skeptical, neutral
    confidence: float  # 0.0 to 1.0
    indicators: List[str]  # Words/phrases that triggered detection
    response_prefix: str  # Empathetic acknowledgment to prepend
    adjustment: str  # How to adjust response: simplify, reassure, celebrate, provide_evidence


class EmotionalIntelligenceService:
    """
    Detects and responds to user emotional states
    Uses Groq LLM for sophisticated emotional understanding
    """
    
    def __init__(self):
        """Initialize with Groq client"""
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.groq_api_key
        
        self.groq_client = Groq(api_key=api_key) if api_key else None
        self.use_llm = api_key is not None
        
        if self.use_llm:
            logger.info("llm_emotion_detection_enabled", model="llama-3.3-70b-versatile")
        else:
            logger.warning("groq_api_key_missing", message="Falling back to keyword detection")
    
    # Fallback keyword patterns (if LLM unavailable)
    STRESS_INDICATORS = [
        "confused", "confusing", "don't understand", "overwhelming", 
        "too much", "too complicated", "lost", "help me",
        "i don't know", "what does this mean", "explain"
    ]
    
    WORRY_INDICATORS = [
        "worried", "nervous", "scared", "concerned", "anxious",
        "what if", "will i be covered", "am i protected",
        "safe", "safety", "risky", "dangerous"
    ]
    
    EXCITEMENT_INDICATORS = [
        "excited", "can't wait", "so happy", "amazing", "awesome",
        "love this", "perfect", "finally", "yes!", "great!"
    ]
    
    FRUSTRATION_INDICATORS = [
        "frustrat", "annoying", "ridiculous", "waste of time",
        "this is stupid", "too hard", "give up", "fed up",
        "this sucks", "terrible"
    ]
    
    SKEPTICISM_INDICATORS = [
        "really?", "are you sure", "i don't believe", "sounds too good",
        "is this legit", "can i trust", "prove it", "how do i know",
        "scam", "suspicious", "show me"
    ]
    
    def detect_emotion(self, message: str, conversation_history: Optional[List[Dict]] = None) -> EmotionalContext:
        """
        Detect emotional state from user message using Groq LLM
        Falls back to keyword matching if LLM unavailable
        
        Args:
            message: Current user message
            conversation_history: Previous messages for context
            
        Returns:
            EmotionalContext with detected state and response adjustments
        """
        # Try LLM-based detection first (more accurate)
        if self.use_llm and self.groq_client:
            try:
                return self._detect_emotion_with_llm(message, conversation_history)
            except Exception as e:
                logger.warning("llm_emotion_detection_failed", error=str(e), fallback="keywords")
                # Fall back to keyword detection
        
        # Fallback: Keyword-based detection
        return self._detect_emotion_with_keywords(message)
    
    def _detect_emotion_with_llm(self, message: str, conversation_history: Optional[List[Dict]] = None) -> EmotionalContext:
        """Use Groq LLM to detect emotional state"""
        
        prompt = f"""Analyze the emotional state of this user message in a travel insurance context.

User Message: "{message}"

Detect the PRIMARY emotion from these options:
- stressed (confused, overwhelmed, don't understand)
- worried (concerned, nervous, anxious about coverage, wants protection)
- excited (EXPLICITLY enthusiastic: "so excited!", "can't wait!", "amazing!")
- frustrated (annoyed, angry, fed up with complexity)
- skeptical (doubtful, questioning legitimacy or value)
- neutral (calm, matter-of-fact, just providing information, normal trip planning)

IMPORTANT: Only classify as "excited" if user is EXPLICITLY enthusiastic with exclamation marks or excitement words.
Just mentioning a trip or anniversary is NEUTRAL, not excited.

Respond in JSON format:
{{
  "emotion": "one of the above",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}}
"""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON response (handle markdown code blocks)
            import json
            import re
            
            # Remove markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            emotion = result.get("emotion", "neutral")
            confidence = float(result.get("confidence", 0.7))
            reasoning = result.get("reasoning", "")
            
            # Map to adjustment strategy
            adjustment_map = {
                "stressed": "simplify_and_reassure",
                "worried": "reassure_with_data",
                "excited": "celebrate_and_match_energy",
                "frustrated": "apologize_and_simplify",
                "skeptical": "provide_evidence_and_transparency",
                "neutral": "normal"
            }
            
            return EmotionalContext(
                state=emotion,
                confidence=confidence,
                indicators=[reasoning],
                response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS.get(emotion, EMOTIONAL_ACKNOWLEDGMENTS["neutral"])),
                adjustment=adjustment_map.get(emotion, "normal")
            )
            
        except Exception as e:
            logger.error("llm_emotion_parse_failed", error=str(e))
            # Fall back to keyword detection
            return self._detect_emotion_with_keywords(message)
    
    def _detect_emotion_with_keywords(self, message: str) -> EmotionalContext:
        """Fallback keyword-based emotion detection"""
        message_lower = message.lower()
        
        # Check for frustration FIRST (strong negative emotion, "ridiculous", "waste of time")
        frustration_matches = [word for word in self.FRUSTRATION_INDICATORS if word in message_lower]
        if frustration_matches:
            return EmotionalContext(
                state="frustrated",
                confidence=0.9,
                indicators=frustration_matches,
                response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS["frustrated"]),
                adjustment="apologize_and_simplify"
            )
        
        # Check for stress (confusion, overwhelm)
        stress_matches = [word for word in self.STRESS_INDICATORS if word in message_lower]
        if stress_matches:
            return EmotionalContext(
                state="stressed",
                confidence=0.8,
                indicators=stress_matches,
                response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS["stressed"]),
                adjustment="simplify_and_reassure"
            )
        
        # Check for worry
        worry_matches = [word for word in self.WORRY_INDICATORS if word in message_lower]
        if worry_matches:
            return EmotionalContext(
                state="worried",
                confidence=0.8,
                indicators=worry_matches,
                response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS["worried"]),
                adjustment="reassure_with_data"
            )
        
        # Check for excitement
        excitement_matches = [word for word in self.EXCITEMENT_INDICATORS if word in message_lower]
        if excitement_matches:
            return EmotionalContext(
                state="excited",
                confidence=0.7,
                indicators=excitement_matches,
                response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS["excited"]),
                adjustment="celebrate_and_match_energy"
            )
        
        # Check for skepticism
        skepticism_matches = [word for word in self.SKEPTICISM_INDICATORS if word in message_lower]
        if skepticism_matches:
            return EmotionalContext(
                state="skeptical",
                confidence=0.8,
                indicators=skepticism_matches,
                response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS["skeptical"]),
                adjustment="provide_evidence_and_transparency"
            )
        
        # Default: neutral
        return EmotionalContext(
            state="neutral",
            confidence=1.0,
            indicators=[],
            response_prefix=random.choice(EMOTIONAL_ACKNOWLEDGMENTS["neutral"]),
            adjustment="normal"
        )
    
    def adapt_response(self, response: str, emotional_context: EmotionalContext, context_type: str = "general") -> str:
        """
        Adapt response based on detected emotion
        BUT: Be selective - don't over-empathize during simple data collection
        
        Args:
            response: Original response text
            emotional_context: Detected emotional state
            context_type: Type of interaction (data_collection, policy_question, recommendation)
            
        Returns:
            Emotionally adapted response
        """
        # During data collection, be direct and natural
        if context_type == "data_collection":
            if emotional_context.state in ["frustrated", "stressed"]:
                # Strong negative emotion - simplify and empathize
                simplified = simplify_jargon(response)
                return f"{emotional_context.response_prefix}\n\n{simplified}"
            elif emotional_context.state == "excited":
                # Match excitement naturally
                return f"Amazing! ✨ {response}"
            elif emotional_context.state == "worried":
                # Acknowledge concern professionally, then ask question
                return f"I can help with that. {response}"
            else:
                # Neutral - just be direct and professional
                return response
        
        # For policy questions or recommendations - add appropriate empathy
        
        # For neutral emotions, minimal adaptation
        if emotional_context.state == "neutral":
            return response  # Don't add unnecessary prefix
        
        # For stressed/frustrated - simplify and add empathy
        if emotional_context.adjustment in ["simplify_and_reassure", "apologize_and_simplify"]:
            simplified = simplify_jargon(response)
            adapted = f"{emotional_context.response_prefix}\n\n{simplified}"
            return adapted
        
        # For worried - add brief reassurance (NOT data claims unless we're showing data)
        if emotional_context.adjustment == "reassure_with_data":
            # Only add data reassurance if response actually contains data
            if "based on" in response.lower() or "$" in response or "%" in response:
                return f"{emotional_context.response_prefix}\n\n{response}"
            else:
                # No data yet, just be empathetic
                return f"{emotional_context.response_prefix}\n\n{response}"
        
        # For excited - match energy briefly
        if emotional_context.adjustment == "celebrate_and_match_energy":
            if "smart choice" not in response.lower() and len(response) > 200:
                # Only add celebration for substantial responses
                return f"{emotional_context.response_prefix}\n\n{response}\n\n🎉 You're going to have an amazing time!"
            return f"{emotional_context.response_prefix}\n\n{response}"
        
        # For skeptical - add transparency ONLY if showing recommendations
        if emotional_context.adjustment == "provide_evidence_and_transparency":
            if "recommend" in response.lower() or "policy" in response.lower():
                return f"{emotional_context.response_prefix}\n\n{response}"
            return f"{emotional_context.response_prefix}\n\n{response}"
        
        # Default: minimal adaptation
        return response
    
    def _break_into_digestible_chunks(self, text: str) -> str:
        """
        Break long text into shorter, more digestible paragraphs
        Helps when user is stressed or overwhelmed
        """
        # Split into sentences
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Group into smaller chunks (2-3 sentences per paragraph)
        chunks = []
        current_chunk = []
        
        for i, sentence in enumerate(sentences):
            current_chunk.append(sentence)
            
            # Create paragraph every 2-3 sentences
            if len(current_chunk) >= 2 or i == len(sentences) - 1:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = []
        
        return '\n\n'.join(chunks)
    
    def generate_encouraging_message(self, context: str = "general") -> str:
        """
        Generate encouraging messages for different contexts
        
        Args:
            context: Situation context (data_collection, quote_review, decision_making)
            
        Returns:
            Encouraging message
        """
        encouragements = {
            "data_collection": [
                "You're doing great! Just a couple more questions and I'll have the perfect recommendations for you.",
                "Almost there! This information helps me find coverage that's exactly right for your trip.",
                "Perfect! Each answer helps me tailor the coverage to your specific needs."
            ],
            "quote_review": [
                "Take your time reviewing these options - I'm here if you have any questions!",
                "No pressure! Let me know if you'd like me to explain anything in more detail.",
                "Want me to highlight the key differences to make your decision easier?"
            ],
            "decision_making": [
                "Great thinking! It's smart to consider all your options carefully.",
                "You're asking all the right questions! What else would help you decide?",
                "I love that you're being thorough - that's exactly what you should do!"
            ]
        }
        
        context_messages = encouragements.get(context, encouragements["general"])
        return random.choice(context_messages)
    
    def detect_confusion_areas(self, message: str) -> List[str]:
        """
        Identify specific areas of confusion to address
        
        Returns:
            List of topics user seems confused about
        """
        confusion_areas = []
        message_lower = message.lower()
        
        topic_indicators = {
            "medical_coverage": ["medical", "hospital", "doctor", "health", "sick", "injured"],
            "trip_cancellation": ["cancel", "cancellation", "can't go", "refund"],
            "pre_existing": ["pre-existing", "preexisting", "diabetes", "condition", "health issue"],
            "deductible": ["deductible", "out of pocket", "pay first"],
            "exclusions": ["not covered", "exclusion", "what's excluded"],
            "claims": ["claim", "how to get money", "reimbursement"]
        }
        
        for topic, indicators in topic_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                confusion_areas.append(topic)
        
        return confusion_areas

