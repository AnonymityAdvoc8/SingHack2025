"""
OpenAI-compatible Chat Completions API
Provides a standard OpenAI format interface to TravelMate AI
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import json
import time
import uuid
from datetime import datetime


class ChatMessage(BaseModel):
    """OpenAI-compatible chat message"""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name for the message sender")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    model: str = Field(default="travelmate-ai", description="Model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    stream: bool = Field(default=False, description="Whether to stream responses")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatCompletionChoice(BaseModel):
    """OpenAI-compatible choice object"""
    index: int
    message: ChatMessage
    finish_reason: str  # stop, length, content_filter, null


class ChatCompletionUsage(BaseModel):
    """OpenAI-compatible usage statistics"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = "travelmate-ai"
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str = "travelmate-ai"
    choices: List[Dict[str, Any]]


def convert_to_ask_format(request: ChatCompletionRequest) -> Dict[str, Any]:
    """
    Convert OpenAI format to our internal /ask format
    
    Args:
        request: OpenAI-compatible request
        
    Returns:
        Dict compatible with /ask endpoint
    """
    # Extract the last user message as the question
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    question = user_messages[-1].content
    
    # Build context from previous messages (conversation history)
    context = {}
    if len(request.messages) > 1:
        context["conversation_history"] = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages[:-1]  # All except last message
        ]
    
    return {
        "question": question,
        "session_id": request.session_id,
        "context": context
    }


def convert_from_ask_format(
    ask_response: Dict[str, Any],
    request_id: str,
    model: str = "travelmate-ai"
) -> ChatCompletionResponse:
    """
    Convert our internal /ask response to OpenAI format
    
    Args:
        ask_response: Response from /ask endpoint
        request_id: Unique request ID
        model: Model name
        
    Returns:
        OpenAI-compatible response
    """
    # Extract the answer
    answer = ask_response.get("answer", "I apologize, but I couldn't generate a response.")
    
    # Estimate token counts (rough approximation)
    prompt_tokens = sum(len(msg.get("content", "").split()) for msg in ask_response.get("context", {}).get("conversation_history", []))
    completion_tokens = len(answer.split())
    
    # Create OpenAI-compatible response
    return ChatCompletionResponse(
        id=request_id,
        model=model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=answer
                ),
                finish_reason="stop"
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=max(prompt_tokens, 10),
            completion_tokens=completion_tokens,
            total_tokens=max(prompt_tokens, 10) + completion_tokens
        )
    )


def stream_response_chunks(
    answer: str,
    request_id: str,
    model: str = "travelmate-ai"
):
    """
    Stream response in OpenAI SSE (Server-Sent Events) format
    
    NOTE: This is a synchronous generator for FastAPI StreamingResponse compatibility
    
    Args:
        answer: The full answer to stream
        request_id: Unique request ID
        model: Model name
        
    Yields:
        SSE-formatted chunks
    """
    import time as time_module
    
    created = int(time.time())
    
    # Split answer into chunks (words for smooth streaming)
    words = answer.split()
    
    if not words:
        # Empty response, send a single chunk
        chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=model,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        )
        yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    # Send chunks
    for i, word in enumerate(words):
        try:
            chunk = ChatCompletionChunk(
                id=request_id,
                created=created,
                model=model,
                choices=[{
                    "index": 0,
                    "delta": {
                        "content": word + " " if i < len(words) - 1 else word
                    },
                    "finish_reason": None
                }]
            )
            
            # Format as SSE
            yield f"data: {chunk.model_dump_json()}\n\n"
            
            # Small delay for realistic streaming
            time_module.sleep(0.05)
        except Exception as e:
            # Log error but continue
            import structlog
            logger = structlog.get_logger()
            logger.error("streaming_chunk_error", error=str(e), word=word)
    
    # Send final chunk with finish_reason
    try:
        final_chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=model,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.error("streaming_final_chunk_error", error=str(e))
    
    # Send [DONE] marker
    yield "data: [DONE]\n\n"


def create_error_response(error: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create OpenAI-compatible error response
    
    Args:
        error: Error message
        status_code: HTTP status code
        
    Returns:
        OpenAI-compatible error dict
    """
    return {
        "error": {
            "message": error,
            "type": "invalid_request_error" if status_code == 400 else "server_error",
            "code": status_code
        }
    }

