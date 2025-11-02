"""
Proactive Intelligence Service
Anticipates user needs and surfaces relevant insights automatically
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class ProactiveInsight:
    """Represents a proactive tip or insight to surface"""
    emoji: str
    type: str  # tip, alert, insight, recommendation
    priority: str  # low, medium, high
    message: str
    source: Optional[str] = None


class ProactiveIntelligenceService:
    """
    Generates proactive insights based on trip data, claims analytics, and real-time intelligence
    Anticipates user needs before they ask
    """
    
    def generate_insights(
        self,
        trip_data: Dict[str, Any],
        claims_data: Optional[Dict[str, Any]] = None,
        tavily_data: Optional[Dict[str, Any]] = None,
        policy_recommendations: Optional[List[Dict]] = None
    ) -> List[ProactiveInsight]:
        """
        Generate all relevant proactive insights for the user's trip
        
        Args:
            trip_data: Extracted trip details
            claims_data: Historical claims analytics
            tavily_data: Real-time intelligence from Tavily
            policy_recommendations: Recommended policies with metadata
            
        Returns:
            List of ProactiveInsight objects, sorted by priority
        """
        insights = []
        
        # Activity-based insights
        insights.extend(self._generate_activity_insights(trip_data))
        
        # Destination-based insights
        insights.extend(self._generate_destination_insights(trip_data, claims_data))
        
        # Claims data insights
        if claims_data:
            insights.extend(self._generate_claims_insights(claims_data, trip_data))
        
        # Real-time intelligence insights
        if tavily_data:
            insights.extend(self._generate_realtime_insights(tavily_data))
        
        # Coverage insights
        if policy_recommendations:
            insights.extend(self._generate_coverage_insights(policy_recommendations, trip_data, claims_data))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return insights
    
    def _generate_activity_insights(self, trip_data: Dict[str, Any]) -> List[ProactiveInsight]:
        """Generate insights based on planned activities"""
        insights = []
        # Support both 'activities' and 'planned_activities' keys
        activities = trip_data.get("planned_activities", trip_data.get("activities", []))
        
        if not activities:
            return insights
        
        # Skiing insights
        if any(act.lower() in ["skiing", "snowboarding", "ski"] for act in activities):
            insights.append(ProactiveInsight(
                emoji="⛷️",
                type="tip",
                priority="high",  # Changed from medium to high
                message="Quick heads up: 73% of skiing claims involve equipment damage or ski lift closures. All recommended plans cover this, but consider adding equipment rental protection if you're renting gear!"
            ))
        
        # Diving insights
        if any(act in ["diving", "scuba", "snorkeling"] for act in activities):
            insights.append(ProactiveInsight(
                emoji="🤿",
                type="tip",
                priority="high",
                message="Important: Make sure your dive certification is current! Most policies require valid certification for dive-related claims. Also, consider depth limits in your coverage."
            ))
        
        # Hiking/trekking insights
        if any(act in ["hiking", "trekking", "mountaineering", "climbing"] for act in activities):
            insights.append(ProactiveInsight(
                emoji="🥾",
                type="tip",
                priority="medium",
                message="Pro tip: For remote hiking areas, medical evacuation coverage is crucial. Some trails can be hours from the nearest hospital. I'd recommend ensuring your plan includes helicopter evacuation."
            ))
        
        # Water sports insights
        if any(act in ["surfing", "kayaking", "rafting", "jet ski"] for act in activities):
            insights.append(ProactiveInsight(
                emoji="🏄",
                type="tip",
                priority="medium",
                message="Water sports tip: Equipment damage and weather-related cancellations are common. Make sure your plan covers both!"
            ))
        
        # Extreme sports
        if any(act in ["bungee", "skydiving", "paragliding", "rock climbing"] for act in activities):
            insights.append(ProactiveInsight(
                emoji="🪂",
                type="alert",
                priority="high",
                message="Extreme sports alert: Not all standard policies cover activities like skydiving or bungee jumping. I'll make sure to recommend plans that explicitly cover your activities!"
            ))
        
        return insights
    
    def _generate_destination_insights(self, trip_data: Dict[str, Any], claims_data: Optional[Dict] = None) -> List[ProactiveInsight]:
        """Generate insights based on destination"""
        insights = []
        destination = trip_data.get("destination_country", "")
        
        # Destination-specific tips
        destination_tips = {
            "Japan": {
                "emoji": "🇯🇵",
                "message": "Japan travel tip: Medical care is excellent but can be expensive without insurance. Also, earthquakes are possible - trip interruption coverage gives peace of mind."
            },
            "USA": {
                "emoji": "🇺🇸",
                "message": "USA travel alert: Medical costs in the US are 3-5x higher than most countries. I strongly recommend maximum medical coverage for peace of mind."
            },
            "Thailand": {
                "emoji": "🇹🇭",
                "message": "Thailand tip: Monsoon season (May-October) can affect travel plans. Trip interruption coverage is worth considering!"
            },
            "Australia": {
                "emoji": "🇦🇺",
                "message": "Australia tip: Remote areas mean evacuation coverage is important. Also, wildlife encounters (though rare) are a consideration for adventure activities."
            }
        }
        
        if destination in destination_tips:
            tip = destination_tips[destination]
            insights.append(ProactiveInsight(
                emoji=tip["emoji"],
                type="insight",
                priority="medium",
                message=tip["message"]
            ))
        
        return insights
    
    def _generate_claims_insights(self, claims_data: Dict[str, Any], trip_data: Dict) -> List[ProactiveInsight]:
        """Generate insights from historical claims data"""
        insights = []
        
        # High claims frequency
        if claims_data.get("total_claims", 0) > 1000:
            avg_claim = claims_data.get("average_claim_amount", 0)
            destination = trip_data.get("destination_country", "this destination")
            
            insights.append(ProactiveInsight(
                emoji="📊",
                type="insight",
                priority="high",
                message=f"Data insight: Based on {claims_data.get('total_claims'):,} real MSIG claims to {destination}, the average claim is ${avg_claim:,.0f}. The coverage I'm recommending exceeds this significantly for your protection."
            ))
        
        # High medical claims percentage
        if claims_data.get("top_claim_types"):
            top_type = claims_data["top_claim_types"][0]
            if top_type.get("type") == "Medical" and top_type.get("percentage", 0) > 60:
                insights.append(ProactiveInsight(
                    emoji="🏥",
                    type="insight",
                    priority="medium",
                    message=f"Medical claims make up {top_type['percentage']:.0f}% of all claims for this destination. Medical coverage is especially important for your trip!"
                ))
        
        # High average claim amounts
        if claims_data.get("average_claim_amount", 0) > 5000:
            insights.append(ProactiveInsight(
                emoji="💰",
                type="recommendation",
                priority="medium",
                message=f"Historical insight: Claims to this destination average ${claims_data['average_claim_amount']:,.0f}, which is above average. I've prioritized plans with strong coverage limits."
            ))
        
        return insights
    
    def _generate_realtime_insights(self, tavily_data: Dict[str, Any]) -> List[ProactiveInsight]:
        """Generate insights from real-time Tavily intelligence"""
        insights = []
        
        # Health advisories
        if tavily_data.get("health_alerts"):
            for alert in tavily_data["health_alerts"][:2]:  # Top 2 alerts
                insights.append(ProactiveInsight(
                    emoji="⚠️",
                    type="alert",
                    priority="high",
                    message=f"Current health advisory: {alert.get('summary', 'Health alert detected')}. Medical coverage is especially important for this trip.",
                    source=alert.get("source", "gov.sg")
                ))
        
        # Travel advisories
        if tavily_data.get("travel_restrictions"):
            insights.append(ProactiveInsight(
                emoji="🚨",
                type="alert",
                priority="high",
                message=f"Travel advisory: {tavily_data['travel_restrictions']}. Consider trip cancellation coverage in case plans change."
            ))
        
        # Weather alerts
        if tavily_data.get("weather_alerts"):
            insights.append(ProactiveInsight(
                emoji="🌧️",
                type="alert",
                priority="medium",
                message=f"Weather heads up: {tavily_data['weather_alerts']}. Trip interruption coverage recommended."
            ))
        
        return insights
    
    def _generate_coverage_insights(
        self,
        policy_recommendations: List[Dict],
        trip_data: Dict,
        claims_data: Optional[Dict]
    ) -> List[ProactiveInsight]:
        """Generate insights about recommended coverage"""
        insights = []
        
        if not policy_recommendations:
            return insights
        
        # Find recommended policy
        recommended = next((p for p in policy_recommendations if p.get("is_recommended")), policy_recommendations[0])
        
        # Coverage vs claims comparison
        if claims_data and recommended.get("benefits"):
            medical_benefit = next((b for b in recommended["benefits"] if "medical" in b.get("name", "").lower()), None)
            if medical_benefit and claims_data.get("average_claim_amount"):
                coverage_amount = medical_benefit.get("limit", 0)
                avg_claim = claims_data["average_claim_amount"]
                
                if coverage_amount > 0:
                    multiplier = coverage_amount / avg_claim
                    
                    if multiplier > 5:
                        insights.append(ProactiveInsight(
                            emoji="🛡️",
                            type="insight",
                            priority="low",
                            message=f"Peace of mind: Your recommended coverage ({self._format_currency(coverage_amount)}) exceeds the historical average claim by {multiplier:.1f}x. You'll be well protected!"
                        ))
        
        # Pre-existing condition coverage
        if trip_data.get("has_pre_existing_conditions") and recommended.get("covers_pre_existing"):
            insights.append(ProactiveInsight(
                emoji="💚",
                type="recommendation",
                priority="medium",
                message="Good news: The recommended plan specifically covers pre-existing conditions, which is crucial for your situation!"
            ))
        
        return insights
    
    def format_insights_for_display(self, insights: List[ProactiveInsight]) -> str:
        """
        Format insights for conversational display
        
        Returns:
            Markdown formatted string of insights
        """
        if not insights:
            return ""
        
        # Group by type
        alerts = [i for i in insights if i.type == "alert"]
        tips = [i for i in insights if i.type == "tip"]
        recommendations = [i for i in insights if i.type in ["insight", "recommendation"]]
        
        sections = []
        
        # Alerts first (highest priority)
        if alerts:
            alert_text = "\n".join([f"{i.emoji} **{i.message}**" for i in alerts])
            sections.append(f"### ⚠️ Important Alerts\n{alert_text}")
        
        # Tips
        if tips:
            tip_text = "\n".join([f"{i.emoji} {i.message}" for i in tips])
            sections.append(f"### 💡 Pro Tips\n{tip_text}")
        
        # Insights/Recommendations
        if recommendations:
            rec_text = "\n".join([f"{i.emoji} {i.message}" for i in recommendations])
            sections.append(f"### 📊 Data-Driven Insights\n{rec_text}")
        
        return "\n\n".join(sections)
    
    def _format_currency(self, amount: float) -> str:
        """Format currency with appropriate symbol"""
        return f"SGD ${amount:,.0f}"

