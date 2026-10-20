# SRE Runbook: High Error Rate & SLO Error Budget Burn

## Incident Metadata
- **Alert Names**: `ProcurePulseErrorBudgetBurnRateCritical`, `ProcurePulseErrorBudgetBurnRateWarning`
- **Severity**: P1 (Critical Page) / P2 (Warning Ticket)
- **Target SLO**: 99.9% Availability over 30 days (Allowed Error Budget: 0.1% or 43.2 minutes/month)
- **Burn Rates**:
  - `14.4x`: Consumes 2% of monthly error budget in 1 hour (Requires dual windows: 1h AND 5m)
  - `6.0x`: Consumes 5% of monthly error budget in 6 hours (Requires dual windows: 6h AND 30m)

---

## 1. Immediate Triage (< 5 Minutes)
1. **Acknowledge the Alert**: Claim the incident in your on-call paging tool.
2. **Verify System Readiness**:
   ```bash
   curl -i http://localhost:8000/readyz
   ```
   - If HTTP 200: Application and database are reachable; error is route-specific.
   - If HTTP 503: Downstream dependency (PostgreSQL) is offline or rejecting connections.
3. **Check Active Chaos Injections**:
   ```bash
   ./scripts/chaosctl.py status
   ```
   - Check if an authorized SRE Chaos Game Day is active (`sum(chaos_active_flag) > 0`).

---

## 2. Root Cause Analysis
- **Open Grafana RED Dashboard**: Navigate to `http://localhost:3000/d/procurepulse-sre`.
- **Identify Failing Route**: Examine the **"Error vs Success Rates"** panel to isolate which endpoint is throwing HTTP 5xx.
- **Inspect Application Logs**:
   ```bash
   docker compose logs --tail=100 -f app
   ```
- **Inspect Nginx Edge Proxy**:
   ```bash
   docker compose logs --tail=100 -f nginx
   ```

---

## 3. Mitigation & Remediation
### Scenario A: Authorized Game Day Fault
If chaos was injected and needs emergency termination:
```bash
./scripts/chaosctl.py reset
```

### Scenario B: Bad Code Deployment
If the error burst began immediately following a container update:
```bash
./scripts/rollback.sh
```

### Scenario C: PostgreSQL Crash or Saturation
Restart the database service and verify recovery:
```bash
docker compose restart db
./scripts/status.sh
```

---

## 4. Verification & Recovery
- Confirm `/readyz` returns HTTP 200.
- Confirm the 5-minute error ratio drops to 0%:
  ```promql
  job:http_error_ratio:rate5m
  ```
- Send resolution notification to the incident channel.
