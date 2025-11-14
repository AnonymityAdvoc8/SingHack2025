"""
TravelMate AI - Taxonomy Service
Loads and uses the populated Taxonomy_Hackathon.json for policy recommendations
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TaxonomyService:
    """Service for accessing populated taxonomy data for policy recommendations"""
    
    def __init__(self):
        self.taxonomy_data = self._load_taxonomy()
        self.products = self.taxonomy_data.get("products", [])
        logger.info("taxonomy_service_initialized", products=len(self.products))
    
    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load the populated taxonomy JSON"""
        try:
            with open(settings.taxonomy_file, 'r') as f:
                data = json.load(f)
            logger.info("taxonomy_loaded_successfully", 
                       file=str(settings.taxonomy_file),
                       products=len(data.get("products", [])))
            return data
        except Exception as e:
            logger.error("failed_to_load_taxonomy", error=str(e))
            return {"products": [], "layers": {}}
    
    def get_all_products(self) -> List[str]:
        """Get list of all product keys (Product A, Product B, Product C)"""
        return self.products
    
    def get_product_data(self, product_key: str) -> Dict[str, Any]:
        """
        Get all data for a specific product across all layers
        
        Args:
            product_key: "Product A", "Product B", or "Product C"
            
        Returns:
            Complete product data from all 3 layers
        """
        if product_key not in self.products:
            logger.warning("product_not_found", product=product_key)
            return {}
        
        result = {
            "product_key": product_key,
            "layer_1_conditions": self._get_layer_1_for_product(product_key),
            "layer_2_benefits": self._get_layer_2_for_product(product_key),
            "layer_3_benefit_conditions": self._get_layer_3_for_product(product_key)
        }
        
        return result
    
    def _get_layer_1_for_product(self, product_key: str) -> List[Dict[str, Any]]:
        """Get Layer 1 general conditions for a product"""
        layer_1 = self.taxonomy_data.get("layers", {}).get("layer_1_general_conditions", [])
        
        result = []
        for condition in layer_1:
            product_data = condition.get("products", {}).get(product_key, {})
            if product_data.get("condition_exist"):
                result.append({
                    "condition": condition["condition"],
                    "condition_type": condition["condition_type"],
                    "original_text": product_data.get("original_text", ""),
                    "parameters": product_data.get("parameters", {})
                })
        
        return result
    
    def _get_layer_2_for_product(self, product_key: str) -> List[Dict[str, Any]]:
        """Get Layer 2 benefits for a product"""
        layer_2 = self.taxonomy_data.get("layers", {}).get("layer_2_benefits", [])
        
        result = []
        for benefit in layer_2:
            product_data = benefit.get("products", {}).get(product_key, {})
            if product_data.get("condition_exist"):
                result.append({
                    "benefit_name": benefit["benefit_name"],
                    "parameters": product_data.get("parameters", {})
                })
        
        return result
    
    def _get_layer_3_for_product(self, product_key: str) -> List[Dict[str, Any]]:
        """Get Layer 3 benefit-specific conditions for a product"""
        layer_3 = self.taxonomy_data.get("layers", {}).get("layer_3_benefit_specific_conditions", [])
        
        result = []
        for condition in layer_3:
            products_data = condition.get("products", {})
            if product_key in products_data:
                product_data = products_data[product_key]
                if product_data.get("condition_exist"):
                    result.append({
                        "benefit_name": condition["benefit_name"],
                        "condition": condition["condition"],
                        "condition_type": condition["condition_type"],
                        "original_text": product_data.get("original_text", ""),
                        "parameters": product_data.get("parameters", {})
                    })
        
        return result
    
    def check_eligibility(self, product_key: str, trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a product is eligible for the given trip details
        
        Args:
            product_key: Product to check
            trip_details: User's trip information
            
        Returns:
            Eligibility result with reasons
        """
        # Debug logging
        activities_value = trip_details.get("activities") or trip_details.get("planned_activities", [])
        logger.info("taxonomy_eligibility_check_started",
                   product=product_key,
                   trip_keys=list(trip_details.keys()),
                   has_travelers=bool(trip_details.get("travelers")),
                   activities=activities_value,
                   departure=trip_details.get("departure_location") or trip_details.get("departure_city") or "not_found")
        
        if product_key not in self.products:
            return {
                "is_eligible": False,
                "product_key": product_key,
                "reasons": ["Product not found in taxonomy"]
            }
        
        layer_1_conditions = self._get_layer_1_for_product(product_key)
        logger.info("layer_1_conditions_loaded", product=product_key, count=len(layer_1_conditions))
        
        is_eligible = True
        reasons = []
        
        # Check age eligibility
        for condition in layer_1_conditions:
            if condition["condition"] == "age_eligibility":
                params = condition.get("parameters", {})
                min_age = params.get("min_age")
                max_age = params.get("max_age")
                
                # Get traveler ages from trip_details
                travelers = trip_details.get("travelers", [])
                for traveler in travelers:
                    age = traveler.get("age")
                    if age:
                        if min_age and age < min_age:
                            is_eligible = False
                            reasons.append(f"Traveler age {age} below minimum {min_age}")
                        if max_age and age > max_age:
                            is_eligible = False
                            reasons.append(f"Traveler age {age} above maximum {max_age}")
            
            # Check trip start location
            elif condition["condition"] == "trip_start_singapore":
                params = condition.get("parameters", {})
                required_departure = params.get("departure_location")
                # Handle multiple possible field names
                actual_departure = (
                    trip_details.get("departure_location") or 
                    trip_details.get("departure_city") or 
                    trip_details.get("origin") or
                    "Singapore"  # Default assumption for Singapore-based system
                )
                
                if required_departure and actual_departure:
                    if required_departure.lower() not in actual_departure.lower():
                        is_eligible = False
                        reasons.append(f"Trip must start from {required_departure}")
            
            # Check pre-existing conditions
            elif condition["condition"] == "pre_existing_conditions":
                travelers = trip_details.get("travelers", [])
                has_pre_existing = any(t.get("has_pre_existing_conditions") for t in travelers)
                
                if has_pre_existing:
                    # This product requires declaration
                    reasons.append("Pre-existing condition declaration required")
            
            # Check high-risk activities
            elif condition["condition"] == "dangerous_activities_exclusion":
                # Handle both 'activities' and 'planned_activities' keys
                activities = trip_details.get("activities") or trip_details.get("planned_activities", [])
                params = condition.get("parameters", {})
                excluded = params.get("excluded_activities", [])
                
                for activity in activities:
                    if activity.lower() in [e.lower() for e in excluded]:
                        is_eligible = False
                        reasons.append(f"Activity '{activity}' is excluded")
        
        if is_eligible and not reasons:
            reasons.append("Meets all eligibility requirements")
        
        result = {
            "is_eligible": is_eligible,
            "product_key": product_key,
            "reasons": reasons
        }
        
        logger.info("taxonomy_eligibility_check_complete",
                   product=product_key,
                   is_eligible=is_eligible,
                   reason_count=len(reasons),
                   reasons=reasons[:3] if not is_eligible else ["eligible"])
        
        return result
    
    def get_benefit_coverage(self, product_key: str, benefit_name: str) -> Optional[Dict[str, Any]]:
        """
        Get coverage details for a specific benefit
        
        Args:
            product_key: Product to check
            benefit_name: Name of benefit
            
        Returns:
            Coverage details or None if not covered
        """
        layer_2 = self.taxonomy_data.get("layers", {}).get("layer_2_benefits", [])
        
        for benefit in layer_2:
            if benefit["benefit_name"] == benefit_name:
                product_data = benefit.get("products", {}).get(product_key, {})
                if product_data.get("condition_exist"):
                    return product_data.get("parameters", {})
        
        return None
    
    def compare_products(self, product_keys: List[str], trip_details: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Compare multiple products across all layers
        
        Args:
            product_keys: List of products to compare
            trip_details: Optional trip details for eligibility check
            
        Returns:
            Comparison matrix with recommendation
        """
        logger.info("taxonomy_compare_products_started",
                   product_count=len(product_keys),
                   has_trip_details=bool(trip_details))
        
        comparison = {
            "products": {},
            "eligibility": {},
            "benefits_comparison": {},
            "recommendation": None
        }
        
        # Check eligibility for each product
        for product_key in product_keys:
            if product_key not in self.products:
                logger.warning("product_not_in_taxonomy", product=product_key)
                continue
            
            product_data = self.get_product_data(product_key)
            comparison["products"][product_key] = product_data
            
            if trip_details:
                eligibility = self.check_eligibility(product_key, trip_details)
                comparison["eligibility"][product_key] = eligibility
        
        # Compare benefit coverage
        all_benefits = set()
        for product_key in product_keys:
            benefits = self._get_layer_2_for_product(product_key)
            all_benefits.update(b["benefit_name"] for b in benefits)
        
        for benefit_name in all_benefits:
            comparison["benefits_comparison"][benefit_name] = {}
            for product_key in product_keys:
                coverage = self.get_benefit_coverage(product_key, benefit_name)
                comparison["benefits_comparison"][benefit_name][product_key] = coverage
        
        # Simple recommendation based on eligibility and coverage
        eligible_products = [
            k for k, v in comparison["eligibility"].items()
            if v.get("is_eligible", False)
        ] if trip_details else product_keys
        
        logger.info("taxonomy_eligible_products_determined",
                   eligible_count=len(eligible_products),
                   eligible_list=eligible_products)
        
        if eligible_products:
            # Recommend product with most benefits
            best_product = max(
                eligible_products,
                key=lambda p: len(self._get_layer_2_for_product(p))
            )
            comparison["recommendation"] = best_product
            logger.info("taxonomy_recommendation_made", recommendation=best_product)
        else:
            logger.warning("no_eligible_products_found")
        
        return comparison
    
    def get_product_summary(self, product_key: str) -> str:
        """
        Get a human-readable summary of a product
        
        Args:
            product_key: Product to summarize
            
        Returns:
            Natural language summary
        """
        if product_key not in self.products:
            return f"Product {product_key} not found."
        
        product_data = self.get_product_data(product_key)
        
        # Count benefits
        benefit_count = len(product_data.get("layer_2_benefits", []))
        
        # Get key coverage amounts
        benefits = product_data.get("layer_2_benefits", [])
        medical_coverage = None
        trip_cancel_coverage = None
        
        for benefit in benefits:
            if benefit["benefit_name"] == "overseas_medical_expenses":
                medical_coverage = benefit.get("parameters", {}).get("coverage_limit")
            elif benefit["benefit_name"] == "trip_cancellation":
                trip_cancel_coverage = benefit.get("parameters", {}).get("coverage_limit")
        
        # Build summary
        summary_parts = [f"{product_key} offers {benefit_count} benefits"]
        
        if medical_coverage:
            summary_parts.append(f"up to ${medical_coverage:,} for medical expenses")
        
        if trip_cancel_coverage:
            summary_parts.append(f"${trip_cancel_coverage:,} for trip cancellation")
        
        return ", ".join(summary_parts) + "."


# Singleton instance
_taxonomy_service = None

def get_taxonomy_service() -> TaxonomyService:
    """Get singleton taxonomy service instance"""
    global _taxonomy_service
    if _taxonomy_service is None:
        _taxonomy_service = TaxonomyService()
    return _taxonomy_service

