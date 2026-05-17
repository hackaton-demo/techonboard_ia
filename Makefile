.PHONY: up down logs migrate seed backend-shell test build reset frontend-dev backend-dev

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

migrate:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python scripts/seed_demo_data.py

backend-shell:
	docker-compose exec backend bash

test:
	docker-compose exec backend pytest

build:
	docker-compose build --no-cache

reset:
	docker-compose down -v
	$(MAKE) up
	$(MAKE) migrate
	$(MAKE) seed

frontend-dev:
	cd frontend && npm run dev

backend-dev:
	uvicorn backend.main:app --reload --port 8000
