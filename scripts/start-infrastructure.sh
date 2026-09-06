#!/bin/bash

set -e

echo "Starting eShop Infrastructure Services..."

COMPOSE_FILE="docker-compose.infrastructure.yml"

run_compose() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo "Using Docker Compose"
        docker compose -f "$COMPOSE_FILE" "$@"
    elif command -v podman-compose >/dev/null 2>&1; then
        if ! podman info >/dev/null 2>&1; then
            echo "Podman is not running. Please run: podman machine start"
            exit 1
        fi
        echo "Using Podman Compose"
        podman-compose -f "$COMPOSE_FILE" "$@"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "Using docker-compose"
        docker-compose -f "$COMPOSE_FILE" "$@"
    else
        echo "No container runtime found. Install Docker Compose or Podman."
        exit 1
    fi
}

echo "Starting PostgreSQL, Redis, RabbitMQ, Seq, and Keycloak..."
run_compose up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Service Status:"
run_compose ps

echo ""
echo "Infrastructure services started successfully!"
echo ""
echo "Access Points:"
echo "  PostgreSQL:          localhost:5432"
echo "  Redis:               localhost:6379"
echo "  RabbitMQ:            localhost:5672"
echo "  RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "  Seq:                 http://localhost:5341"
echo "  Keycloak Admin:      http://localhost:8080 (admin/admin)"
echo ""
echo "Next Steps:"
echo "  1. Run backend:  cd backend && poetry run uvicorn app.main:app --reload"
echo "  2. Run frontend: cd frontend && python3 -m http.server 3000"
echo ""
echo "See docs/GETTING_STARTED.md for the full runbook."
echo "To stop: ./scripts/stop-infrastructure.sh"
