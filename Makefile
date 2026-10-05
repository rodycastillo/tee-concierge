UV ?= $(shell command -v uv || echo $(HOME)/.local/bin/uv)

.PHONY: smoke seed migrate chat install up down logs test lint fmt typecheck arch check run
install:   ## Install dependencies
	$(UV) sync
up:        ## Start api, worker, postgres, redis
	docker compose up --build -d
down:
	docker compose down
logs:
	docker compose logs -f api worker
run:       ## Run API locally with reload
	$(UV) run uvicorn tee_concierge.interfaces.api.main:app --reload
test:
	$(UV) run pytest
lint:
	$(UV) run ruff check . && $(UV) run ruff format --check .
fmt:
	$(UV) run ruff check --fix . && $(UV) run ruff format .
typecheck:
	$(UV) run mypy
arch:      ## Verify layer rules
	$(UV) run lint-imports
check: lint typecheck arch test   ## Everything CI runs
migrate:   ## Apply database migrations (needs DATABASE_URL)
	$(UV) run alembic upgrade head
chat:      ## Chat with the bot in the terminal (fake gateway, stack must be up)
	$(UV) run tee-chat
seed:      ## Load the synthetic demo catalog and FAQ (idempotent)
	$(UV) run python -m tee_concierge.seed
smoke:     ## End-to-end test against the running stack (make up && make seed first)
	$(UV) run python scripts/smoke_test.py
