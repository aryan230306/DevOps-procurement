# SRE Runbook: High Latency & p95 Response Time Degradation

## Incident Metadata
- **Alert Name**: `ProcurePulseHighLatencyP95`
- **Severity**: P2 (Warning Ticket)
- **Target SLA**: 95% of all HTTP requests served in < 300ms

---

## 1. Triage & Identification
1. **Open Grafana Latency Distribution Panel**:
   - Compare p50, p95, and p99 timeseries.
   - If p50 is 10ms but p95 is 500ms -> tail-latency issue (e.g. unindexed search or lock contention).
   - If p50 is uniformly elevated (>300ms) -> CPU throttling, upstream network saturation, or connection pool starvation.
2. **Check Host CPU and Memory**:
   - Open Node Exporter dashboard or run:
     ```bash
     docker stats
     ```

---

## 2. Mitigation Steps
- Check if synthetic latency chaos fault is armed:
  ```bash
  ./scripts/chaosctl.py status
  ```
- If unindexed query on requisitions table:
  - Add database index on `department` or `created_at`.
- Enable Nginx response caching for read-heavy endpoints like `/api/v1/analytics/spend`.
