"""
TravelMate AI - Tavily Intelligence Service
Real-time travel intelligence using Tavily Search API
"""

from typing import Dict, Any, List, Optional
from tavily import TavilyClient
from app.config import get_settings
from app.utils.logger import get_logger
from datetime import datetime, timedelta

settings = get_settings()
logger = get_logger(__name__)


class TavilyIntelligenceService:
    """Service for real-time travel intelligence using Tavily API"""
    
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=1)  # Cache for 1 hour
    
    def get_destination_intelligence(
        self,
        destination: str,
        travel_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get real-time destination intelligence
        
        Args:
            destination: Country or city name
            travel_date: Optional travel date for temporal context
            
        Returns:
            Dictionary with travel advisories, requirements, alerts
        """
        cache_key = f"dest_{destination}_{travel_date or 'current'}"
        
        # Check cache
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached["timestamp"] < self._cache_ttl:
                logger.info("tavily_cache_hit", destination=destination)
                return cached["data"]
        
        logger.info("tavily_destination_search", destination=destination, date=travel_date)
        
        # Build search query
        query = f"travel to {destination} {travel_date or 'current'} requirements visa insurance health vaccination mandatory entry"
        
        try:
            results = self.client.search(
                query=query,
                search_depth=settings.tavily_search_depth,
                max_results=5,
                include_domains=["gov.sg", "moh.gov.sg", "who.int", "gov.uk", "state.gov"]  # Trusted sources
            )
            
            intelligence = {
                "destination": destination,
                "travel_date": travel_date,
                "answer": results.get("answer", ""),
                "key_findings": self._extract_key_findings(results),
                "insurance_requirements": self._extract_insurance_requirements(results),
                "health_alerts": self._extract_health_alerts(results),
                "citations": [r.get("url") for r in results.get("results", [])],
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache results
            self._cache[cache_key] = {
                "data": intelligence,
                "timestamp": datetime.now()
            }
            
            logger.info("tavily_destination_success", destination=destination, findings=len(intelligence["key_findings"]))
            return intelligence
            
        except Exception as e:
            logger.error("tavily_destination_failed", destination=destination, error=str(e))
            return {
                "destination": destination,
                "error": str(e),
                "answer": f"Unable to fetch real-time intelligence for {destination}",
                "key_findings": [],
                "insurance_requirements": [],
                "health_alerts": [],
                "citations": []
            }
    
    def analyze_real_time_risks(
        self,
        destination: str,
        activities: List[str],
        travel_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze real-time risks for destination and activities
        
        Args:
            destination: Travel destination
            activities: List of planned activities
            travel_date: Optional travel date
            
        Returns:
            Dictionary with risk analysis and recommendations
        """
        cache_key = f"risk_{destination}_{'-'.join(activities)}_{travel_date or 'current'}"
        
        # Check cache
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached["timestamp"] < self._cache_ttl:
                logger.info("tavily_cache_hit", type="risk", destination=destination)
                return cached["data"]
        
        logger.info("tavily_risk_search", destination=destination, activities=activities)
        
        # Build search query
        activities_str = ", ".join(activities) if activities else "general travel"
        query = f"{destination} {travel_date or 'current'} travel risks {activities_str} weather conditions health outbreak accidents insurance claims"
        
        try:
            results = self.client.search(
                query=query,
                search_depth=settings.tavily_search_depth,
                max_results=5
            )
            
            risk_analysis = {
                "destination": destination,
                "activities": activities,
                "travel_date": travel_date,
                "risk_summary": results.get("answer", ""),
                "risk_factors": self._extract_risk_factors(results, activities),
                "current_conditions": self._extract_current_conditions(results),
                "recommendations": self._generate_risk_recommendations(results, activities),
                "citations": [r.get("url") for r in results.get("results", [])],
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache results
            self._cache[cache_key] = {
                "data": risk_analysis,
                "timestamp": datetime.now()
            }
            
            logger.info("tavily_risk_success", destination=destination, factors=len(risk_analysis["risk_factors"]))
            return risk_analysis
            
        except Exception as e:
            logger.error("tavily_risk_failed", destination=destination, error=str(e))
            return {
                "destination": destination,
                "activities": activities,
                "error": str(e),
                "risk_summary": f"Unable to fetch real-time risk data for {destination}",
                "risk_factors": [],
                "current_conditions": {},
                "recommendations": [],
                "citations": []
            }
    
    def get_medical_cost_intelligence(
        self,
        destination: str
    ) -> Dict[str, Any]:
        """
        Get real-time medical cost intelligence for destination
        
        Args:
            destination: Travel destination
            
        Returns:
            Medical cost information and recommendations
        """
        cache_key = f"medical_{destination}"
        
        # Check cache
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached["timestamp"] < self._cache_ttl:
                logger.info("tavily_cache_hit", type="medical", destination=destination)
                return cached["data"]
        
        logger.info("tavily_medical_search", destination=destination)
        
        query = f"{destination} hospital costs medical expenses treatment prices emergency room ambulance healthcare tourism insurance"
        
        try:
            results = self.client.search(
                query=query,
                search_depth=settings.tavily_search_depth,
                max_results=3
            )
            
            medical_intel = {
                "destination": destination,
                "cost_summary": results.get("answer", ""),
                "average_costs": self._extract_medical_costs(results),
                "coverage_recommendations": self._generate_coverage_recommendations(results),
                "citations": [r.get("url") for r in results.get("results", [])],
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache results
            self._cache[cache_key] = {
                "data": medical_intel,
                "timestamp": datetime.now()
            }
            
            logger.info("tavily_medical_success", destination=destination)
            return medical_intel
            
        except Exception as e:
            logger.error("tavily_medical_failed", destination=destination, error=str(e))
            return {
                "destination": destination,
                "error": str(e),
                "cost_summary": f"Unable to fetch medical cost data for {destination}",
                "average_costs": {},
                "coverage_recommendations": [],
                "citations": []
            }
    
    # Helper methods for parsing Tavily results
    
    def _extract_key_findings(self, results: Dict[str, Any]) -> List[str]:
        """Extract key findings from search results"""
        findings = []
        answer = results.get("answer") or ""
        
        if not answer:
            return findings
        
        # Simple extraction - split by sentences containing key terms
        key_terms = ["required", "mandatory", "must", "need", "warning", "alert", "advisory"]
        sentences = answer.split(". ")
        
        for sentence in sentences:
            if any(term in sentence.lower() for term in key_terms):
                findings.append(sentence.strip())
        
        return findings[:5]  # Top 5 findings
    
    def _extract_insurance_requirements(self, results: Dict[str, Any]) -> List[str]:
        """Extract insurance-related requirements"""
        requirements = []
        answer = results.get("answer") or ""
        
        if not answer:
            return requirements
        
        if "insurance" in answer.lower():
            # Extract sentences about insurance
            sentences = answer.split(". ")
            for sentence in sentences:
                if "insurance" in sentence.lower():
                    requirements.append(sentence.strip())
        
        return requirements
    
    def _extract_health_alerts(self, results: Dict[str, Any]) -> List[str]:
        """Extract health-related alerts"""
        alerts = []
        answer = results.get("answer") or ""
        
        if not answer:
            return alerts
        
        health_terms = ["covid", "dengue", "malaria", "outbreak", "vaccination", "disease", "health"]
        sentences = answer.split(". ")
        
        for sentence in sentences:
            if any(term in sentence.lower() for term in health_terms):
                alerts.append(sentence.strip())
        
        return alerts[:3]  # Top 3 alerts
    
    def _extract_risk_factors(self, results: Dict[str, Any], activities: List[str]) -> List[Dict[str, str]]:
        """Extract specific risk factors"""
        factors = []
        answer = results.get("answer") or ""
        
        if not answer:
            return factors
        
        # Look for risk-related keywords
        risk_keywords = ["risk", "danger", "hazard", "warning", "accident", "incident", "injury"]
        sentences = answer.split(". ")
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                factors.append({
                    "description": sentence.strip(),
                    "severity": "moderate"  # Could be enhanced with sentiment analysis
                })
        
        return factors[:5]
    
    def _extract_current_conditions(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Extract current conditions from results"""
        conditions = {}
        answer = results.get("answer") or ""
        
        if not answer:
            return conditions
        
        answer_lower = answer.lower()
        
        # Look for weather, health, safety mentions
        if "weather" in answer_lower:
            conditions["weather"] = "Check search results for current weather conditions"
        if "outbreak" in answer_lower or "disease" in answer_lower:
            conditions["health"] = "Health alerts detected - see details"
        if "accident" in answer_lower or "incident" in answer_lower:
            conditions["safety"] = "Safety incidents reported recently"
        
        return conditions
    
    def _generate_risk_recommendations(self, results: Dict[str, Any], activities: List[str]) -> List[str]:
        """Generate risk-based recommendations"""
        recommendations = []
        answer = results.get("answer") or ""
        
        if not answer:
            return ["Standard coverage recommended based on current conditions"]
        
        answer_lower = answer.lower()
        
        # Activity-specific recommendations
        if "skiing" in str(activities).lower() and ("accident" in answer_lower or "injury" in answer_lower):
            recommendations.append("Consider upgrading to premium medical coverage due to skiing risks")
        
        if "scuba" in str(activities).lower() or "diving" in str(activities).lower():
            recommendations.append("Ensure policy includes hyperbaric treatment coverage")
        
        # General recommendations based on findings
        if "expensive" in answer_lower or "high cost" in answer_lower:
            recommendations.append("Medical costs are high in this destination - recommend comprehensive coverage")
        
        if "outbreak" in answer_lower or "epidemic" in answer_lower:
            recommendations.append("Health outbreak detected - ensure medical evacuation coverage")
        
        return recommendations if recommendations else ["Standard coverage recommended based on current conditions"]
    
    def _extract_medical_costs(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Extract medical cost information"""
        costs = {}
        answer = results.get("answer") or ""
        
        if not answer:
            return costs
        
        # Simple pattern matching for costs
        # This could be enhanced with better NLP
        if "$" in answer or "USD" in answer or "dollar" in answer.lower():
            costs["note"] = "Medical costs information found in search results"
        
        return costs
    
    def _generate_coverage_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate coverage recommendations based on medical costs"""
        recommendations = []
        answer = results.get("answer") or ""
        
        if not answer:
            return ["Standard medical coverage should be sufficient"]
        
        answer_lower = answer.lower()
        
        if "expensive" in answer_lower or "high" in answer_lower:
            recommendations.append("Higher medical coverage recommended due to elevated costs")
        
        if "emergency" in answer_lower:
            recommendations.append("Ensure emergency evacuation coverage is included")
        
        return recommendations if recommendations else ["Standard medical coverage should be sufficient"]

