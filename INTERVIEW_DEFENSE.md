# Interview Defense Guide: Zycus ProcurePulse

This document equips you with comprehensive, highly defensible answers to technical, architectural, and SRE questions during an interview at **Zycus** or any top-tier enterprise platform engineering company.

---

## 1. The 60-Second Elevator Pitch
> *"I built **Zycus ProcurePulse**, an enterprise procurement requisition and purchase order lifecycle service designed around the core business domains Zycus handles—purchase requisitions, spend analysis, approval hierarchies, and budget compliance. Rather than just building a CRUD API, I treated it as a mission-critical financial backend: implementing strict ACID transaction semantics, Google SRE Multi-Window Multi-Burn-Rate alerting against a 99.9% 30-day availability SLO, an in-process chaos engineering engine for automated Game Days, and a zero-downtime deployment pipeline with automated rollback."*

---

## 2. Domain & Company Alignment (Why Zycus?)
**Q: Why choose the Procurement Requisition domain instead of a generic e-commerce store or blog engine?**
- **Answer**: 
  - *"In B2B enterprise SaaS like Zycus's Cognitive Sourcing and Procure-to-Pay suites, procurement workflows are mission-critical. Requisitions represent legally binding financial commitments with multi-tiered approval policies, department budget allocations, and compliance audit trails.*
  - *Generic CRUD apps don't handle state machines (Draft -> Submitted -> Approved/Rejected -> Ordered), line item price rollups, or spend aggregation by department. By building directly in this domain, I demonstrate that I understand enterprise data modeling, business compliance, and how system reliability directly impacts our customer's procurement operations."*

---

## 3. SRE & Observability Deep Dives

**Q: Explain how your Multi-Window Multi-Burn-Rate alerts work and why static threshold alerts fail.**
- **Answer**:
  - *"Static threshold alerts (like `error_rate > 1% for 5 minutes`) suffer from two fatal flaws in production:
    1. **Alert Fatigue**: A 10-second blip caused by a network retry can trigger a page, waking an engineer at 3 AM for a self-healed issue.
    2. **Undetected Catastrophic Drains**: A low, constant error rate of 0.8% will never trigger a 1% threshold, yet it will drain 80% of a 99.9% error budget over a month.
  - *To solve this, I implemented Google's SRE Workbook standard: **Multi-Window Multi-Burn-Rate Alerting**.
    - For our 99.9% availability SLO, the allowed monthly error budget is $0.1\%$ ($1 - 0.999$).
    - A **14.4x burn rate** means we are burning 2% of our monthly error budget in a single hour. If unaddressed, the entire budget is gone in 50 hours.
    - We use a **dual-window rule**: The alert fires **only** if the error ratio exceeds 14.4x across a 1-hour window (high precision/statistical significance) **AND** across a 5-minute window (ensuring the outage is active right now and hasn't already resolved).
    - This eliminates false positive pages and provides mathematically sound incident detection."*

**Q: How did you prevent Prometheus cardinality explosion?**
- **Answer**:
  - *"Prometheus metric cardinality is determined by the Cartesian product of label values. In REST APIs, including dynamic path parameters like `/api/v1/requisitions/124` directly in metric labels causes cardinality to explode to millions of series, exhausting Prometheus memory.
  - In `app/main.py`, I implemented a custom ASGI middleware that dynamically normalizes parameterized URL routes before recording latency histograms or request counters—mapping `/api/v1/requisitions/124` to `/api/v1/requisitions/{id}`. This keeps label cardinality bounded and predictable regardless of how many millions of requisitions are processed."*

**Q: What is the difference between `/healthz` and `/readyz`, and why does it matter?**
- **Answer**:
  - *"`/healthz` is a **Liveness Probe**: It verifies whether the Python process event loop is alive. It does NOT touch the database. If this fails, the orchestrator (Kubernetes or Docker) kills and restarts the container.
  - *"`/readyz` is a **Readiness Probe**: It verifies whether downstream dependencies (PostgreSQL connection pool, network latency) are healthy. If PostgreSQL is temporarily offline or saturated, `/readyz` returns HTTP 503. The orchestrator removes the pod from the load balancer routing pool without killing the process, giving the database time to recover without cascading restarts."*

---

## 4. Architecture & Engineering Decisions

**Q: Why FastAPI over Django or Flask?**
- **Answer**:
  - *"FastAPI natively supports modern Python asynchronous I/O (`async/await`) and integrates with Pydantic v2 for compile-time and runtime type validation. In a procurement service handling concurrent requisitions, asynchronous database queries via `asyncpg` ensure worker threads aren't blocked during database I/O, yielding superior throughput and lower p95 latency under high concurrency."*

**Q: How did you design database connection pooling for resilience?**
- **Answer**:
  - *"We use SQLAlchemy's async engine with an `asyncpg` connection pool configured with:
    - `pool_size=20`: Baseline persistent database connections.
    - `max_overflow=10`: Allows temporary bursts during peak procurement approval cycles.
    - `pool_recycle=1800`: Automatically recycles connections every 30 minutes to prevent stale TCP drops across AWS NAT gateways.
    - `pool_pre_ping=True`: Tests connection liveness with a lightweight `SELECT 1` ping before handing it to a worker, preventing errors from broken connections.
    - We also instrumented the pool state directly into Prometheus (`db_pool_checked_out`), allowing SREs to alert before pool exhaustion occurs."*

**Q: Walk me through what happens during your Chaos Game Day.**
- **Answer**:
  - *"During the Game Day (`scripts/gameday.sh`):
    1. We launch continuous procurement user journeys using `loadgen.py` to establish a healthy baseline (0% errors, <100ms latency).
    2. We inject a 60% HTTP 500 error burst using our in-process chaos controller (`scripts/chaosctl.py error`).
    3. We watch the Prometheus multi-burn-rate recording rules compute the error ratio. Within seconds, the 14.4x burn rate threshold is crossed.
    4. Alertmanager groups the alerts and dispatches a critical page notification to our webhook sink.
    5. We execute automated remediation (`chaosctl.py reset` or `./scripts/rollback.sh`), returning the system to 100% healthy traffic, verifying that the burn rate returns to zero and `/readyz` confirms full recovery."*
