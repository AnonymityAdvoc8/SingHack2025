"""
TravelMate AI - MCP Prompts Layer
Conversational templates for natural language generation
"""

from typing import Dict, Any, List, Optional


class MCPPrompts:
    """MCP Prompts Layer - Templates for conversational responses"""
    
    @staticmethod
    def comparison_prompt_template(
        policies: List[str],
        comparison_result: Dict[str, Any]
    ) -> str:
        """Generate natural language comparison response"""
        
        template = f"""
I've compared {len(policies)} insurance policies for you. Here's what I found:

{comparison_result.get('recommendation', 'All policies have been analyzed.')}

Key Differences:
"""
        
        # Add specific comparisons
        if "benefits_comparison" in comparison_result.get("comparison_matrix", {}):
            template += "\n📋 Coverage Comparison:\n"
            benefits = comparison_result["comparison_matrix"]["benefits_comparison"]
            for benefit_name, policy_data in list(benefits.items())[:5]:
                template += f"  • {benefit_name}:\n"
                for policy_id, data in policy_data.items():
                    if data.get("coverage_limit"):
                        template += f"    - {data['policy_name']}: ${data['coverage_limit']:,.0f}\n"
        
        template += "\nWould you like me to explain any specific aspect in more detail?"
        
        return template
    
    @staticmethod
    def explanation_prompt_template(
        answer: str,
        citations: List[str],
        confidence: float
    ) -> str:
        """Generate natural language explanation response"""
        
        template = answer
        
        if citations:
            template += "\n\n📚 Sources:\n"
            for citation in citations:
                template += f"  • {citation}\n"
        
        if confidence < 0.7:
            template += "\n\n⚠️ Note: I recommend verifying this information with the full policy document or contacting the insurer directly for critical decisions."
        
        return template
    
    @staticmethod
    def recommendation_prompt_template(
        recommended_policy: str,
        rationale: str,
        quote_data: Dict[str, Any]
    ) -> str:
        """Generate policy recommendation response"""
        
        template = f"""
Based on your trip details, I recommend: **{recommended_policy}**

{rationale}

💰 **Pricing Summary:**
"""
        
        if "quotes" in quote_data:
            for quote in quote_data["quotes"]:
                if quote.get("is_eligible"):
                    template += f"\n  {quote['policy_name']}: ${quote['premium']:.2f} SGD"
                    if quote['policy_id'] == quote_data.get("recommended_policy_id"):
                        template += " ⭐ (Recommended)"
        
        template += "\n\nWould you like to proceed with purchasing this policy?"
        
        return template
    
    @staticmethod
    def eligibility_prompt_template(
        eligibility_results: List[Dict[str, Any]]
    ) -> str:
        """Generate eligibility check response"""
        
        eligible_count = sum(1 for r in eligibility_results if r.get("is_eligible"))
        
        if eligible_count == 0:
            template = "⚠️ Unfortunately, none of the policies meet your eligibility requirements.\n\n"
            template += "Reasons:\n"
            for result in eligibility_results:
                if result.get("reasons"):
                    template += f"\n{result['policy_name']}:\n"
                    for reason in result["reasons"]:
                        template += f"  • {reason}\n"
            
            template += "\nWould you like me to suggest alternatives or explain these requirements?"
        else:
            template = f"✅ Good news! You're eligible for {eligible_count} polic{'y' if eligible_count == 1 else 'ies'}:\n\n"
            
            for result in eligibility_results:
                if result.get("is_eligible"):
                    template += f"• {result['policy_name']}\n"
                    if result.get("warnings"):
                        template += "  Warnings:\n"
                        for warning in result["warnings"]:
                            template += f"    - {warning}\n"
            
            template += "\nWould you like me to generate quotes for these policies?"
        
        return template
    
    @staticmethod
    def quote_prompt_template(
        quote_response: Dict[str, Any]
    ) -> str:
        """Generate quote response"""
        
        template = "📊 **Insurance Quotes for Your Trip**\n\n"
        
        trip = quote_response.get("trip_details", {})
        template += f"Destination: {trip.get('destination_country')}\n"
        template += f"Duration: {trip.get('trip_duration_days')} days\n"
        template += f"Travelers: {len(trip.get('travelers', []))}\n\n"
        
        template += "**Available Quotes:**\n\n"
        
        quotes = quote_response.get("quotes", [])
        for quote in quotes:
            if quote.get("is_eligible"):
                template += f"💼 **{quote['policy_name']}**: ${quote['premium']:.2f} SGD\n"
                
                summary = quote.get("coverage_summary", {})
                template += f"   • Medical Coverage: ${summary.get('medical_coverage', 0):,.0f}\n"
                template += f"   • Total Benefits: {summary.get('total_benefits', 0)}\n"
                
                if quote.get("policy_id") == quote_response.get("recommended_policy_id"):
                    template += "   ⭐ **Recommended for your trip**\n"
                
                template += "\n"
        
        if quote_response.get("recommendation_rationale"):
            template += f"\n💡 **Recommendation:**\n{quote_response['recommendation_rationale']}\n"
        
        template += f"\n📅 This quote is valid until {quote_response.get('expires_at', 'N/A')}"
        template += "\n\nReady to purchase? I can help you complete the payment securely."
        
        return template
    
    @staticmethod
    def error_prompt_template(
        error_type: str,
        error_message: str
    ) -> str:
        """Generate user-friendly error message"""
        
        templates = {
            "not_found": "I couldn't find the information you're looking for. Could you provide more details?",
            "invalid_input": f"I had trouble understanding that. {error_message}",
            "service_error": "I'm experiencing technical difficulties. Please try again in a moment.",
            "unauthorized": "You don't have permission to perform this action.",
        }
        
        return templates.get(error_type, f"An error occurred: {error_message}")
    
    @staticmethod
    def greeting_prompt() -> str:
        """Generate greeting message"""
        return """👋 Hello! I'm your TravelMate AI assistant.

I can help you with:
• Finding the right travel insurance policy
• Comparing coverage options
• Answering questions about policies
• Getting instant quotes
• Completing your purchase

Where are you planning to travel?"""
    
    @staticmethod
    def followup_questions_prompt(context: str) -> List[str]:
        """Generate relevant follow-up questions"""
        
        # Simple rule-based follow-ups
        questions = [
            "Would you like to see a detailed comparison?",
            "Do you have any questions about the coverage?",
            "Would you like me to generate a quote?",
        ]
        
        if "eligible" in context.lower():
            questions.append("Ready to purchase?")
        
        if "medical" in context.lower():
            questions.append("Do you have any pre-existing medical conditions we should know about?")
        
        return questions[:3]  # Return top 3

