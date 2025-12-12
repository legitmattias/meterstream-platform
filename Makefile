# MeterStream Development Makefile
# Run 'make help' to see available commands

SHELL := /bin/bash

.PHONY: help dev-up dev-down dev-logs nats-status nats-status-raw mongo-up mongo-down mongo-logs ingestion-run ingestion-test ingestion-lint auth-run auth-test gateway-run gateway-test gateway-lint producer-run generate-token peek-kafka clean

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
	@echo "  make producer-run    Run the test data producer"
	@echo "  make generate-token  Generate a test JWT token"
	@echo "  make peek-kafka      Peek at Kalmar Energi Team 1's Kafka stream"
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

# Peek at Kalmar Energi Team 1's Kafka stream (requires: cd scripts && npm install)
peek-kafka:
	cd scripts && \
	node peek_kalmar1_kafka.js

# Cleanup
clean:
	docker compose -f docker-compose.dev.yaml down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
