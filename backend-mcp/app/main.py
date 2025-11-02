"""
TravelMate AI - FastAPI Application
REST API wrapping the MCP Server
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db, init_db
from app.mcp.server import MCPServer
from app.schemas.trip import TripDetailsSchema, QuoteRequestSchema
from app.utils.logger import get_logger
from app.api.openai_compat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    convert_to_ask_format,
    convert_from_ask_format,
    stream_response_chunks,
    create_error_response
)

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
    session_id: Optional[str] = None  # NEW: For conversation continuity
    context: Optional[Dict[str, Any]] = None  # NEW: For conversation state


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
@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    Handle OAuth callback from Google
    User is redirected here after authorizing Gmail access
    """
    logger.info("oauth_callback_received", state=state)
    
    try:
        from app.services.gmail_oauth import get_gmail_oauth_service
        oauth_service = get_gmail_oauth_service()  # Use singleton
        
        credentials = oauth_service.handle_oauth_callback(code, state)
        
        if credentials:
            # Store credentials in session for later use
            from app.services.session_store import get_session_store
            session_store = get_session_store()
            
            # Load existing session
            session_data = session_store.load_session(state) or {}
            
            # Store credentials token (not the whole object, just what we need)
            session_data["gmail_authorized"] = True
            session_data["gmail_token"] = credentials.token
            session_data["gmail_refresh_token"] = credentials.refresh_token
            
            # Save back
            session_store.save_session(
                session_id=state,
                conversation_history=session_data.get("conversation_history", []),
                extracted_trip_details=session_data.get("extracted_trip_details", {}),
                trip_context=session_data.get("trip_context", {}),
                gmail_authorized=True
            )
            
            logger.info("gmail_credentials_stored_in_session", session=state)
            
            # Auto-trigger Gmail scan now that we're authorized
            logger.info("gmail_auth_success_auto_scanning", session=state)
            
            # Get Gmail agent and scan
            from app.services.gmail_agent import GmailAgent
            from app.database import get_db
            
            gmail_agent = GmailAgent()
            bookings = await gmail_agent.search_for_bookings(credentials=credentials, use_mock=False)
            
            # Store results in session for retrieval
            session_data["gmail_scan_results"] = [
                {
                    "email_id": b.email_id,
                    "subject": b.subject,
                    "booking_type": b.booking_type,
                    "extracted_data": b.extracted_data
                }
                for b in bookings
            ]
            
            session_store.save_session(
                session_id=state,
                conversation_history=session_data.get("conversation_history", []),
                extracted_trip_details=session_data.get("extracted_trip_details", {}),
                trip_context=session_data.get("trip_context", {}),
                gmail_authorized=True,
                gmail_scan_results=session_data["gmail_scan_results"]  # CRITICAL: Save scan results
            )
            
            # Show results immediately
            formatted_bookings = gmail_agent.format_bookings_for_display(bookings)
            
            html_response = f"""
            <html>
            <head><title>Gmail Authorized</title></head>
            <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: white;">
                <h2>✅ Gmail Authorized!</h2>
                <p>I found {len(bookings)} booking(s) in your email.</p>
                <div style="background: #2a2a2a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <pre style="white-space: pre-wrap;">{formatted_bookings}</pre>
                </div>
                <p><strong>Close this window and return to the chat - your bookings are ready!</strong></p>
                <script>
                    // Auto-close after 3 seconds
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
            """
            
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_response)
        else:
            return {
                "success": False,
                "error": "Failed to authorize Gmail"
            }
    
    except Exception as e:
        logger.error("oauth_callback_error", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


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
    Intelligent conversational endpoint with automatic Tavily integration
    
    **NEW in Phase 3:**
    - Automatically extracts trip details from conversation
    - Triggers Tavily for real-time destination intelligence
    - Provides personalized policy recommendations with real-time insights
    - Handles multi-turn conversations with context
    
    **Usage:**
    - Simple questions: "What does medical evacuation cover?"
    - Recommendations: "I'm 31 travelling to Japan for hiking, which policy?"
    - Follow-ups: Maintains context across multiple messages
    """
    logger.info("api_ask", question_length=len(request.question))
    
    # Import here to avoid circular dependency
    from app.services.orchestration_service import ConversationOrchestrator
    
    # Use orchestrator for intelligent routing
    orchestrator = ConversationOrchestrator(db)
    result = await orchestrator.handle_message(
        message=request.question,
        session_id=request.session_id,
        context=request.context
    )
    
    # Add metadata for API response
    result["api_version"] = "2.0"
    result["features_used"] = []
    
    # Track which features were used
    if result.get("real_time_intelligence"):
        result["features_used"].append("tavily_intelligence")
    if result.get("trip_details"):
        result["features_used"].append("conversational_extraction")
    if result.get("policy_recommendations"):
        result["features_used"].append("policy_matching")
    
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


# =============================================================================
# OpenAI-Compatible Chat Completions API
# =============================================================================

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db)
):
    """
    OpenAI-compatible Chat Completions endpoint
    
    Supports both streaming and non-streaming responses.
    Compatible with OpenAI SDKs, Claude Desktop, and other tools.
    
    **Example (Non-streaming)**:
    ```json
    {
      "model": "travelmate-ai",
      "messages": [
        {"role": "user", "content": "I need insurance for Japan trip"}
      ],
      "stream": false
    }
    ```
    
    **Example (Streaming)**:
    ```json
    {
      "model": "travelmate-ai",
      "messages": [
        {"role": "user", "content": "I need insurance for Japan trip"}
      ],
      "stream": true
    }
    ```
    """
    logger.info(
        "openai_chat_completions",
        model=request.model,
        messages=len(request.messages),
        stream=request.stream
    )
    
    try:
        # Convert OpenAI format to our internal format
        ask_request = convert_to_ask_format(request)
        
        # Import here to avoid circular dependency
        from app.services.orchestration_service import ConversationOrchestrator
        
        # Use orchestrator for intelligent routing
        orchestrator = ConversationOrchestrator(db)
        ask_response = await orchestrator.handle_message(
            message=ask_request["question"],
            session_id=ask_request.get("session_id"),
            context=ask_request.get("context")
        )
        
        # Generate unique request ID
        import uuid
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        
        # Handle streaming vs non-streaming
        if request.stream:
            logger.info("openai_streaming_response", request_id=request_id)
            
            try:
                # Extract answer for streaming
                answer = ask_response.get("answer", "I couldn't generate a response.")
                
                logger.info("openai_streaming_answer_extracted", length=len(answer))
                
                # Return SSE stream
                return StreamingResponse(
                    stream_response_chunks(answer, request_id, request.model),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no"  # Disable nginx buffering
                    }
                )
            except Exception as stream_err:
                logger.error("openai_streaming_error", error=str(stream_err), traceback=True)
                raise HTTPException(
                    status_code=500,
                    detail={"error": f"Streaming failed: {str(stream_err)}"}
                )
        else:
            logger.info("openai_complete_response", request_id=request_id)
            
            # Convert to OpenAI format
            response = convert_from_ask_format(ask_response, request_id, request.model)
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("openai_chat_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=create_error_response(str(e), 500)
        )


@app.get("/v1/models")
async def list_models():
    """
    OpenAI-compatible models list endpoint
    Returns available TravelMate AI models
    """
    import time
    
    return {
        "object": "list",
        "data": [
            {
                "id": "travelmate-ai",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "travelmate",
                "permission": [],
                "root": "travelmate-ai",
                "parent": None
            }
        ]
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

