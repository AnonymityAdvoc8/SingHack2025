"""
TravelMate AI - FastAPI Application
REST API wrapping the MCP Server
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db, init_db
from app.mcp.server import MCPServer
from app.schemas.trip import TripDetailsSchema, QuoteRequestSchema
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TravelMate AI API",
    description="Conversational AI Travel Insurance Platform",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests
class MCPRequestModel(BaseModel):
    type: str
    parameters: Dict[str, Any] = {}


class ComparisonRequest(BaseModel):
    policy_ids: List[str]
    comparison_criteria: Optional[List[str]] = None
    user_context: Optional[Dict[str, Any]] = None


class QuestionRequest(BaseModel):
    question: str
    policy_id: Optional[str] = None
    include_citations: bool = True


class EligibilityRequest(BaseModel):
    trip_details: TripDetailsSchema
    policy_id: Optional[str] = None


class ScenarioRequest(BaseModel):
    scenario_description: str
    trip_details: Optional[TripDetailsSchema] = None
    policy_ids: Optional[List[str]] = None


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("api_starting", port=settings.api_port)
    init_db()
    logger.info("api_started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("api_shutdown")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TravelMate AI",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "service": "TravelMate AI API",
        "description": "Conversational AI Travel Insurance Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "mcp": "/mcp",
            "compare": "/compare",
            "ask": "/ask",
            "eligibility": "/eligibility",
            "scenario": "/scenario",
            "quote": "/quote"
        }
    }


# MCP Protocol Endpoint
@app.post("/mcp")
async def mcp_endpoint(
    request: MCPRequestModel,
    db: Session = Depends(get_db)
):
    """
    Generic MCP protocol endpoint
    Handles all MCP requests
    """
    logger.info("mcp_api_request", type=request.type)
    
    mcp_server = MCPServer(db)
    response = mcp_server.handle_request(request.dict())
    
    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error"))
    
    return response


# Convenience REST endpoints
@app.post("/compare")
async def compare_policies(
    request: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple insurance policies
    
    Convenience endpoint that wraps MCP compare_policies tool
    """
    logger.info("api_compare", policies=len(request.policy_ids))
    
    mcp_server = MCPServer(db)
    result = mcp_server.tools.compare_policies(
        policy_ids=request.policy_ids,
        comparison_criteria=request.comparison_criteria,
        user_context=request.user_context
    )
    
    return result


@app.post("/ask")
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Answer policy questions with citations
    
    Convenience endpoint that wraps MCP answer_policy_question tool
    """
    logger.info("api_ask", question_length=len(request.question))
    
    mcp_server = MCPServer(db)
    result = mcp_server.tools.answer_policy_question(
        question=request.question,
        policy_id=request.policy_id,
        include_citations=request.include_citations
    )
    
    return result


@app.post("/eligibility")
async def check_eligibility(
    request: EligibilityRequest,
    db: Session = Depends(get_db)
):
    """
    Check user eligibility for policies
    
    Convenience endpoint that wraps MCP check_eligibility tool
    """
    logger.info("api_eligibility")
    
    mcp_server = MCPServer(db)
    result = mcp_server.tools.check_eligibility(
        trip_details=request.trip_details.dict(),
        policy_id=request.policy_id
    )
    
    return result


@app.post("/scenario")
async def analyze_scenario(
    request: ScenarioRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze what-if coverage scenarios
    
    Convenience endpoint that wraps MCP analyze_scenario tool
    """
    logger.info("api_scenario")
    
    mcp_server = MCPServer(db)
    
    trip_dict = request.trip_details.dict() if request.trip_details else None
    
    result = mcp_server.tools.analyze_scenario(
        scenario_description=request.scenario_description,
        trip_details=trip_dict,
        policy_ids=request.policy_ids
    )
    
    return result


@app.post("/quote")
async def get_quote(
    request: QuoteRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Generate insurance quotes
    
    Convenience endpoint that wraps MCP get_quote tool
    """
    logger.info("api_quote")
    
    mcp_server = MCPServer(db)
    result = mcp_server.tools.get_quote(
        trip_details=request.trip_details.dict(),
        policy_ids=request.policy_ids
    )
    
    return result


# List all policies endpoint
@app.get("/policies")
async def list_policies(db: Session = Depends(get_db)):
    """
    List all available policies
    
    Returns summary information about all policies
    """
    logger.info("api_list_policies")
    
    mcp_server = MCPServer(db)
    policies = mcp_server.resources.get_normalized_policies(None)
    
    # Return summary information
    summaries = []
    for policy in policies:
        summaries.append({
            "policy_id": policy.policy_id,
            "policy_name": policy.policy_name,
            "product_type": policy.product_type,
            "num_benefits": len(policy.benefits),
            "age_range": f"{policy.general_conditions.age_min}-{policy.general_conditions.age_max}" if policy.general_conditions else "N/A",
            "trip_duration_max": policy.general_conditions.trip_duration_max_days if policy.general_conditions else None
        })
    
    return {
        "total_policies": len(summaries),
        "policies": summaries
    }


# Get single policy details
@app.get("/policies/{policy_id}")
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific policy
    """
    logger.info("api_get_policy", policy_id=policy_id)
    
    mcp_server = MCPServer(db)
    policies = mcp_server.resources.get_normalized_policies([policy_id])
    
    if not policies:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    
    policy = policies[0]
    
    return {
        "policy_id": policy.policy_id,
        "policy_name": policy.policy_name,
        "product_type": policy.product_type,
        "version": policy.version,
        "general_conditions": policy.general_conditions.dict() if policy.general_conditions else None,
        "benefits": [b.dict() for b in policy.benefits],
        "operational_details": policy.operational_details.dict() if policy.operational_details else None
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.error("http_error", status=exc.status_code, detail=exc.detail)
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error("unhandled_error", error=str(exc))
    return {
        "success": False,
        "error": "Internal server error",
        "details": str(exc) if settings.environment == "development" else None
    }


# Entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )

