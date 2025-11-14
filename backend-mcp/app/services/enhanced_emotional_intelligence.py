"""
Enhanced Emotional Intelligence Service
LLM-powered emotion detection and response adaptation
Handles ANY emotional state, not just predefined ones
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from groq import Groq
from app.config import get_settings
from app.utils.logger import get_logger
import json
import re

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class EmotionalProfile:
    """Comprehensive emotional profile from LLM analysis"""
    primary_emotion: str
    intensity: float  # 0.0 to 1.0
    secondary_emotions: List[str]
    detected_concerns: List[str]
    suggested_approach: str
    confidence: float


class EnhancedEmotionalIntelligence:
    """
    LLM-powered emotional intelligence that detects and adapts to ANY emotion
    No hardcoded emotion types - dynamically understands emotional nuance
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
    
    def analyze_emotional_state(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> EmotionalProfile:
        """
        Deeply analyze user's emotional state using LLM
        Detects ANY emotion, not just predefined categories
        
        Args:
            message: User's current message
            conversation_history: Previous conversation turns
            
        Returns:
            EmotionalProfile with detailed analysis
        """
        try:
            # Build conversation context
            history_str = ""
            if conversation_history and len(conversation_history) > 0:
                history_str = "\nRECENT CONVERSATION:\n"
                for msg in conversation_history[-3:]:  # Last 3 messages
                    role = msg.get("role", "").upper()
                    content = msg.get("content", "")[:200]  # Truncate long messages
                    history_str += f"{role}: {content}\n"
            
            prompt = f"""Analyze the emotional state of this user in a travel insurance conversation.

{history_str}
CURRENT USER MESSAGE: "{message}"

Perform deep emotional analysis:

1. PRIMARY EMOTION: What is the dominant emotion? (can be ANY emotion - stressed, excited, worried, confused, skeptical, frustrated, happy, anxious, overwhelmed, curious, impatient, etc.)

2. INTENSITY: How strongly are they feeling this? (0.0 = barely, 0.5 = moderate, 1.0 = very intense)

3. SECONDARY EMOTIONS: What other emotions are present?

4. DETECTED CONCERNS: What are they worried about or focused on? (e.g., "cost", "coverage gaps", "complexity", "making wrong choice", "trip safety")

5. SUGGESTED APPROACH: How should we respond? (e.g., "simplify and reassure", "provide data for confidence", "match enthusiasm", "be transparent and detailed")

Return as JSON:
{{
  "primary_emotion": "the main emotion as a single word",
  "intensity": 0.0-1.0,
  "secondary_emotions": ["emotion2", "emotion3"],
  "detected_concerns": ["concern1", "concern2"],
  "suggested_approach": "clear guidance on how to respond",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why you detected these emotions"
}}

Be nuanced - people often feel multiple emotions simultaneously.

JSON output:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower for more consistent emotion detection
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            profile = EmotionalProfile(
                primary_emotion=analysis.get("primary_emotion", "neutral"),
                intensity=float(analysis.get("intensity", 0.5)),
                secondary_emotions=analysis.get("secondary_emotions", []),
                detected_concerns=analysis.get("detected_concerns", []),
                suggested_approach=analysis.get("suggested_approach", "be helpful and clear"),
                confidence=float(analysis.get("confidence", 0.7))
            )
            
            logger.info("emotional_analysis_complete",
                       primary_emotion=profile.primary_emotion,
                       intensity=profile.intensity,
                       concerns=len(profile.detected_concerns))
            
            return profile
            
        except Exception as e:
            logger.error("emotional_analysis_failed", error=str(e))
            # Fallback to keyword detection
            return self._fallback_emotion_detection(message)
    
    def adapt_response(
        self,
        original_response: str,
        emotional_profile: EmotionalProfile,
        user_message: str
    ) -> str:
        """
        Adapt response based on detailed emotional profile
        Uses LLM to intelligently adjust tone, complexity, and framing
        
        Args:
            original_response: The factual response
            emotional_profile: Detailed emotional analysis
            user_message: User's original message
            
        Returns:
            Emotionally-adapted response
        """
        try:
            concerns_str = ", ".join(emotional_profile.detected_concerns) if emotional_profile.detected_concerns else "none detected"
            
            prompt = f"""Adapt this response to match the user's emotional state and concerns.

USER MESSAGE: "{user_message}"

EMOTIONAL PROFILE:
- Primary Emotion: {emotional_profile.primary_emotion}
- Intensity: {emotional_profile.intensity}/1.0
- Secondary Emotions: {', '.join(emotional_profile.secondary_emotions)}
- Detected Concerns: {concerns_str}
- Suggested Approach: {emotional_profile.suggested_approach}

ORIGINAL RESPONSE (may be too long/complex):
{original_response[:500]}...

Your task - adapt the response to:
1. **Acknowledge their emotion** warmly
2. **Be CONCISE** - max 3-4 sentences (150 words maximum)
3. **Address their concerns** directly
4. **Simplify drastically** if confused/overwhelmed/skeptical
5. **Match energy** appropriately
6. **Add warmth** - feel like a caring friend

Special Rules by Emotion:
- **Skeptical**: Be brief, use 1-2 data points (not a policy dump), acknowledge doubt, be transparent
- **Confused/Overwhelmed**: Super simple language, break down into steps, reassure
- **Worried/Anxious**: Empathize first, then reassure with specific coverage
- **Excited**: Match enthusiasm, celebrate
- **Impatient**: Get to the point in 2 sentences max

Example (Skeptical):
Original: [2,800 chars of policy details]
Adapted: "I hear you - your friend got lucky! Here's the reality: 1 in 12 travelers to Japan file a claim (avg $3,400). For $67, you get $50K coverage. Think of it as: 8% chance you'll need $3,400+ coverage. Worth the peace of mind? Your call - I'm just showing you the data!"

Return ONLY the adapted response (150 words max, warm tone):"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            adapted = response.choices[0].message.content.strip()
            
            logger.info("response_adapted",
                       emotion=emotional_profile.primary_emotion,
                       original_length=len(original_response),
                       adapted_length=len(adapted))
            
            return adapted
            
        except Exception as e:
            logger.error("response_adaptation_failed", error=str(e))
            # Return original if adaptation fails
            return original_response
    
    def generate_empathetic_opening(
        self,
        emotional_profile: EmotionalProfile,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a natural, empathetic opening based on emotional state
        
        Args:
            emotional_profile: Detected emotional state
            context: Conversation context
            
        Returns:
            Natural empathetic opening (or empty if not needed)
        """
        try:
            # Only add opening if emotion is moderate-to-high intensity
            if emotional_profile.intensity < 0.5:
                return ""
            
            concerns_str = ", ".join(emotional_profile.detected_concerns[:2]) if emotional_profile.detected_concerns else "general travel insurance"
            
            prompt = f"""Generate a brief, empathetic opening for a response.

USER'S EMOTIONAL STATE:
- Feeling: {emotional_profile.primary_emotion} (intensity: {emotional_profile.intensity}/1.0)
- Concerns: {concerns_str}

Generate a 1-sentence empathetic opening that:
1. Acknowledges their emotion naturally
2. Feels genuine, not robotic
3. Sets a supportive tone
4. Doesn't sound condescending

Examples of good openings:
- "I totally get it - insurance can feel overwhelming!"
- "I understand that can be stressful, but I'm here to help!"
- "How exciting! I love helping people protect amazing trips like this!"
- "Great question! I appreciate your thorough thinking."

Your opening (1 sentence):"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Higher for more natural variation
                max_tokens=100
            )
            
            opening = response.choices[0].message.content.strip()
            
            # Remove quotes if LLM added them
            opening = opening.strip('"\'')
            
            return opening
            
        except Exception as e:
            logger.error("empathetic_opening_failed", error=str(e))
            return ""
    
    def should_simplify_response(self, emotional_profile: EmotionalProfile) -> bool:
        """
        Determine if response should be simplified based on emotion
        
        Returns:
            True if user seems confused, stressed, or overwhelmed
        """
        simplify_emotions = [
            "confused", "stressed", "overwhelmed", "frustrated", 
            "lost", "uncertain", "anxious", "worried"
        ]
        
        primary_needs_simplify = any(
            emotion in emotional_profile.primary_emotion.lower() 
            for emotion in simplify_emotions
        )
        
        secondary_needs_simplify = any(
            any(emotion in sec.lower() for emotion in simplify_emotions)
            for sec in emotional_profile.secondary_emotions
        )
        
        return (primary_needs_simplify or secondary_needs_simplify) and emotional_profile.intensity > 0.5
    
    def _fallback_emotion_detection(self, message: str) -> EmotionalProfile:
        """Keyword-based fallback if LLM fails"""
        
        message_lower = message.lower()
        
        # Keyword patterns
        if any(word in message_lower for word in ["confused", "don't understand", "complicated", "overwhelmed"]):
            emotion = "confused"
            intensity = 0.7
        elif any(word in message_lower for word in ["worried", "concerned", "nervous", "anxious"]):
            emotion = "worried"
            intensity = 0.6
        elif any(word in message_lower for word in ["excited", "amazing", "can't wait", "awesome", "great"]):
            emotion = "excited"
            intensity = 0.7
        elif any(word in message_lower for word in ["frustrated", "annoying", "difficult", "hard"]):
            emotion = "frustrated"
            intensity = 0.8
        elif any(word in message_lower for word in ["why", "prove", "how do i know", "really", "sure"]):
            emotion = "skeptical"
            intensity = 0.5
        else:
            emotion = "neutral"
            intensity = 0.3
        
        return EmotionalProfile(
            primary_emotion=emotion,
            intensity=intensity,
            secondary_emotions=[],
            detected_concerns=[],
            suggested_approach="be helpful and clear",
            confidence=0.6
        )


# Singleton instance
_enhanced_emotional_intelligence = None


def get_enhanced_emotional_intelligence() -> EnhancedEmotionalIntelligence:
    """Get singleton instance of enhanced emotional intelligence"""
    global _enhanced_emotional_intelligence
    if _enhanced_emotional_intelligence is None:
        _enhanced_emotional_intelligence = EnhancedEmotionalIntelligence()
    return _enhanced_emotional_intelligence

