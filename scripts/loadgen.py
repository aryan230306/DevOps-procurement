#!/usr/bin/env python3
"""Realistic procurement traffic and load generator for Zycus ProcurePulse."""

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DEPARTMENTS = ["Engineering", "Finance", "Legal", "Procurement", "Sales", "Operations", "Marketing"]
CATEGORIES = ["Software Licenses", "Cloud Infrastructure", "Hardware", "Consulting", "Office Supplies"]
SUPPLIERS = [
    "Amazon Web Services",
    "Microsoft Azure",
    "Zycus Cognitive AI",
    "Salesforce Inc.",
    "Apple Enterprise",
    "Gartner Advisory",
]

STATS = {
    "requests": 0,
    "success": 0,
    "client_errors": 0,
    "server_errors": 0,
    "total_time": 0.0,
}


def send_http(method: str, url: str, data: dict = None):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            elapsed = time.perf_counter() - start
            return resp.status, resp.read().decode("utf-8"), elapsed
    except urllib.error.HTTPError as err:
        elapsed = time.perf_counter() - start
        return err.code, "", elapsed
    except Exception:
        elapsed = time.perf_counter() - start
        return 0, "", elapsed


def simulate_procurement_user(base_url: str):
    """Executes a randomized user journey through the procurement system."""
    action = random.random()

    if action < 0.40:
        # Create a new Requisition
        dept = random.choice(DEPARTMENTS)
        items_count = random.randint(1, 4)
        items = []
        for _ in range(items_count):
            items.append(
                {
                    "item_description": f"{random.choice(CATEGORIES)} Subscription",
                    "category": random.choice(CATEGORIES),
                    "quantity": random.randint(1, 10),
                    "unit_price": round(random.uniform(50.0, 2500.0), 2),
                    "supplier_name": random.choice(SUPPLIERS),
                }
            )

        payload = {
            "title": f"Q4 Procurement for {dept}",
            "description": "Standard departmental procurement request",
            "requester_name": f"User_{random.randint(100, 999)}",
            "requester_email": f"requester_{random.randint(100, 999)}@zycus.com",
            "department": dept,
            "currency": "USD",
            "priority": random.choice(["LOW", "MEDIUM", "HIGH", "URGENT"]),
            "line_items": items,
        }
        status, body, elapsed = send_http("POST", f"{base_url}/api/v1/requisitions/", payload)

        if status == 201:
            req_data = json.loads(body)
            req_id = req_data["id"]
            # 50% chance to immediately submit
            if random.random() < 0.5:
                send_http("POST", f"{base_url}/api/v1/requisitions/{req_id}/submit")

    elif action < 0.65:
        # Query spend analytics
        status, _, elapsed = send_http("GET", f"{base_url}/api/v1/analytics/spend")

    elif action < 0.85:
        # List requisitions
        dept = random.choice(DEPARTMENTS) if random.random() < 0.5 else ""
        query = f"?department={dept}" if dept else ""
        status, _, elapsed = send_http("GET", f"{base_url}/api/v1/requisitions/{query}")

    else:
        # Health & readiness probe
        probe = "/readyz" if random.random() < 0.5 else "/healthz"
        status, _, elapsed = send_http("GET", f"{base_url}{probe}")

    # Record stats
    STATS["requests"] += 1
    STATS["total_time"] += elapsed
    if 200 <= status < 300:
        STATS["success"] += 1
    elif 400 <= status < 500:
        STATS["client_errors"] += 1
    else:
        STATS["server_errors"] += 1


def main():
    parser = argparse.ArgumentParser(description="Zycus ProcurePulse Realistic Load Generator")
    parser.add_argument("--url", default="http://localhost:8000", help="Target API URL")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent client workers")
    parser.add_argument("--duration", type=int, default=0, help="Run duration in seconds (0 = infinite)")
    args = parser.parse_args()

    print(f"[*] Starting LoadGen against {args.url} (Concurrency: {args.concurrency}, Duration: {args.duration or 'infinite'}s)")
    start_time = time.time()
    last_report_time = start_time
    last_requests = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        try:
            while True:
                if args.duration > 0 and (time.time() - start_time) > args.duration:
                    break

                futures = [executor.submit(simulate_procurement_user, args.url) for _ in range(args.concurrency)]
                for f in futures:
                    f.result()

                # Report stats every 5 seconds
                now = time.time()
                if now - last_report_time >= 5.0:
                    delta_t = now - last_report_time
                    delta_req = STATS["requests"] - last_requests
                    rps = delta_req / delta_t
                    avg_lat_ms = (STATS["total_time"] / max(1, STATS["requests"])) * 1000.0

                    print(
                        f"[{time.strftime('%H:%M:%S')}] Rate: {rps:.1f} rps | "
                        f"2xx: {STATS['success']} | "
                        f"4xx: {STATS['client_errors']} | "
                        f"5xx: {STATS['server_errors']} | "
                        f"Avg Latency: {avg_lat_ms:.1f}ms"
                    )
                    last_report_time = now
                    last_requests = STATS["requests"]

                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n[*] Load generation stopped by user.")

    print(f"\n[SUMMARY] Total Requests: {STATS['requests']} | Success (2xx): {STATS['success']} | Errors (5xx): {STATS['server_errors']}")


if __name__ == "__main__":
    main()
