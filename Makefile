# MeterStream Development Makefile
# Run 'make help' to see available commands

SHELL := /bin/bash

.PHONY: help dev-up dev-down dev-logs nats-status nats-status-raw mongo-up mongo-down mongo-logs ingestion-run ingestion-test ingestion-lint auth-run auth-test gateway-run gateway-test gateway-lint producer-run generate-token peek-kafka extract-data clean integration-test load-interactive load-smoke load-normal load-stress load-spike

help:
	@echo "MeterStream Development Commands"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make dev-up        Start NATS for local development"
	@echo "  make dev-down      Stop NATS"
	@echo "  make dev-logs      Show NATS logs"
	@echo "  make nats-status   Show NATS JetStream status (streams, messages)"
	@echo ""
	@echo "  make mongo-up      Start MongoDB for local development"
	@echo "  make mongo-down    Stop MongoDB"
	@echo "  make mongo-logs    Show MongoDB logs (50 lines)"
	@echo ""
	@echo "Ingestion Service:"
	@echo "  make ingestion-run   Run the ingestion service locally"
	@echo "  make ingestion-test  Run ingestion service tests"
	@echo "  make ingestion-lint  Run linter on ingestion service"
	@echo ""
	@echo "Auth Service:"
	@echo "  make auth-run        Run the auth service locally"
	@echo "  make auth-test       Run auth service tests"
	@echo ""
	@echo "Gateway Service:"
	@echo "  make gateway-run     Run the API gateway locally"
	@echo "  make gateway-test    Run gateway tests"
	@echo "  make gateway-lint    Run linter on gateway"
	@echo ""
	@echo "Testing:"
	@echo "  make producer-run      Run the test data producer"
	@echo "  make generate-token    Generate a test JWT token"
	@echo "  make peek-kafka        Peek at Kalmar Energi Team 1's Kafka stream"
	@echo ""
	@echo "Integration Tests (Newman):"
	@echo "  make integration-test  Run Newman API tests against staging"
	@echo "                         Pass ADMIN_PASSWORD=xxx for cleanup tests"
	@echo ""
	@echo "Load Tests (Locust):"
	@echo "  make load-interactive  Open web UI at http://localhost:8089"
	@echo "  make load-smoke        Quick sanity check (1 user, 30s)"
	@echo "  make load-normal       Baseline performance (10 users, 2m)"
	@echo "  make load-stress       Stress test for HPA scaling (50 users, 5m)"
	@echo "  make load-spike        Sudden load burst (100 users, 1m)"
	@echo ""
	@echo "Data:"
	@echo "  make extract-data    Regenerate test_data_large.csv (50 customers, 4 years)"
	@echo "                       Requires source dataset in meterstream-filer/"
	@echo "                       Use scripts/extract_test_data.py for custom extractions"
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

mongo-up:
	docker compose -f docker-compose.mongo.yaml up -d
	@echo "MongoDB is running at localhost:27017"

mongo-down:
	docker compose -f docker-compose.mongo.yaml down

mongo-logs:
	docker compose -f docker-compose.mongo.yaml logs -f --tail 50

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

# Auth Service
auth-run:
	cd services/auth && \
	source .venv/bin/activate && \
	MONGODB_URL=mongodb://localhost:27017 uvicorn src.main:app --reload --port 8001

auth-test:
	cd services/auth && \
	source .venv/bin/activate && \
	pytest tests/ -v

# Gateway Service
gateway-run:
	cd services/gateway && \
	source .venv/bin/activate && \
	JWT_SECRET=test-secret-for-local-dev uvicorn src.main:app --reload

gateway-test:
	cd services/gateway && \
	source .venv/bin/activate && \
	JWT_SECRET=test-secret pytest tests/ -v

gateway-lint:
	cd services/gateway && \
	source .venv/bin/activate && \
	pylint src/ tests/

# Test data producer
producer-run:
	cd scripts && \
	python3 produce_test_data.py --url http://localhost:8000 --limit 100

# Generate test JWT token
generate-token:
	cd services/gateway && \
	source .venv/bin/activate && \
	python ../../scripts/generate_test_token.py --decode

# Peek at Kalmar Energi Team 1's Kafka stream
peek-kafka:
	@test -d scripts/node_modules || (cd scripts && npm install)
	cd scripts && node peek_kalmar1_kafka.js

# Extract test data from source dataset
extract-data:
	python3 scripts/extract_test_data.py -n 50 --seed 42 -o test_data_large.csv

# Integration Tests (Newman)
STAGING_URL ?= http://194.47.170.217
ADMIN_PASSWORD ?=

integration-test:
	newman run tests/integration/collections/meterstream-api.json \
		--environment tests/integration/environments/staging.json \
		--env-var "admin_password=$(ADMIN_PASSWORD)"

# Load Tests (Locust)
load-interactive:
	locust -f tests/load/locustfile.py --host=$(STAGING_URL)

load-smoke:
	locust -f tests/load/locustfile.py \
		--host=$(STAGING_URL) \
		--users 1 --spawn-rate 1 --run-time 30s --headless

load-normal:
	locust -f tests/load/locustfile.py \
		--host=$(STAGING_URL) \
		--users 10 --spawn-rate 5 --run-time 2m --headless

load-stress:
	locust -f tests/load/locustfile.py \
		--host=$(STAGING_URL) \
		--users 50 --spawn-rate 10 --run-time 5m --headless

load-spike:
	locust -f tests/load/locustfile.py \
		--host=$(STAGING_URL) \
		--users 100 --spawn-rate 50 --run-time 1m --headless

# Cleanup
clean:
	docker compose -f docker-compose.dev.yaml down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
