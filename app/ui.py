"""Mission Control UI for Zycus ProcurePulse."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zycus ProcurePulse — Enterprise SRE & Procurement Mission Control</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(18, 24, 38, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover: rgba(255, 255, 255, 0.12);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.25);
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.25);
      --warning: #f59e0b;
      --danger: #ef4444;
      --danger-glow: rgba(239, 68, 68, 0.3);
      --purple: #a855f7;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: radial-gradient(circle at 10% 20%, #0d1527 0%, var(--bg) 90%);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }

    header {
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      padding: 1rem 2rem;
      position: sticky;
      top: 0;
      z-index: 50;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-logo {
      width: 34px;
      height: 34px;
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      color: white;
      box-shadow: 0 0 15px var(--primary-glow);
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-badge {
      font-size: 0.65rem;
      text-transform: uppercase;
      padding: 0.2rem 0.5rem;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 9999px;
      font-weight: 600;
      letter-spacing: 0.05em;
    }

    .nav-links {
      display: flex;
      gap: 0.75rem;
    }
    .nav-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 0.45rem 0.85rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 500;
      text-decoration: none;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .nav-btn:hover {
      background: rgba(255, 255, 255, 0.1);
      color: var(--text);
      border-color: var(--card-hover);
      transform: translateY(-1px);
    }

    .container {
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem 2rem;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* Live Status Bar */
    .status-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
      justify-content: space-between;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 0.85rem 1.25rem;
      backdrop-filter: blur(16px);
    }
    .status-pills {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.78rem;
      padding: 0.3rem 0.7rem;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
    }
    .pill-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }
    .pill-dot.green { background: var(--success); box-shadow: 0 0 8px var(--success-glow); }
    .pill-dot.red { background: var(--danger); box-shadow: 0 0 8px var(--danger-glow); }
    .pill-dot.amber { background: var(--warning); }

    /* Top Metric Stat Cards */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.2rem;
      backdrop-filter: blur(16px);
      transition: transform 0.2s ease, border-color 0.2s ease;
      position: relative;
      overflow: hidden;
    }
    .stat-card:hover {
      border-color: var(--card-hover);
      transform: translateY(-2px);
    }
    .stat-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; width: 4px; height: 100%;
      background: var(--primary);
    }
    .stat-card.emerald::before { background: var(--success); }
    .stat-card.purple::before { background: var(--purple); }
    .stat-card.amber::before { background: var(--warning); }

    .stat-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.4rem;
    }
    .stat-value {
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--text);
      font-family: 'JetBrains Mono', monospace;
    }
    .stat-sub {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.35rem;
    }

    /* Main Split Layout */
    .main-grid {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 1024px) {
      .main-grid { grid-template-columns: 1fr; }
    }

    .panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.4rem;
      backdrop-filter: blur(16px);
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      padding-bottom: 0.8rem;
    }
    .panel-title {
      font-size: 0.95rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    /* Buttons */
    .btn {
      background: var(--primary);
      color: #030712;
      border: none;
      padding: 0.55rem 1rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .btn:hover {
      opacity: 0.9;
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text);
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.15);
      border-color: var(--card-hover);
    }
    .btn-danger {
      background: var(--danger);
      color: white;
    }
    .btn-success {
      background: var(--success);
      color: white;
    }

    /* Table */
    .table-container {
      overflow-x: auto;
      max-height: 400px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }
    th {
      text-align: left;
      padding: 0.6rem 0.75rem;
      color: var(--text-muted);
      border-bottom: 1px solid var(--card-border);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.7rem;
    }
    td {
      padding: 0.75rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    tr:hover td {
      background: rgba(255, 255, 255, 0.02);
    }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
    }
    .badge.DRAFT { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; }
    .badge.SUBMITTED { background: rgba(245, 158, 11, 0.2); color: #fcd34d; }
    .badge.APPROVED { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
    .badge.REJECTED { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }

    /* Chaos Controls */
    .chaos-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1rem;
    }
    .chaos-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }
    .chaos-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      font-size: 0.88rem;
    }
    .chaos-desc {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .chaos-inputs {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      margin-top: 0.3rem;
    }
    .chaos-inputs input[type="range"] {
      flex: 1;
      accent-color: var(--primary);
    }
    .chaos-val {
      font-size: 0.78rem;
      font-family: 'JetBrains Mono', monospace;
      min-width: 45px;
      text-align: right;
    }

    /* Live Log Console */
    .console {
      background: #050811;
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: #38bdf8;
      height: 160px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }
    .console-line { opacity: 0.9; }

    /* Toast Notification */
    #toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid var(--primary);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px var(--primary-glow);
      padding: 0.85rem 1.25rem;
      border-radius: 8px;
      color: white;
      font-size: 0.85rem;
      z-index: 100;
      display: none;
      align-items: center;
      gap: 0.5rem;
      backdrop-filter: blur(8px);
    }

    footer {
      border-top: 1px solid var(--card-border);
      padding: 1rem 2rem;
      text-align: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">Z</div>
      <div class="brand-title">ProcurePulse</div>
      <div class="brand-badge">SRE Mission Control</div>
    </div>
    <div class="nav-links">
      <a href="/docs" target="_blank" class="nav-btn">📖 Swagger API</a>
      <a href="http://localhost:3000" target="_blank" class="nav-btn">📊 Grafana</a>
      <a href="http://localhost:9090" target="_blank" class="nav-btn">🔥 Prometheus</a>
      <a href="http://localhost:9093" target="_blank" class="nav-btn">🔔 Alertmanager</a>
      <a href="http://localhost:9999/alerts" target="_blank" class="nav-btn">📥 Alert Sink</a>
    </div>
  </header>

  <div class="container">

    <!-- Live Status Banner -->
    <div class="status-bar">
      <div class="status-pills">
        <div class="pill">
          <div class="pill-dot green" id="dot-liveness"></div>
          <span>Liveness: <strong id="lbl-liveness">UP</strong></span>
        </div>
        <div class="pill">
          <div class="pill-dot green" id="dot-readiness"></div>
          <span>Readiness: <strong id="lbl-readiness">READY</strong></span>
        </div>
        <div class="pill">
          <div class="pill-dot green" id="dot-slo"></div>
          <span>30-Day Availability SLO: <strong>99.9%</strong></span>
        </div>
        <div class="pill">
          <span style="color: var(--primary);">⚡ Mode: <strong>Enterprise SaaS</strong></span>
        </div>
      </div>
      <div>
        <button class="btn btn-secondary" onclick="generateDemoRequisition()">
          + Quick Demo PR
        </button>
      </div>
    </div>

    <!-- Top KPI Stat Cards -->
    <div class="metrics-grid">
      <div class="stat-card">
        <div class="stat-label">Total Cumulative Spend</div>
        <div class="stat-value" id="kpi-spend">$0</div>
        <div class="stat-sub">Across all approved departments</div>
      </div>
      <div class="stat-card emerald">
        <div class="stat-label">Requisitions Processed</div>
        <div class="stat-value" id="kpi-count">0</div>
        <div class="stat-sub">Drafted, submitted & approved</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-label">Database Health Latency</div>
        <div class="stat-value" id="kpi-db-latency">0.0ms</div>
        <div class="stat-sub">PostgreSQL async ping</div>
      </div>
      <div class="stat-card amber">
        <div class="stat-label">Active Chaos Faults</div>
        <div class="stat-value" id="kpi-chaos-faults">0</div>
        <div class="stat-sub">Failure injections armed</div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="main-grid">

      <!-- Left Column: Procurement Requisitions Workflow -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">📦 Procurement Requisition Lifecycle</div>
          <button class="btn btn-secondary" onclick="fetchRequisitions()">↻ Refresh</button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Req #</th>
                <th>Title</th>
                <th>Department</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="requisitions-table-body">
              <tr>
                <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                  Loading procurement requisitions...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Right Column: SRE Chaos Engineering & Telemetry -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">💥 SRE Chaos Engineering & Alert Verification</div>
          <button class="btn btn-danger" onclick="resetChaos()">🧹 Reset All</button>
        </div>

        <div class="chaos-grid">
          <!-- Error Spike -->
          <div class="chaos-card">
            <div class="chaos-header">
              <span>HTTP 500 Error Burst</span>
              <span class="badge" id="lbl-chaos-error-state" style="background: rgba(255,255,255,0.05);">DISARMED</span>
            </div>
            <div class="chaos-desc">Burns the 99.9% SLO error budget to trigger 14.4x multi-burn-rate pages.</div>
            <div class="chaos-inputs">
              <input type="range" id="rng-error" min="10" max="100" value="60" oninput="document.getElementById('lbl-error-pct').innerText = this.value + '%'">
              <span class="chaos-val" id="lbl-error-pct">60%</span>
              <button class="btn btn-secondary" onclick="armErrorChaos()">Arm Spike</button>
            </div>
          </div>

          <!-- Latency Injection -->
          <div class="chaos-card">
            <div class="chaos-header">
              <span>Upstream Latency Spike</span>
              <span class="badge" id="lbl-chaos-latency-state" style="background: rgba(255,255,255,0.05);">DISARMED</span>
            </div>
            <div class="chaos-desc">Tests p95 latency SLO alerts (>300ms) and downstream circuit breakers.</div>
            <div class="chaos-inputs">
              <input type="range" id="rng-latency" min="0.2" max="3.0" step="0.2" value="1.0" oninput="document.getElementById('lbl-latency-sec').innerText = this.value + 's'">
              <span class="chaos-val" id="lbl-latency-sec">1.0s</span>
              <button class="btn btn-secondary" onclick="armLatencyChaos()">Arm Latency</button>
            </div>
          </div>

          <!-- Database Dropout -->
          <div class="chaos-card">
            <div class="chaos-header">
              <span>PostgreSQL Connection Dropout</span>
              <span class="badge" id="lbl-chaos-db-state" style="background: rgba(255,255,255,0.05);">ONLINE</span>
            </div>
            <div class="chaos-desc">Simulates DB host crash; isolates /healthz (UP) from /readyz (503 UNAVAILABLE).</div>
            <div style="margin-top: 0.3rem;">
              <button class="btn btn-danger" id="btn-toggle-db" onclick="toggleDbChaos()">Simulate DB Outage</button>
            </div>
          </div>
        </div>

        <div style="margin-top: 0.5rem;">
          <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.4rem;">
            LIVE SRE TELEMETRY & EVENT LOG
          </div>
          <div class="console" id="console-logs">
            <div class="console-line">[SYSTEM] Zycus ProcurePulse Mission Control initialized.</div>
          </div>
        </div>
      </div>

    </div>

  </div>

  <div id="toast"></div>

  <footer>
    Zycus ProcurePulse • Enterprise SRE & Procurement Platform • Built by Aryan
  </footer>

  <script>
    let isDbOffline = false;

    function logToConsole(msg) {
      const consoleEl = document.getElementById('console-logs');
      const time = new Date().toLocaleTimeString();
      const line = document.createElement('div');
      line.className = 'console-line';
      line.innerText = `[${time}] ${msg}`;
      consoleEl.prepend(line);
    }

    function showToast(message, isError = false) {
      const toast = document.getElementById('toast');
      toast.innerText = message;
      toast.style.borderColor = isError ? 'var(--danger)' : 'var(--primary)';
      toast.style.display = 'flex';
      setTimeout(() => { toast.style.display = 'none'; }, 3000);
    }

    async function fetchStatus() {
      try {
        const readyResp = await fetch('/readyz');
        const readyData = await readyResp.json();

        const dotReadiness = document.getElementById('dot-readiness');
        const lblReadiness = document.getElementById('lbl-readiness');
        const dbLatency = document.getElementById('kpi-db-latency');

        if (readyData.ready) {
          dotReadiness.className = 'pill-dot green';
          lblReadiness.innerText = 'READY';
          dbLatency.innerText = readyData.database.latency_ms + 'ms';
        } else {
          dotReadiness.className = 'pill-dot red';
          lblReadiness.innerText = 'DEGRADED';
          dbLatency.innerText = 'OFFLINE';
        }

        const chaosResp = await fetch('/api/v1/chaos/status');
        const chaosData = await chaosResp.json();

        let activeCount = 0;
        if (chaosData.error_spike.active) activeCount++;
        if (chaosData.latency.active) activeCount++;
        if (chaosData.db_offline.active) activeCount++;
        document.getElementById('kpi-chaos-faults').innerText = activeCount;

        // Update badges
        const errorBadge = document.getElementById('lbl-chaos-error-state');
        errorBadge.innerText = chaosData.error_spike.active ? 'ARMED' : 'DISARMED';
        errorBadge.style.color = chaosData.error_spike.active ? 'var(--danger)' : 'var(--text-muted)';

        const latBadge = document.getElementById('lbl-chaos-latency-state');
        latBadge.innerText = chaosData.latency.active ? 'ARMED' : 'DISARMED';
        latBadge.style.color = chaosData.latency.active ? 'var(--warning)' : 'var(--text-muted)';

        const dbBadge = document.getElementById('lbl-chaos-db-state');
        isDbOffline = chaosData.db_offline.active;
        dbBadge.innerText = isDbOffline ? 'OFFLINE' : 'ONLINE';
        dbBadge.style.color = isDbOffline ? 'var(--danger)' : 'var(--success)';
        document.getElementById('btn-toggle-db').innerText = isDbOffline ? 'Restore DB Connection' : 'Simulate DB Outage';
      } catch (err) {
        console.error('Status fetch error:', err);
      }
    }

    async function fetchAnalytics() {
      try {
        const resp = await fetch('/api/v1/analytics/spend');
        if (!resp.ok) return;
        const data = await resp.json();
        document.getElementById('kpi-spend').innerText = '$' + data.total_spend_usd.toLocaleString();
        document.getElementById('kpi-count').innerText = data.total_requisition_count;
      } catch (err) {
        console.error('Analytics fetch error:', err);
      }
    }

    async function fetchRequisitions() {
      try {
        const resp = await fetch('/api/v1/requisitions/?limit=20');
        if (!resp.ok) return;
        const items = await resp.json();
        const tbody = document.getElementById('requisitions-table-body');

        if (items.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No requisitions created yet. Click "+ Quick Demo PR" above!</td></tr>';
          return;
        }

        tbody.innerHTML = items.map(req => {
          let actionBtn = '';
          if (req.status === 'DRAFT') {
            actionBtn = `<button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.72rem;" onclick="submitRequisition(${req.id})">Submit</button>`;
          } else if (req.status === 'SUBMITTED') {
            actionBtn = `<button class="btn btn-success" style="padding: 0.25rem 0.5rem; font-size: 0.72rem;" onclick="approveRequisition(${req.id})">Approve</button>`;
          }

          return `
            <tr>
              <td><strong style="color: var(--primary); font-family: 'JetBrains Mono';">${req.req_number}</strong></td>
              <td>${req.title}</td>
              <td>${req.department}</td>
              <td style="font-family: 'JetBrains Mono';">$${req.total_amount.toLocaleString()}</td>
              <td><span class="badge ${req.status}">${req.status}</span></td>
              <td>${actionBtn}</td>
            </tr>
          `;
        }).join('');
      } catch (err) {
        console.error('Requisitions fetch error:', err);
      }
    }

    async function generateDemoRequisition() {
      const depts = ['Engineering', 'Procurement', 'Finance', 'IT Operations', 'Marketing'];
      const suppliers = ['Amazon Web Services', 'Zycus Cognitive AI', 'Salesforce Inc.', 'Apple Enterprise', 'Datadog'];
      const chosenDept = depts[Math.floor(Math.random() * depts.length)];
      const chosenSupp = suppliers[Math.floor(Math.random() * suppliers.length)];
      const qty = Math.floor(Math.random() * 5) + 1;
      const unitPrice = Math.floor(Math.random() * 2000) + 250;

      const payload = {
        title: `Enterprise Cloud & Software License for ${chosenDept}`,
        description: `Automated demonstration requisition generated from Mission Control`,
        requester_name: 'Aryan Admin',
        requester_email: 'aryan@zycus.com',
        department: chosenDept,
        currency: 'USD',
        priority: 'HIGH',
        line_items: [
          {
            item_description: `${chosenSupp} Enterprise Subscription`,
            category: 'Software Licenses',
            quantity: qty,
            unit_price: unitPrice,
            supplier_name: chosenSupp
          }
        ]
      };

      try {
        const resp = await fetch('/api/v1/requisitions/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();
        logToConsole(`Created Requisition ${data.req_number} ($${data.total_amount}) for ${chosenDept}`);
        showToast(`Created Requisition ${data.req_number}!`);
        fetchRequisitions();
        fetchAnalytics();
      } catch (err) {
        showToast('Failed to create requisition', true);
      }
    }

    async function submitRequisition(id) {
      try {
        const resp = await fetch(`/api/v1/requisitions/${id}/submit`, { method: 'POST' });
        const data = await resp.json();
        logToConsole(`Submitted Requisition ${data.req_number} for manager approval`);
        showToast(`Submitted ${data.req_number}!`);
        fetchRequisitions();
      } catch (err) {
        showToast('Failed to submit requisition', true);
      }
    }

    async function approveRequisition(id) {
      try {
        const resp = await fetch(`/api/v1/requisitions/${id}/approve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            approver_name: 'Sarah Connor',
            approver_role: 'Head of Procurement',
            decision: 'APPROVED',
            comments: 'Approved via SRE Mission Control UI'
          })
        });
        const data = await resp.json();
        logToConsole(`Approved Requisition ${data.req_number}`);
        showToast(`Approved ${data.req_number}!`);
        fetchRequisitions();
        fetchAnalytics();
      } catch (err) {
        showToast('Failed to approve requisition', true);
      }
    }

    async function armErrorChaos() {
      const pct = parseInt(document.getElementById('rng-error').value, 10) / 100.0;
      await fetch('/api/v1/chaos/error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ probability: pct, status_code: 500 })
      });
      logToConsole(`[CHAOS] Armed HTTP 500 error spike at ${pct * 100}% probability!`);
      showToast(`Chaos Armed: ${pct * 100}% Error Burst!`, true);
      fetchStatus();
    }

    async function armLatencyChaos() {
      const delay = parseFloat(document.getElementById('rng-latency').value);
      await fetch('/api/v1/chaos/latency', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delay_seconds: delay, probability: 1.0 })
      });
      logToConsole(`[CHAOS] Armed latency injection of ${delay}s!`);
      showToast(`Chaos Armed: ${delay}s Latency!`);
      fetchStatus();
    }

    async function toggleDbChaos() {
      const targetState = !isDbOffline;
      await fetch(`/api/v1/chaos/db-offline?offline=${targetState}`, { method: 'POST' });
      logToConsole(`[CHAOS] Set PostgreSQL Connection simulation to: ${targetState ? 'OFFLINE' : 'ONLINE'}`);
      showToast(`Database set to ${targetState ? 'OFFLINE' : 'ONLINE'}`, targetState);
      fetchStatus();
    }

    async function resetChaos() {
      await fetch('/api/v1/chaos/reset', { method: 'POST' });
      logToConsole(`[CHAOS] All chaos experiments disarmed. System nominal.`);
      showToast(`All chaos disarmed. System nominal!`);
      fetchStatus();
    }

    // Initial load & Polling loop
    fetchStatus();
    fetchAnalytics();
    fetchRequisitions();
    setInterval(() => {
      fetchStatus();
      fetchAnalytics();
    }, 3000);
  </script>
</body>
</html>
"""
