"""Tests for Prometheus metrics exposition and instrumentation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_scraping(client: AsyncClient):
    # Perform a few requests to populate metrics
    await client.get("/healthz")
    await client.get("/api/v1/requisitions/")

    # Scrape metrics endpoint
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]

    body = res.text

    # Verify RED metrics exist
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "http_requests_in_flight" in body

    # Verify procurement domain metrics exist
    assert "procurement_requisitions_created_total" in body
    assert "procurement_requisition_value_total" in body
    assert "procurement_requisitions_by_state" in body

    # Verify chaos metrics exist
    assert "chaos_faults_injected_total" in body
    assert "chaos_active_flag" in body
