.PHONY: help setup test lint run up down status smoke load chaos gameday backup restore clean

help:
	@echo "Zycus ProcurePulse — Enterprise SRE & Procurement Requisition Service"
	@echo "Available commands:"
	@echo "  make setup     - Create virtual environment and install dependencies"
	@echo "  make test      - Run full pytest test suite"
	@echo "  make lint      - Run ruff linter and black code formatter"
	@echo "  make run       - Run application locally with Uvicorn (uses SQLite fallback)"
	@echo "  make up        - Start full Docker Compose stack (App, Postgres, Nginx, Prometheus, Grafana, Alertmanager)"
	@echo "  make down      - Stop all containers and teardown networks"
	@echo "  make status    - Show container status, health probes, and active alerts"
	@echo "  make smoke     - Run end-to-end smoke test against running service"
	@echo "  make load      - Run realistic procurement traffic load generator"
	@echo "  make chaos     - Open chaos engineering status CLI"
	@echo "  make gameday   - Execute automated SRE Chaos Game Day (outage, alert, recovery)"
	@echo "  make backup    - Execute PostgreSQL logical backup with checksum"
	@echo "  make restore   - Restore database from latest backup"
	@echo "  make clean     - Remove virtual environment, pycache, and temporary files"

setup:
	./scripts/init_env.sh
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt

test:
	.venv/bin/pytest -v

lint:
	.venv/bin/ruff check .
	.venv/bin/black .

run:
	.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

up:
	./scripts/deploy.sh

down:
	docker compose down

status:
	./scripts/status.sh

smoke:
	./scripts/smoke.py http://localhost:8000

load:
	./scripts/loadgen.py --url http://localhost:8000 --concurrency 5

chaos:
	./scripts/chaosctl.py status

gameday:
	./scripts/gameday.sh http://localhost:8000

backup:
	./scripts/backup.sh

restore:
	./scripts/restore.sh

clean:
	rm -rf .venv __pycache__ */__pycache__ */*/__pycache__ .pytest_cache .ruff_cache
