"""Alertmanager webhook sink service.

Receives webhook payloads from Alertmanager, logs them in real-time,
and stores recent alerts in memory for automated Game Day verification.
"""

import json
import logging
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ALERT-SINK] %(message)s",
)
logger = logging.getLogger("sink")

RECEIVED_ALERTS = []


class AlertSinkHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/alerts":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(RECEIVED_ALERTS, indent=2).encode("utf-8"))
        elif self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                payload = json.loads(post_data.decode("utf-8"))
                status = payload.get("status", "unknown").upper()
                alerts = payload.get("alerts", [])

                logger.info(f"=== ALERT NOTIFICATION RECEIVED [{status}] ===")
                for alert in alerts:
                    labels = alert.get("labels", {})
                    annotations = alert.get("annotations", {})
                    alert_name = labels.get("alertname", "UnknownAlert")
                    severity = labels.get("severity", "info")
                    summary = annotations.get("summary", "No summary")
                    description = annotations.get("description", "No description")

                    log_msg = f"[{severity.upper()}] {alert_name} -> {summary} | {description}"
                    logger.warning(log_msg)

                    RECEIVED_ALERTS.append(
                        {
                            "received_at": datetime.now(timezone.utc).isoformat(),
                            "status": alert.get("status"),
                            "alertname": alert_name,
                            "severity": severity,
                            "summary": summary,
                            "description": description,
                            "labels": labels,
                        }
                    )

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "received"}')
            except Exception as exc:
                logger.error(f"Error parsing webhook: {exc}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "bad request"}')
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=9999):
    server = HTTPServer(("0.0.0.0", port), AlertSinkHandler)
    logger.info(f"Alert Sink listening on port {port}...")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
