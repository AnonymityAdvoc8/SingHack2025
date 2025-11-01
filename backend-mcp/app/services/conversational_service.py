"""
TravelMate AI - Conversational Extraction Service
Natural language trip details extraction through conversation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from groq import Groq
from app.config import get_settings
from app.schemas.trip import TripDetailsSchema, TravelerSchema
from app.utils.logger import get_logger
import json
import re

settings = get_settings()
logger = get_logger(__name__)


class ConversationalExtractionService:
    """Service for extracting trip details through natural conversation"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
    
    def extract_from_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract trip details from a conversational message
        
        Args:
            message: User's message
            context: Existing conversation context
            
        Returns:
            Extracted details + what's still needed
        """
        logger.info("conversational_extraction", message_length=len(message))
        
        # Build prompt for LLM
        prompt = self._build_extraction_prompt(message, context or {})
        
        try:
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting travel details from natural conversation. Extract structured data and identify what information is still needed."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            extracted = json.loads(response.choices[0].message.content)
            
            # Merge with context
            merged = self._merge_with_context(extracted, context or {})
            
            # Determine what's missing
            missing = self._identify_missing_fields(merged)
            
            logger.info("extraction_success", extracted_fields=len(merged), missing_fields=len(missing))
            
            return {
                "extracted": merged,
                "missing": missing,
                "is_complete": len(missing) == 0,
                "confidence": extracted.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error("extraction_failed", error=str(e))
            return {
                "extracted": context or {},
                "missing": self._identify_missing_fields(context or {}),
                "is_complete": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def generate_follow_up_question(
        self,
        missing_fields: List[str],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate natural follow-up question for missing information
        
        Args:
            missing_fields: List of missing field names
            context: Current conversation context
            
        Returns:
            Natural language follow-up question
        """
        if not missing_fields:
            return ""
        
        # Prioritize questions
        priority_order = [
            "destination_country",
            "departure_date",
            "return_date",
            "travelers",
            "planned_activities"
        ]
        
        # Ask about highest priority missing field
        for field in priority_order:
            if field in missing_fields:
                return self._generate_question_for_field(field, context)
        
        # Fallback to first missing field
        return self._generate_question_for_field(missing_fields[0], context)
    
    def _build_extraction_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Build prompt for extraction"""
        
        # Separate conversation history from extracted trip details
        conversation_history = context.get("conversation_history", [])
        extracted_details = {k: v for k, v in context.items() if k != "conversation_history"}
        
        # Format conversation history for the prompt
        history_str = ""
        if conversation_history:
            history_str = "CONVERSATION HISTORY:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"
            history_str += "\n"
        
        extracted_str = json.dumps(extracted_details, indent=2) if extracted_details else "None"
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""Extract travel insurance trip details from the user's message.

TODAY'S DATE: {current_date}

{history_str}CURRENT USER MESSAGE: "{message}"

PREVIOUSLY EXTRACTED DETAILS: {extracted_str}

Extract these fields (return JSON):
{{
  "destination_country": "Country name if mentioned (e.g., 'Japan', 'USA', 'Thailand')",
  "destination_region": "Region if mentioned (e.g., 'Asia', 'Europe', 'North America')",
  "departure_date": "ISO date YYYY-MM-DD (convert relative dates like 'next month' to actual date based on today)",
  "return_date": "ISO date YYYY-MM-DD if mentioned",
  "trip_duration_days": "Number of days as integer if mentioned or can be calculated",
  "trip_purpose": "leisure/business/study if mentioned",
  "travelers": [
    {{"age": 31, "has_pre_existing_conditions": false}}
  ],
  "planned_activities": ["hiking", "skiing", "diving"],
  "has_high_risk_activities": true,
  "confidence": 0.9
}}

EXTRACTION RULES:
1. If destination is mentioned (e.g., "Japan", "travelling to Japan"), extract it to destination_country
2. If activities mentioned (hiking, skiing, diving, etc.), add to planned_activities array
3. Extract age from "31 years old male" → {{"age": 31, "has_pre_existing_conditions": false}}
4. For "with my wife" → add 2 travelers, for "solo" → 1 traveler
5. Convert relative dates: "march" → "2026-03-15" (MUST be future date!), "next month" → add 1 month to today
6. **IMPORTANT**: If extracted date is before {current_date}, add 1 year to make it future
7. High-risk activities: skiing, scuba diving, bungee jumping, skydiving, mountain climbing
8. Return ONLY valid JSON object, no additional text
9. Set fields to null if not mentioned (don't guess)
10. Use conversation history to understand context (e.g., "it" might refer to previously mentioned destination)
11. Merge new information with previously extracted details
12. Assign confidence score (0.0-1.0) based on how much info was extracted

OUTPUT (JSON only):
"""
    
    def _merge_with_context(
        self,
        extracted: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge extracted data with existing context"""
        
        merged = context.copy()
        
        # Update with new extractions (new data overwrites old)
        for key, value in extracted.items():
            if value is not None and value != "" and key != "confidence":
                merged[key] = value
        
        return merged
    
    def _identify_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """Identify which required fields are still missing"""
        
        required_fields = [
            "destination_country",
            "departure_date",
            "return_date",
            "trip_duration_days",
            "travelers"
        ]
        
        missing = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing.append(field)
            elif field == "travelers" and (not isinstance(data[field], list) or len(data[field]) == 0):
                missing.append(field)
        
        return missing
    
    def _generate_question_for_field(self, field: str, context: Dict[str, Any]) -> str:
        """Generate natural question for a missing field"""
        
        questions = {
            "destination_country": "Where are you planning to travel?",
            "departure_date": "When are you planning to depart?",
            "return_date": "When will you be returning?",
            "trip_duration_days": "How long will your trip be?",
            "travelers": "Will you be traveling alone or with others?",
            "planned_activities": "What activities are you planning (skiing, diving, sightseeing, etc.)?",
            "trip_purpose": "Is this a leisure trip, business travel, or something else?"
        }
        
        # Add context-aware variations
        dest = context.get("destination_country")
        if field == "departure_date" and dest:
            return f"When are you planning to head to {dest}?"
        if field == "return_date" and dest:
            return f"How many days will you be staying in {dest}?"
        
        return questions.get(field, f"Could you provide the {field.replace('_', ' ')}?")
    
    def validate_and_create_schema(
        self,
        extracted_data: Dict[str, Any]
    ) -> Optional[TripDetailsSchema]:
        """
        Validate extracted data and create TripDetailsSchema
        
        Args:
            extracted_data: Extracted trip details
            
        Returns:
            TripDetailsSchema or None if validation fails
        """
        try:
            # Ensure travelers is a list of TravelerSchema
            if "travelers" in extracted_data:
                travelers = []
                for t in extracted_data["travelers"]:
                    if isinstance(t, dict):
                        travelers.append(TravelerSchema(**t))
                    else:
                        travelers.append(TravelerSchema(age=t, has_pre_existing_conditions=False))
                extracted_data["travelers"] = travelers
            
            # Create schema
            trip_schema = TripDetailsSchema(**extracted_data)
            
            logger.info("schema_validation_success", destination=trip_schema.destination_country)
            return trip_schema
            
        except Exception as e:
            logger.error("schema_validation_failed", error=str(e), data=extracted_data)
            return None

