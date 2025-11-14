"""
TravelMate AI - Question Answering Service
Real LLM-powered Q&A with policy citations using Groq
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from groq import Groq
from app.config import get_settings
from app.mcp.resources import MCPResources
from app.schemas.policy import PolicyQuestionAnswerSchema
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class QuestionAnsweringService:
    """Service for answering policy questions with citations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.resources = MCPResources(db)
        self.groq_client = Groq(api_key=settings.groq_api_key)
    
    def answer_question(
        self,
        question: str,
        policy_id: Optional[str] = None,
        include_citations: bool = True
    ) -> PolicyQuestionAnswerSchema:
        """
        Answer policy question using LLM with real policy data
        
        Args:
            question: User's question
            policy_id: Specific policy to query, or None for all
            include_citations: Whether to include policy text citations
            
        Returns:
            Answer with citations and confidence score
        """
        logger.info("answer_question", question=question, policy_id=policy_id)
        
        # Get relevant policies
        policy_ids = [policy_id] if policy_id else None
        policies = self.resources.get_normalized_policies(policy_ids)
        
        if not policies:
            return PolicyQuestionAnswerSchema(
                question=question,
                answer="No policies found to answer your question.",
                citations=[],
                confidence=0.0,
                related_policies=[]
            )
        
        # Get original text for citations
        policy_texts = {}
        for policy in policies:
            text_data = self.resources.get_original_policy_text(policy.policy_id)
            policy_texts[policy.policy_id] = text_data.get("text", "")
        
        # Build context for LLM
        context = self._build_context(policies, policy_texts)
        
        # Generate answer using Groq
        answer_data = self._generate_answer_with_llm(question, context, policies)
        
        return answer_data
    
    def _build_context(
        self,
        policies: List[Any],
        policy_texts: Dict[str, str]
    ) -> str:
        """Build comprehensive context from policies"""
        
        context_parts = []
        
        for policy in policies:
            context_parts.append(f"\n{'='*60}")
            context_parts.append(f"POLICY: {policy.policy_name} (ID: {policy.policy_id})")
            context_parts.append(f"{'='*60}")
            
            # General Conditions
            if policy.general_conditions:
                gc = policy.general_conditions
                context_parts.append("\nGENERAL CONDITIONS:")
                context_parts.append(f"- Age: {gc.age_min}-{gc.age_max} years")
                context_parts.append(f"- Trip duration: {gc.trip_duration_min_days}-{gc.trip_duration_max_days} days")
                context_parts.append(f"- Pre-existing conditions covered: {gc.pre_existing_covered}")
                if gc.high_risk_activities_excluded:
                    context_parts.append(f"- Excluded activities: {', '.join(gc.high_risk_activities_excluded[:5])}")
            
            # Benefits
            context_parts.append(f"\nBENEFITS ({len(policy.benefits)} total):")
            for benefit in policy.benefits[:10]:  # Limit to first 10 for context
                limit_str = f"${benefit.coverage_limit:,.0f}" if benefit.coverage_limit else "Covered"
                context_parts.append(f"- {benefit.benefit_name}: {limit_str} {benefit.currency}")
            
            if len(policy.benefits) > 10:
                context_parts.append(f"  ... and {len(policy.benefits) - 10} more benefits")
            
            # Operational
            if policy.operational_details:
                od = policy.operational_details
                context_parts.append("\nOPERATIONAL DETAILS:")
                context_parts.append(f"- Deductible: ${od.deductible_amount}")
                context_parts.append(f"- Co-pay: {od.copay_percentage}%")
                if od.emergency_hotline:
                    context_parts.append(f"- Emergency: {od.emergency_hotline}")
            
            # Add excerpt from original text for citations
            original_text = policy_texts.get(policy.policy_id, "")
            if original_text:
                excerpt = original_text[:2000]  # First 2000 chars
                context_parts.append(f"\nORIGINAL POLICY EXCERPT:\n{excerpt}...")
        
        return "\n".join(context_parts)
    
    def _generate_answer_with_llm(
        self,
        question: str,
        context: str,
        policies: List[Any]
    ) -> PolicyQuestionAnswerSchema:
        """Generate answer using Groq LLM"""
        
        prompt = f"""You are a friendly, helpful insurance advisor. Answer the user's question based on the provided policy information.

IMPORTANT RULES:
1. Be CONCISE and CONVERSATIONAL - keep answers short (2-4 sentences max)
2. Get straight to the point - no lengthy explanations
3. For comparison questions: Focus ONLY on the key difference
4. Skip formal citations like "(TravelEasy Standard policy, Page 1)" - just mention the policy name naturally
5. Don't repeat the question back to the user
6. No "References" section at the end
7. Use simple, clear language

POLICY INFORMATION:
{context}

USER QUESTION: {question}

Provide a SHORT, conversational answer (2-4 sentences):"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a friendly insurance advisor. Keep answers SHORT and conversational - 2-4 sentences max."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for factual accuracy
                max_tokens=300  # Reduced from 1500 to enforce brevity
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Remove any "References:" or "Sources:" sections that the LLM might add
            answer = answer.split("References:")[0].strip()
            answer = answer.split("Sources:")[0].strip()
            answer = answer.replace("---", "").strip()
            
            # Extract citations (simple implementation - find policy names mentioned)
            citations = []
            for policy in policies:
                if policy.policy_name.lower() in answer.lower():
                    citations.append(policy.policy_name)
            
            # Confidence based on whether we found relevant info
            confidence = 0.9 if citations else 0.6
            
            logger.info("answer_generated", question_length=len(question), answer_length=len(answer))
            
            return PolicyQuestionAnswerSchema(
                question=question,
                answer=answer,
                citations=citations,
                confidence=confidence,
                related_policies=[p.policy_id for p in policies]
            )
            
        except Exception as e:
            logger.error("llm_answer_failed", error=str(e))
            
            # Fallback answer
            return PolicyQuestionAnswerSchema(
                question=question,
                answer=f"I apologize, but I'm having trouble processing your question right now. Please try rephrasing or contact support. Error: {str(e)}",
                citations=[],
                confidence=0.0,
                related_policies=[p.policy_id for p in policies]
            )

