#!/usr/bin/env python3
"""Rapid end-to-end smoke test for Zycus ProcurePulse."""

import json
import sys
import urllib.error
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.read().decode("utf-8")


def main():
    print(f"[*] Running smoke tests against: {BASE_URL}")

    # 1. Health check
    status, body = request("GET", "/healthz")
    assert status == 200, f"Healthz failed: {status}"
    print("  [✓] /healthz is UP")

    # 2. Readiness check
    status, body = request("GET", "/readyz")
    assert status == 200, f"Readyz failed: {status}"
    print("  [✓] /readyz is READY")

    # 3. Create requisition
    req_payload = {
        "title": "Smoke Test Procure Requisition",
        "requester_name": "Smoke Tester",
        "requester_email": "smoke@zycus.com",
        "department": "Engineering",
        "currency": "USD",
        "priority": "HIGH",
        "line_items": [
            {
                "item_description": "Load Testing Cluster",
                "category": "Cloud Infrastructure",
                "quantity": 2,
                "unit_price": 450.0,
                "supplier_name": "CloudCorp",
            }
        ],
    }
    status, body = request("POST", "/api/v1/requisitions/", req_payload)
    assert status == 201, f"Create requisition failed: {status}"
    data = json.loads(body)
    req_id = data["id"]
    print(f"  [✓] Created requisition #{req_id} ({data['req_number']}) - Total: ${data['total_amount']}")

    # 4. Submit requisition
    status, body = request("POST", f"/api/v1/requisitions/{req_id}/submit")
    assert status == 200, f"Submit failed: {status}"
    print(f"  [✓] Submitted requisition #{req_id}")

    # 5. Approve requisition
    approval_payload = {
        "approver_name": "Chief Procurement Officer",
        "approver_role": "CPO",
        "decision": "APPROVED",
        "comments": "Approved via automated smoke verification.",
    }
    status, body = request("POST", f"/api/v1/requisitions/{req_id}/approve", approval_payload)
    assert status == 200, f"Approval failed: {status}"
    print(f"  [✓] Approved requisition #{req_id}")

    # 6. Spend analytics
    status, body = request("GET", "/api/v1/analytics/spend")
    assert status == 200, f"Spend analytics failed: {status}"
    analytics = json.loads(body)
    print(f"  [✓] Analytics spend total: ${analytics['total_spend_usd']}")

    # 7. Prometheus Metrics
    status, body = request("GET", "/metrics")
    assert status == 200, f"Metrics scrape failed: {status}"
    assert "http_requests_total" in body
    print("  [✓] Prometheus /metrics scraped successfully")

    print("\n[SUCCESS] All smoke tests passed!")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[FAIL] Smoke test failure: {exc}")
        sys.exit(1)
