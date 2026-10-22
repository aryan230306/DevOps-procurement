"""Unit and integration tests for procurement requisition APIs."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_and_readiness(client: AsyncClient):
    # Test Liveness Probe
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert "version" in data

    # Test Readiness Probe
    ready_resp = await client.get("/readyz")
    assert ready_resp.status_code == 200
    ready_data = ready_resp.json()
    assert ready_data["ready"] is True
    assert ready_data["database"]["connected"] is True


@pytest.mark.asyncio
async def test_create_and_fetch_requisition(client: AsyncClient):
    payload = {
        "title": "Cloud Infrastructure Compute Nodes",
        "description": "Quarterly cloud scaling for production Kubernetes cluster",
        "requester_name": "Aryan DevOps",
        "requester_email": "aryan@example.com",
        "department": "Infrastructure",
        "currency": "USD",
        "priority": "HIGH",
        "line_items": [
            {
                "item_description": "c6g.4xlarge AWS EC2 Reserved Instances",
                "category": "Cloud Infrastructure",
                "quantity": 4,
                "unit_price": 500.0,
                "supplier_name": "Amazon Web Services",
            },
            {
                "item_description": "Datadog Observability Licenses",
                "category": "Software Licenses",
                "quantity": 10,
                "unit_price": 75.0,
                "supplier_name": "Datadog Inc.",
            },
        ],
    }

    # Expected total: 4 * 500 + 10 * 75 = 2000 + 750 = 2750.0
    res = await client.post("/api/v1/requisitions/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["total_amount"] == 2750.0
    assert data["status"] == "DRAFT"
    assert data["req_number"].startswith("PR-")
    assert len(data["line_items"]) == 2
    req_id = data["id"]

    # Fetch by ID
    get_res = await client.get(f"/api/v1/requisitions/{req_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == payload["title"]

    # List requisitions
    list_res = await client.get("/api/v1/requisitions/?department=Infrastructure")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["id"] == req_id for item in items)


@pytest.mark.asyncio
async def test_requisition_approval_workflow(client: AsyncClient):
    # 1. Create requisition
    create_payload = {
        "title": "TechCorp AI Sourcing License Renewal",
        "requester_name": "Jane Doe",
        "requester_email": "jane@example.com",
        "department": "Procurement",
        "currency": "USD",
        "priority": "URGENT",
        "line_items": [
            {
                "item_description": "Enterprise Sourcing Enterprise Tier",
                "category": "Software Licenses",
                "quantity": 1,
                "unit_price": 12000.0,
                "supplier_name": "Acme Corp",
            }
        ],
    }
    create_res = await client.post("/api/v1/requisitions/", json=create_payload)
    assert create_res.status_code == 201
    req_id = create_res.json()["id"]

    # 2. Cannot approve while still DRAFT
    approve_attempt = await client.post(
        f"/api/v1/requisitions/{req_id}/approve",
        json={
            "approver_name": "VP Finance",
            "approver_role": "VP",
            "decision": "APPROVED",
            "comments": "Too early",
        },
    )
    assert approve_attempt.status_code == 400

    # 3. Submit requisition
    submit_res = await client.post(f"/api/v1/requisitions/{req_id}/submit")
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "SUBMITTED"

    # 4. Approve requisition
    approve_res = await client.post(
        f"/api/v1/requisitions/{req_id}/approve",
        json={
            "approver_name": "Sarah Connor",
            "approver_role": "Head of Finance",
            "decision": "APPROVED",
            "comments": "Approved within Q4 capital budget limit.",
        },
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["status"] == "APPROVED"
    assert len(approved_data["approvals"]) == 1
    assert approved_data["approvals"][0]["decision"] == "APPROVED"
    assert approved_data["approvals"][0]["approver_name"] == "Sarah Connor"


@pytest.mark.asyncio
async def test_spend_analytics_endpoint(client: AsyncClient):
    # Create two requisitions in different departments
    req1 = {
        "title": "Laptop Fleet Upgrade",
        "requester_name": "IT Admin",
        "requester_email": "it@example.com",
        "department": "IT Operations",
        "currency": "USD",
        "line_items": [
            {
                "item_description": "MacBook Pro M3",
                "category": "Hardware",
                "quantity": 2,
                "unit_price": 2500.0,
                "supplier_name": "Apple Inc.",
            }
        ],
    }
    await client.post("/api/v1/requisitions/", json=req1)

    analytics_res = await client.get("/api/v1/analytics/spend")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_requisition_count"] >= 1
    assert analytics_data["total_spend_usd"] >= 5000.0
    assert any(
        d["department"] == "IT Operations" for d in analytics_data["department_spend"]
    )


def test_dashboard_does_not_emit_unreachable_monitoring_links():
    from app.main import _dashboard_html

    dashboard = _dashboard_html()

    assert "http://localhost:3000" not in dashboard
    assert "http://localhost:9090" not in dashboard
    assert "http://localhost:9093" not in dashboard
    assert "http://localhost:9999" not in dashboard


def test_dashboard_marks_failed_requests_instead_of_leaving_loading_state():
    from app.ui import DASHBOARD_HTML

    assert "if (!resp.ok) throw new Error(`Requisitions request failed" in DASHBOARD_HTML
    assert "Unable to load requisitions." in DASHBOARD_HTML
    assert "UNAVAILABLE" in DASHBOARD_HTML
