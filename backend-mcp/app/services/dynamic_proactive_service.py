"""
Dynamic Proactive Intelligence Service
Uses LLM to generate insights for ANY activity, destination, or situation
No hardcoded if-statements - fully adaptive and intelligent
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from groq import Groq
from app.config import get_settings
from app.utils.logger import get_logger
import json

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class DynamicInsight:
    """Represents a dynamically-generated insight"""
    emoji: str
    type: str  # tip, alert, insight, recommendation
    priority: str  # low, medium, high
    message: str
    source: Optional[str] = None
    confidence: float = 0.8


class DynamicProactiveService:
    """
    LLM-powered proactive intelligence that generates insights for ANY context
    No hardcoded rules - learns from data and generates contextual advice
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
    
    def generate_all_insights(
        self,
        trip_data: Dict[str, Any],
        claims_data: Optional[Dict[str, Any]] = None,
        realtime_data: Optional[Dict[str, Any]] = None,
        policy_recommendations: Optional[List[Dict]] = None
    ) -> List[DynamicInsight]:
        """
        Generate ALL relevant insights using LLM intelligence
        Single LLM call analyzes entire context and returns prioritized insights
        
        Args:
            trip_data: Extracted trip details
            claims_data: Historical claims analytics
            realtime_data: Real-time intelligence (Tavily)
            policy_recommendations: Recommended policies
            
        Returns:
            List of DynamicInsight objects, prioritized
        """
        try:
            # Build comprehensive context
            context = self._build_context(
                trip_data, claims_data, realtime_data, policy_recommendations
            )
            
            prompt = self._build_insights_prompt(context)
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert travel insurance analyst. Generate proactive insights as valid JSON only.
CRITICAL: Return ONLY the JSON object. No markdown, no code fences, no explanations."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower for more consistent JSON
                max_tokens=800,  # Shorter to avoid truncation
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:].strip()
            
            insights_data = json.loads(content)
            insights = self._parse_insights(insights_data)
            
            logger.info("dynamic_insights_generated", 
                       count=len(insights),
                       destination=trip_data.get('destination_country'))
            
            return insights
            
        except Exception as e:
            logger.error("dynamic_insights_generation_failed", error=str(e))
            # Return minimal fallback insights
            return self._generate_fallback_insights(trip_data)
    
    def generate_activity_specific_insights(
        self,
        activities: List[str],
        destination: str,
        claims_data: Optional[Dict] = None
    ) -> List[DynamicInsight]:
        """
        Generate insights for ANY activity using LLM
        Works for activities we've never seen before
        
        Args:
            activities: List of planned activities (can be anything)
            destination: Destination country
            claims_data: Historical claims data if available
            
        Returns:
            List of activity-specific insights
        """
        try:
            activities_str = ", ".join(activities)
            claims_context = ""
            
            if claims_data and claims_data.get("activity_breakdown"):
                claims_context = f"\n\nHistorical Claims Data:\n{json.dumps(claims_data['activity_breakdown'], indent=2)}"
            
            prompt = f"""Analyze these activities and generate proactive insurance insights.

ACTIVITIES: {activities_str}
DESTINATION: {destination}{claims_context}

For EACH activity, identify:
1. Key insurance-relevant risks
2. Coverage considerations
3. Data-backed statistics if available
4. Practical tips

Return insights as JSON array:
[
  {{
    "emoji": "⛷️",
    "activity": "skiing",
    "priority": "high",
    "message": "Specific, helpful insight with data if available",
    "risk_factors": ["factor1", "factor2"],
    "coverage_recommendation": "what coverage is important"
  }}
]

Focus on being genuinely helpful, not alarmist. Use specific details about the activities.
If no historical data, use general knowledge of activity risks.

JSON output:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            insights_data = json.loads(response.choices[0].message.content)
            
            # Convert to DynamicInsight objects
            insights = []
            for insight in insights_data.get("insights", insights_data.get("activities", [])):
                insights.append(DynamicInsight(
                    emoji=insight.get("emoji", "💡"),
                    type="tip",
                    priority=insight.get("priority", "medium"),
                    message=insight.get("message", ""),
                    confidence=0.8
                ))
            
            return insights
            
        except Exception as e:
            logger.error("activity_insights_failed", error=str(e), activities=activities)
            return []
    
    def generate_destination_insights(
        self,
        destination: str,
        travel_dates: Optional[str] = None,
        claims_data: Optional[Dict] = None,
        realtime_data: Optional[Dict] = None
    ) -> List[DynamicInsight]:
        """
        Generate destination insights for ANY country using LLM
        Combines historical claims + real-time intelligence
        
        Args:
            destination: ANY country or city
            travel_dates: When traveling
            claims_data: Historical MSIG claims
            realtime_data: Tavily real-time intelligence
            
        Returns:
            List of destination-specific insights
        """
        try:
            context_parts = [f"DESTINATION: {destination}"]
            
            if travel_dates:
                context_parts.append(f"TRAVEL DATES: {travel_dates}")
            
            if claims_data:
                context_parts.append(f"\nHISTORICAL CLAIMS (MSIG Data):")
                context_parts.append(f"- Total Claims: {claims_data.get('total_claims', 0):,}")
                context_parts.append(f"- Average Claim: ${claims_data.get('average_claim_amount', 0):,.0f}")
                context_parts.append(f"- Top Claim Types: {claims_data.get('top_claim_types', [])}")
            
            if realtime_data:
                context_parts.append(f"\nCURRENT REAL-TIME DATA:")
                if realtime_data.get('health_alerts'):
                    context_parts.append(f"- Health Alerts: {realtime_data['health_alerts']}")
                if realtime_data.get('travel_advisories'):
                    context_parts.append(f"- Travel Advisories: {realtime_data['travel_advisories']}")
                if realtime_data.get('weather'):
                    context_parts.append(f"- Weather: {realtime_data['weather']}")
            
            context_str = "\n".join(context_parts)
            
            prompt = f"""Analyze this destination and generate insurance-relevant insights.

