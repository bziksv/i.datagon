COMPOSE = docker compose -f docker-compose.yml -f docker-compose.local.yml

.PHONY: up down logs test

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

test:
	pytest
