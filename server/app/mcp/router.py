import json
import asyncio
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.mcp.tools import MCP_TOOLS_CATALOG, execute_mcp_tool

router = APIRouter(prefix="", tags=["Model Context Protocol (MCP)"])

# Keep active SSE streams and queues
_sse_sessions: Dict[str, asyncio.Queue] = {}


def _handle_jsonrpc_request(db: Session, req_data: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Processes a single JSON-RPC 2.0 MCP request."""
    req_id = req_data.get("id")
    method = req_data.get("method")
    params = req_data.get("params", {}) or {}

    # 1. Ping
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    # 2. Initialize
    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    },
                    "resources": {
                        "subscribe": False,
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "esi-treasury-harness",
                    "version": "2.0.0"
                }
            }
        }

    # 3. Initialized notification
    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "ok"}}

    # 4. Tools List
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS_CATALOG
            }
        }

    # 5. Tools Call
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {}) or {}
        
        result_data = execute_mcp_tool(db, tool_name, tool_args)
        is_error = "error" in result_data and result_data.get("status") != "success"
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_data, indent=2, default=str)
                    }
                ],
                "isError": is_error
            }
        }

    # 6. Resources List
    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "resources": [
                    {
                        "uri": "treasury://state/positions",
                        "name": "Live Currency Positions",
                        "mimeType": "application/json",
                        "description": "Real-time net spot and forward positions across all currencies"
                    },
                    {
                        "uri": "treasury://state/limits",
                        "name": "Counterparty Credit Limits",
                        "mimeType": "application/json",
                        "description": "Active counterparty limits, utilized amounts, and available headroom"
                    }
                ]
            }
        }

    # 7. Resources Read
    elif method == "resources/read":
        uri = params.get("uri")
        if uri == "treasury://state/positions":
            data = execute_mcp_tool(db, "get_positions", {})
        elif uri == "treasury://state/limits":
            data = execute_mcp_tool(db, "get_twin_state", {})
        else:
            data = {"error": f"Resource not found: {uri}"}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(data, indent=2, default=str)
                    }
                ]
            }
        }

    # Unknown Method
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found"
            }
        }


# --- HTTP Stream / POST JSON-RPC Endpoint ---

@router.post("/mcp")
@router.post("/api/v1/mcp")
async def mcp_post_endpoint(request: Request, db: Session = Depends(get_db)):
    """Standard HTTP JSON-RPC 2.0 endpoint for MCP queries."""
    try:
        req_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Handle batch or single
    if isinstance(req_data, list):
        results = [_handle_jsonrpc_request(db, item) for item in req_data]
        return results
    elif isinstance(req_data, dict):
        result = _handle_jsonrpc_request(db, req_data)
        return result
    else:
        raise HTTPException(status_code=400, detail="Expected JSON-RPC object or array")


@router.get("/mcp")
@router.get("/api/v1/mcp")
def mcp_get_endpoint():
    """Information endpoint verifying MCP server status and tool count."""
    return {
        "status": "online",
        "service": "Treasury Harness Engine MCP Server",
        "protocol": "Model Context Protocol (MCP) JSON-RPC 2.0",
        "endpoints": {
            "http_jsonrpc": "/api/v1/mcp",
            "sse_stream": "/api/v1/mcp/sse",
            "sse_messages": "/api/v1/mcp/messages"
        },
        "tool_count": len(MCP_TOOLS_CATALOG),
        "tools": [t["name"] for t in MCP_TOOLS_CATALOG]
    }


# --- Server-Sent Events (SSE) Transport ---

@router.get("/mcp/sse")
@router.get("/api/v1/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    """SSE endpoint for streaming MCP connections."""
    session_id = uuid.uuid4().hex
    queue: asyncio.Queue = asyncio.Queue()
    _sse_sessions[session_id] = queue

    async def event_generator():
        try:
            # Send initial endpoint event
            endpoint_url = f"/api/v1/mcp/messages?sessionId={session_id}"
            yield f"event: endpoint\ndata: {endpoint_url}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Wait for message in session queue
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: message\ndata: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive comment
                    yield ": ping\n\n"
        finally:
            _sse_sessions.pop(session_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/mcp/messages")
@router.post("/api/v1/mcp/messages")
async def mcp_sse_message_endpoint(request: Request, sessionId: Optional[str] = None, db: Session = Depends(get_db)):
    """Receives JSON-RPC messages from clients connected via SSE."""
    session_id = sessionId or request.query_params.get("sessionId")
    try:
        req_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    response_data = _handle_jsonrpc_request(db, req_data, session_id=session_id)

    if session_id and session_id in _sse_sessions:
        await _sse_sessions[session_id].put(response_data)
        return Response(status_code=202)
    else:
        return response_data
