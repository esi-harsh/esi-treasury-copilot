import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_mcp():
    print("\n--- 1. Testing GET /api/v1/mcp ---")
    resp = client.get("/api/v1/mcp")
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["tool_count"] == 13

    print("\n--- 2. Testing MCP initialize ---")
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = client.post("/api/v1/mcp", json=init_payload)
    print(f"Status: {resp.status_code}")
    print(f"Result: {json.dumps(resp.json(), indent=2)}")
    assert resp.status_code == 200
    assert "protocolVersion" in resp.json()["result"]

    print("\n--- 3. Testing tools/list ---")
    tools_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = client.post("/api/v1/mcp", json=tools_payload)
    tools = resp.json()["result"]["tools"]
    print(f"Found {len(tools)} tools:")
    for t in tools:
        print(f"  - {t['name']}: {t['description'][:60]}...")
    assert len(tools) == 13

    print("\n--- 4. Testing tools/call: get_twin_state ---")
    call_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_twin_state",
            "arguments": {"currency_scope": "ALL", "days_ahead": 30}
        }
    }
    resp = client.post("/api/v1/mcp", json=call_payload)
    print(f"Response: {resp.json()['result']['content'][0]['text'][:300]}...")

    print("\n--- 5. Testing tools/call: evaluate_risk_limits ---")
    call_payload2 = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "evaluate_risk_limits",
            "arguments": {
                "counterparty_name": "RBC",
                "currency": "USD",
                "proposed_amount": 5000000
            }
        }
    }
    resp = client.post("/api/v1/mcp", json=call_payload2)
    print(f"Response: {resp.json()['result']['content'][0]['text']}")

    print("\n--- 6. Testing tools/call: run_lcr_stress_test ---")
    call_payload3 = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "run_lcr_stress_test",
            "arguments": {
                "outflow_multiplier": 1.25,
                "hqla_haircut_pct": 5.0
            }
        }
    }
    resp = client.post("/api/v1/mcp", json=call_payload3)
    print(f"Response: {resp.json()['result']['content'][0]['text']}")

    print("\n--- 7. Testing tools/call: apply_market_shock ---")
    call_payload4 = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "apply_market_shock",
            "arguments": {
                "rate_shift_bps": 50.0,
                "fx_shock_pct": 2.5,
                "currency_pair": "ALL"
            }
        }
    }
    resp = client.post("/api/v1/mcp", json=call_payload4)
    print(f"Response: {resp.json()['result']['content'][0]['text']}")

    print("\nALL MCP TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_mcp()
