"""Services package initialization

Note: Services are NOT auto-imported to avoid circular dependencies.
Import services directly from their modules:
    from app.services.comparison_service import PolicyComparisonService
"""

# No automatic imports to prevent circular dependency issues
# Each service should be imported explicitly where needed

__all__ = [
    "PolicyComparisonService",
    "EligibilityService",
    "QuestionAnsweringService",
    "QuoteService",
    "TavilyIntelligenceService",
    "ConversationalExtractionService",
    "ConversationOrchestrator"
]
