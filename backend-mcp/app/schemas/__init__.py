"""Schemas package initialization"""

from app.schemas.policy import (
    PolicySchema,
    GeneralConditionSchema,
    BenefitSchema,
    OperationalDetailSchema,
    PolicyComparisonSchema,
    PolicyQuestionAnswerSchema
)
from app.schemas.trip import (
    TravelerSchema,
    TripDetailsSchema,
    EligibilityResultSchema,
    QuoteItemSchema,
    QuoteRequestSchema,
    QuoteResponseSchema
)

__all__ = [
    # Policy schemas
    "PolicySchema",
    "GeneralConditionSchema",
    "BenefitSchema",
    "OperationalDetailSchema",
    "PolicyComparisonSchema",
    "PolicyQuestionAnswerSchema",
    # Trip schemas
    "TravelerSchema",
    "TripDetailsSchema",
    "EligibilityResultSchema",
    "QuoteItemSchema",
    "QuoteRequestSchema",
    "QuoteResponseSchema"
]
