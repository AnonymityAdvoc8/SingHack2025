"""
TravelMate AI - MCP Server Core
Implements the Model Context Protocol server
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.mcp.resources import MCPResources
from app.mcp.tools import MCPTools
from app.mcp.prompts import MCPPrompts
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    """Main MCP Server - Coordinates resources, tools, and prompts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.resources = MCPResources(db)
        self.tools = MCPTools(db)
        self.prompts = MCPPrompts()
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP requests
        
        Args:
            request: MCP request with type and parameters
            
        Returns:
            MCP response
        """
        request_type = request.get("type")
        params = request.get("parameters", {})
        
        logger.info("mcp_request", type=request_type)
        
        try:
            if request_type == "list_resources":
                return self._handle_list_resources()
            
            elif request_type == "get_resource":
                return self._handle_get_resource(params)
            
            elif request_type == "list_tools":
                return self._handle_list_tools()
            
            elif request_type == "call_tool":
                return self._handle_call_tool(params)
            
            elif request_type == "get_prompt":
                return self._handle_get_prompt(params)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}"
                }
        
        except Exception as e:
            logger.error("mcp_request_failed", type=request_type, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_list_resources(self) -> Dict[str, Any]:
        """List available MCP resources"""
        return {
            "success": True,
            "resources": [
                {
                    "id": "normalized_policies",
                    "name": "Normalized Policies",
                    "description": "Structured policy data for algorithmic processing",
                    "type": "json"
                },
                {
                    "id": "original_policy_text",
                    "name": "Original Policy Text",
                    "description": "Raw policy language for citations",
                    "type": "text"
                },
                {
                    "id": "user_session",
                    "name": "User Session",
                    "description": "Conversation context and history",
                    "type": "json"
                },
                {
                    "id": "taxonomy_schema",
                    "name": "Taxonomy Schema",
                    "description": "4-layer taxonomy structure",
                    "type": "json"
                }
            ]
        }
    
    def _handle_get_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific resource data"""
        resource_id = params.get("resource_id")
        resource_params = params.get("params", {})
        
        if resource_id == "normalized_policies":
            policy_ids = resource_params.get("policy_ids")
            data = self.resources.get_normalized_policies(policy_ids)
            return {
                "success": True,
                "resource_id": resource_id,
                "data": [p.dict() for p in data]
            }
        
        elif resource_id == "original_policy_text":
            policy_id = resource_params.get("policy_id")
            section = resource_params.get("section")
            data = self.resources.get_original_policy_text(policy_id, section)
            return {
                "success": True,
                "resource_id": resource_id,
                "data": data
            }
        
        elif resource_id == "user_session":
            session_id = resource_params.get("session_id")
            data = self.resources.get_user_session(session_id)
            return {
                "success": True,
                "resource_id": resource_id,
                "data": data
            }
        
        elif resource_id == "taxonomy_schema":
            data = self.resources.get_taxonomy_schema()
            return {
                "success": True,
                "resource_id": resource_id,
                "data": data
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown resource: {resource_id}"
            }
    
    def _handle_list_tools(self) -> Dict[str, Any]:
        """List available MCP tools"""
        return {
            "success": True,
            "tools": [
                {
                    "id": "compare_policies",
                    "name": "Compare Policies",
                    "description": "Multi-dimensional policy comparison",
                    "parameters": ["policy_ids", "comparison_criteria", "user_context"]
                },
                {
                    "id": "answer_policy_question",
                    "name": "Answer Policy Question",
                    "description": "Answer questions with citations",
                    "parameters": ["question", "policy_id", "include_citations"]
                },
                {
                    "id": "check_eligibility",
                    "name": "Check Eligibility",
                    "description": "Verify user eligibility for policies",
                    "parameters": ["trip_details", "policy_id"]
                },
                {
                    "id": "analyze_scenario",
                    "name": "Analyze Scenario",
                    "description": "What-if coverage analysis",
                    "parameters": ["scenario_description", "trip_details", "policy_ids"]
                },
                {
                    "id": "get_quote",
                    "name": "Get Quote",
                    "description": "Generate insurance quotes",
                    "parameters": ["trip_details", "policy_ids"]
                },
                {
                    "id": "purchase_policy",
                    "name": "Purchase Policy",
                    "description": "Initiate policy purchase (Phase 4)",
                    "parameters": ["quote_id", "selected_policy_id", "user_id"]
                },
                {
                    "id": "check_payment_status",
                    "name": "Check Payment Status",
                    "description": "Monitor payment status (Phase 4)",
                    "parameters": ["payment_intent_id"]
                },
                {
                    "id": "analyze_trip_risk",
                    "name": "Analyze Trip Risk",
                    "description": "Claims-based risk analysis (Phase 5)",
                    "parameters": ["trip_details"]
                }
            ]
        }
    
    def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with parameters"""
        tool_id = params.get("tool_id")
        tool_params = params.get("params", {})
        
        try:
            if tool_id == "compare_policies":
                result = self.tools.compare_policies(**tool_params)
            
            elif tool_id == "answer_policy_question":
                result = self.tools.answer_policy_question(**tool_params)
            
            elif tool_id == "check_eligibility":
                result = self.tools.check_eligibility(**tool_params)
            
            elif tool_id == "analyze_scenario":
                result = self.tools.analyze_scenario(**tool_params)
            
            elif tool_id == "get_quote":
                result = self.tools.get_quote(**tool_params)
            
            elif tool_id == "purchase_policy":
                result = self.tools.purchase_policy(**tool_params)
            
            elif tool_id == "check_payment_status":
                result = self.tools.check_payment_status(**tool_params)
            
            elif tool_id == "analyze_trip_risk":
                result = self.tools.analyze_trip_risk(**tool_params)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_id}"
                }
            
            return {
                "success": True,
                "tool_id": tool_id,
                "result": result
            }
        
        except Exception as e:
            logger.error("tool_execution_failed", tool_id=tool_id, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversational prompt template"""
        prompt_type = params.get("prompt_type")
        prompt_params = params.get("params", {})
        
        if prompt_type == "greeting":
            text = self.prompts.greeting_prompt()
        
        elif prompt_type == "comparison":
            text = self.prompts.comparison_prompt_template(**prompt_params)
        
        elif prompt_type == "explanation":
            text = self.prompts.explanation_prompt_template(**prompt_params)
        
        elif prompt_type == "recommendation":
            text = self.prompts.recommendation_prompt_template(**prompt_params)
        
        elif prompt_type == "eligibility":
            text = self.prompts.eligibility_prompt_template(**prompt_params)
        
        elif prompt_type == "quote":
            text = self.prompts.quote_prompt_template(**prompt_params)
        
        elif prompt_type == "error":
            text = self.prompts.error_prompt_template(**prompt_params)
        
        else:
            return {
                "success": False,
                "error": f"Unknown prompt type: {prompt_type}"
            }
        
        return {
            "success": True,
            "prompt_type": prompt_type,
            "text": text
        }