{context_str}

Generate 2-4 proactive insights as JSON:
{{
  "insights": [
    {{
      "emoji": "🏥",
      "priority": "high/medium/low",
      "type": "alert/tip/insight",
      "message": "Specific, actionable insight with data",
      "source": "claims_data or realtime or general_knowledge"
    }}
  ]
}}

Focus on:
1. Medical cost considerations
2. Common claim types for this destination
3. Current advisories or risks
4. Seasonal factors (weather, holidays, etc.)
5. Cultural/practical considerations

Be specific to THIS destination, not generic.

JSON output:"""
            
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            insights_data = json.loads(response.choices[0].message.content)
            
            insights = []
            for insight in insights_data.get("insights", []):
                insights.append(DynamicInsight(
                    emoji=insight.get("emoji", "✈️"),
                    type=insight.get("type", "insight"),
                    priority=insight.get("priority", "medium"),
                    message=insight.get("message", ""),
                    source=insight.get("source"),
                    confidence=0.8 if insight.get("source") in ["claims_data", "realtime"] else 0.6
                ))
            
            return insights
            
        except Exception as e:
            logger.error("destination_insights_failed", error=str(e), destination=destination)
            return []
    
    def _build_context(
        self,
        trip_data: Dict,
        claims_data: Optional[Dict],
        realtime_data: Optional[Dict],
        policies: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Build comprehensive context for insight generation"""
        
        context = {
            "trip": {
                "destination": trip_data.get("destination_country"),
                "duration": trip_data.get("trip_duration_days"),
                "activities": trip_data.get("planned_activities", []),
                "travelers": len(trip_data.get("travelers", [])),
                "ages": [t.get("age") for t in trip_data.get("travelers", []) if t.get("age")]
            }
        }
        
        if claims_data:
            context["historical_claims"] = {
                "total_claims": claims_data.get("total_claims", 0),
                "average_amount": claims_data.get("average_claim_amount", 0),
                "top_types": claims_data.get("top_claim_types", []),
                "risk_level": claims_data.get("risk_level", "unknown")
            }
        
        if realtime_data:
            context["realtime_intelligence"] = {
                "health_alerts": realtime_data.get("health_alerts", []),
                "travel_restrictions": realtime_data.get("travel_restrictions"),
                "weather_alerts": realtime_data.get("weather_alerts")
            }
        
        if policies:
            context["recommended_policies"] = []
            for p in policies[:2]:
                medical_benefits = [
                    b.get("coverage_limit") or 0 
                    for b in p.get("benefits", []) 
                    if "medical" in b.get("benefit_name", "").lower()
                ]
                context["recommended_policies"].append({
                    "name": p.get("policy_name"),
                    "medical_coverage": max(medical_benefits) if medical_benefits else 0
                })
        
        return context
    
    def _build_insights_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for insight generation"""
        
        context_str = json.dumps(context, indent=2)
        
        return f"""Analyze this trip context and generate 2-3 proactive insurance insights.

CONTEXT:
{context_str}

Generate insights that are:
1. Specific to this trip
2. Data-driven when possible
3. Actionable and helpful
4. Not alarmist or salesy

CRITICAL: Return ONLY valid JSON without markdown code fences or backticks.
Do not wrap your response in ```json or any other formatting.
Return the raw JSON object directly.

{{
  "insights": [
    {{
      "emoji": "✈️",
      "type": "tip",
      "priority": "medium",
      "message": "Brief helpful insight with data if available",
      "reasoning": "why this matters"
    }}
  ]
}}

Output only the JSON object, nothing else:"""
    
    def _parse_insights(self, insights_data: Dict) -> List[DynamicInsight]:
        """Parse LLM JSON output into DynamicInsight objects"""
        
        insights = []
        
        for insight in insights_data.get("insights", []):
            insights.append(DynamicInsight(
                emoji=insight.get("emoji", "💡"),
                type=insight.get("type", "insight"),
                priority=insight.get("priority", "medium"),
                message=insight.get("message", ""),
                source="llm_analysis",
                confidence=0.8
            ))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return insights
    
    def _generate_fallback_insights(self, trip_data: Dict) -> List[DynamicInsight]:
        """Generate minimal insights if LLM fails"""
        
        destination = trip_data.get("destination_country", "your destination")
        
        return [
            DynamicInsight(
                emoji="✈️",
                type="insight",
                priority="medium",
                message=f"Travel insurance provides important protection for your trip to {destination}. Let me find the best coverage options for you!",
                confidence=0.5
            )
        ]


# Singleton instance
_dynamic_proactive_service = None


def get_dynamic_proactive_service() -> DynamicProactiveService:
    """Get singleton instance of dynamic proactive service"""
    global _dynamic_proactive_service
    if _dynamic_proactive_service is None:
        _dynamic_proactive_service = DynamicProactiveService()
    return _dynamic_proactive_service

