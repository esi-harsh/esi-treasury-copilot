#!/usr/bin/env python
"""
Standard I/O (stdio) Model Context Protocol (MCP) Server for ESI Treasury.
Can be run directly by any MCP client using:
  python server/mcp_stdio.py
"""

import sys
import os
import json

# Ensure server path is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models import *  # noqa: F401,F403
from app.mcp.tools import MCP_TOOLS_CATALOG, execute_mcp_tool

# Ensure database tables exist
Base.metadata.create_all(bind=engine)


def handle_request(db, req_data: dict) -> dict:
    req_id = req_data.get("id")
    method = req_data.get("method")
    params = req_data.get("params", {}) or {}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False}
                },
                "serverInfo": {
                    "name": "esi-treasury-stdio-harness",
                    "version": "2.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "ok"}}

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS_CATALOG
            }
        }

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

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found"
            }
        }


def main():
    db = SessionLocal()
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req_data = json.loads(line)
                response = handle_request(db, req_data)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
    finally:
        db.close()


if __name__ == "__main__":
    main()
