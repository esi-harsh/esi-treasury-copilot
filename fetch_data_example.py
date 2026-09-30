"""
ESI Treasury MCP Client - Localhost Data Fetching Example

Usage:
  1. Start the server:
     uvicorn main:app --reload --port 8000 (inside server directory)
  2. Run this script:
     python fetch_data_example.py
"""

import requests
import json

MCP_URL = "http://localhost:8000/api/v1/mcp"

def call_mcp_tool(tool_name: str, arguments: dict = None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    response = requests.post(MCP_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    if "result" in data and "content" in data["result"]:
        raw_text = data["result"]["content"][0]["text"]
        return json.loads(raw_text)
    return data

def list_mcp_tools():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    response = requests.post(MCP_URL, json=payload)
    response.raise_for_status()
    return response.json()["result"]["tools"]

if __name__ == "__main__":
    print("==================================================")
    print(" ESI Treasury MCP Localhost Client")
    print("==================================================")
    
    # 1. List tools
    print("\n[1] Discovering Available Tools via tools/list...")
    tools = list_mcp_tools()
    print(f"Total Tools: {len(tools)}")
    for t in tools:
        print(f"  • {t['name']}: {t['description'][:70]}...")

    # 2. Fetch Twin State
    print("\n[2] Fetching Treasury State via 'get_twin_state'...")
    state = call_mcp_tool("get_twin_state", {"currency_scope": "USD", "days_ahead": 14})
    print("Nostro Accounts:", json.dumps(state.get("nostro_vostro_accounts", []), indent=2))
    print("Net Positions:", json.dumps(state.get("net_positions", []), indent=2))

    # 3. Evaluate Risk Limits
    print("\n[3] Evaluating Counterparty Limit via 'evaluate_risk_limits'...")
    limit_res = call_mcp_tool("evaluate_risk_limits", {
        "counterparty_name": "RBC",
        "currency": "USD",
        "proposed_amount": 5000000
    })
    print(json.dumps(limit_res, indent=2))

    # 4. Run LCR Stress Test
    print("\n[4] Running Basel III LCR Stress Test via 'run_lcr_stress_test'...")
    lcr_res = call_mcp_tool("run_lcr_stress_test", {
        "outflow_multiplier": 1.25,
        "hqla_haircut_pct": 5.0
    })
    print(json.dumps(lcr_res, indent=2))
