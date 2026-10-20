# SRE Runbook: Database Connection Exhaustion & Dropout

## Incident Metadata
- **Alert Name**: `ProcurePulseDatabaseErrors`
- **Severity**: P1 (Critical Page)
- **Subsystem**: PostgreSQL Connection Pool & AsyncPG Driver

---

## 1. Symptoms & Diagnostic Indicators
- Prometheus Gauge: `db_pool_checked_out == db_pool_size`
- Application logs reporting: `TimeoutError: QueuePool limit of size 20 overflow 10 reached`
- `/readyz` probe returning `HTTP 503 Service Unavailable` with message: `"connection timeout"`

---

## 2. Immediate Diagnostic Actions
1. **Check PostgreSQL container status**:
   ```bash
   docker exec -it procurepulse_db pg_isready -U zycus_user -d procurepulse
   ```
2. **Inspect active connection count directly in PostgreSQL**:
   ```bash
   docker exec -it procurepulse_db psql -U zycus_user -d procurepulse -c "
     SELECT count(*), state FROM pg_stat_activity GROUP BY state;
   "
   ```
3. **Identify long-running blocking queries**:
   ```bash
   docker exec -it procurepulse_db psql -U zycus_user -d procurepulse -c "
     SELECT pid, now() - query_start AS duration, query 
     FROM pg_stat_activity 
     WHERE state != 'idle' 
     ORDER BY duration DESC LIMIT 5;
   "
   ```

---

## 3. Mitigation Steps
- **Terminate Stuck Queries**:
  ```sql
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > interval '30 seconds';
  ```
- **Scale Pool Configuration**:
  Edit `.env` to temporarily increase `DB_MAX_OVERFLOW=20` and restart the app:
  ```bash
  docker compose restart app
  ```
- **If complete deadlock or database crash**:
  ```bash
  docker compose restart db
  ```
