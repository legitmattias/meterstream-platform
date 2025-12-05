# MeterStream Development Makefile
# Run 'make help' to see available commands

SHELL := /bin/bash

.PHONY: help dev-up dev-down dev-logs nats-status nats-status-raw ingestion-run ingestion-test ingestion-lint producer-run clean

help:
	@echo "MeterStream Development Commands"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make dev-up        Start NATS for local development"
	@echo "  make dev-down      Stop NATS"
	@echo "  make dev-logs      Show NATS logs"
	@echo "  make nats-status   Show NATS JetStream status (streams, messages)"
	@echo ""
	@echo "Ingestion Service:"
	@echo "  make ingestion-run   Run the ingestion service locally"
	@echo "  make ingestion-test  Run ingestion service tests"
	@echo "  make ingestion-lint  Run linter on ingestion service"
	@echo ""
	@echo "Testing:"
	@echo "  make producer-run    Run the test data producer"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove all containers and volumes"

# Infrastructure
dev-up:
	docker compose -f docker-compose.dev.yaml up -d
	@echo "NATS is running at localhost:4222"
	@echo "NATS monitoring at http://localhost:8222"

dev-down:
	docker compose -f docker-compose.dev.yaml down

dev-logs:
	docker compose -f docker-compose.dev.yaml logs -f

nats-status:
	@python3 scripts/nats_status.py

nats-status-raw:
	@curl -s http://localhost:8222/jsz 2>/dev/null | python3 -m json.tool || echo "NATS not running"

# Ingestion Service
ingestion-run:
	cd services/ingestion && \
	source .venv/bin/activate && \
	NATS_URL=nats://localhost:4222 uvicorn src.main:app --reload

ingestion-test:
	cd services/ingestion && \
	source .venv/bin/activate && \
	pytest tests/ -v

ingestion-lint:
	cd services/ingestion && \
	source .venv/bin/activate && \
	pylint src/ tests/

# Test data producer
producer-run:
	cd scripts && \
	python3 produce_test_data.py --url http://localhost:8000 --limit 100

# Cleanup
clean:
	docker compose -f docker-compose.dev.yaml down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
