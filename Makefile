.PHONY: help build up down restart logs ps clean test init

# Help command to display available commands
help:
	@echo "Available commands:"
	@echo "  make build       - Build all Docker containers"
	@echo "  make up          - Start all containers"
	@echo "  make down        - Stop all containers"
	@echo "  make restart     - Restart all containers"
	@echo "  make logs        - View logs of all containers"
	@echo "  make ps          - List running containers"
	@echo "  make clean       - Remove all containers, volumes, and images"
	@echo "  make test        - Run backend tests"
	@echo "  make init        - Initialize the system (run after first up)"

# Build all containers
build:
	docker-compose build

# Start all containers
up:
	docker-compose up -d

# Stop all containers
down:
	docker-compose down

# Restart all containers
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# List running containers
ps:
	docker-compose ps

# Remove all containers, volumes, and images
clean:
	docker-compose down -v --rmi all

# Run tests
test:
	docker-compose exec backend pytest

# Initialize the system
init:
	@echo "Initializing the system..."
	curl -X POST http://localhost:8000/api/v1/system/initialize
	@echo "\nSystem initialization complete!" 