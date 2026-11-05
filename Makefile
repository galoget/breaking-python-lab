# Breaking Python Lab - convenience targets.
# These mirror the commands documented in the README; nothing here is required
# to use the lab, it just saves typing. Run `make` or `make help` to list them.
#
# Assumes a virtual environment is active (see README: python -m venv .venv).

PYTHON ?= python
BASE   ?= http://127.0.0.1:5000

.DEFAULT_GOAL := help
.PHONY: help install install-dev run poc lint sast docker-up docker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies (both branches)
	$(PYTHON) -m pip install -r requirements.txt

install-dev: ## Install SAST tools (bandit + semgrep)
	$(PYTHON) -m pip install -r requirements-dev.txt

run: ## Run the lab + the simulated internal service (SSRF challenge)
	cd app && $(PYTHON) internal_service.py & \
	cd app && exec $(PYTHON) app.py

poc: ## Run all proof-of-concept tests against a running lab
	$(PYTHON) exploits/poc.py --base $(BASE)

lint: ## Check code style (PEP 8, 79 columns)
	flake8

sast: ## Run static analysis on app/ (bandit + semgrep)
	bandit -r app/
	semgrep --config auto app/

docker-up: ## Build and start the lab with Docker (127.0.0.1:5000)
	docker compose up --build

docker-down: ## Stop and remove the Docker containers
	docker compose down

clean: ## Remove the local database and Python caches
	rm -f app/lab.db
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
