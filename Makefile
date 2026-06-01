BACKEND_PYTHON ?= $(shell if [ -x backend/.venv/bin/python ]; then echo backend/.venv/bin/python; else echo python; fi)
FRONTEND_DIR ?= frontend

.PHONY: backend-install backend-lint backend-format-check backend-tests frontend-install frontend-lint frontend-typecheck frontend-build markdown-lint mocked-smoke ci

backend-install:
	$(BACKEND_PYTHON) -m pip install -r backend/requirements-dev.txt

backend-lint:
	$(BACKEND_PYTHON) -m ruff check backend scripts
	$(BACKEND_PYTHON) -m ruff format --check backend scripts

backend-format-check:
	$(BACKEND_PYTHON) -m ruff format --check backend scripts

backend-tests:
	$(BACKEND_PYTHON) -m pytest backend/tests -m "not smoke"

frontend-install:
	cd $(FRONTEND_DIR) && npm ci

frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

frontend-typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

markdown-lint:
	cd $(FRONTEND_DIR) && npm run lint:md

mocked-smoke:
	$(BACKEND_PYTHON) -m pytest backend/tests/test_mocked_smoke.py

ci: backend-lint backend-tests frontend-lint frontend-typecheck frontend-build markdown-lint mocked-smoke
