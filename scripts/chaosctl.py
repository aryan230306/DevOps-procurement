#!/usr/bin/env python3
"""CLI utility for injecting and managing runtime chaos experiments in ProcurePulse."""

import argparse
import json
import sys
import urllib.error
import urllib.request


def send_request(base_url: str, method: str, path: str, payload: dict = None):
    url = f"{base_url}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        print(f"[!] HTTP Error {err.code}: {err.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as exc:
        print(f"[!] Network error: {exc}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="ProcurePulse Chaos Engineering Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of ProcurePulse API (default: http://localhost:8000)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Get current chaos status")

    # reset
    subparsers.add_parser("reset", help="Disarm all chaos experiments (restore nominal)")

    # latency
    latency_p = subparsers.add_parser("latency", help="Inject synthetic latency")
    latency_p.add_argument("--delay", type=float, default=1.5, help="Delay in seconds (default: 1.5)")
    latency_p.add_argument("--prob", type=float, default=1.0, help="Probability 0.0-1.0 (default: 1.0)")

    # error
    error_p = subparsers.add_parser("error", help="Inject HTTP 500 error bursts")
    error_p.add_argument("--prob", type=float, default=0.5, help="Error probability 0.0-1.0 (default: 0.5)")
    error_p.add_argument("--code", type=int, default=500, help="HTTP status code (default: 500)")
    error_p.add_argument("--msg", default="Chaos Injected: Critical Downstream Failure", help="Error message")

    # db
    db_p = subparsers.add_parser("db", help="Simulate database outage")
    db_p.add_argument("--offline", action="store_true", help="Take database offline")
    db_p.add_argument("--online", action="store_true", help="Restore database connection")

    # memory
    mem_p = subparsers.add_parser("leak", help="Simulate memory leak")
    mem_p.add_argument("--mb", type=int, default=50, help="Megabytes to allocate (default: 50)")

    args = parser.parse_args()

    if args.command == "status":
        res = send_request(args.url, "GET", "/api/v1/chaos/status")
        print(json.dumps(res, indent=2))

    elif args.command == "reset":
        res = send_request(args.url, "POST", "/api/v1/chaos/reset")
        print(f"[✓] {res.get('message', 'Chaos reset')}")

    elif args.command == "latency":
        payload = {"delay_seconds": args.delay, "probability": args.prob}
        res = send_request(args.url, "POST", "/api/v1/chaos/latency", payload)
        print(f"[✓] Latency armed: {args.delay}s (prob: {args.prob})")

    elif args.command == "error":
        payload = {"probability": args.prob, "status_code": args.code, "message": args.msg}
        res = send_request(args.url, "POST", "/api/v1/chaos/error", payload)
        print(f"[✓] Error burst armed: status {args.code} (prob: {args.prob})")

    elif args.command == "db":
        offline = True if args.offline else (False if args.online else True)
        res = send_request(args.url, "POST", f"/api/v1/chaos/db-offline?offline={str(offline).lower()}")
        status_str = "OFFLINE" if offline else "ONLINE"
        print(f"[✓] Database connection simulation set to: {status_str}")

    elif args.command == "leak":
        payload = {"megabytes": args.mb}
        res = send_request(args.url, "POST", "/api/v1/chaos/memory-leak", payload)
        print(f"[✓] Allocated {args.mb}MB. Total leak buffer: {res.get('total_leaked_mb')}MB")


if __name__ == "__main__":
    main()
