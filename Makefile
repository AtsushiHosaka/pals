COMPOSE_ENV_FILE ?= $(if $(wildcard .env.local),.env.local,.env.example)
COMPOSE := docker compose --env-file $(COMPOSE_ENV_FILE)
PALS_LOCAL_ENV_FILE ?= .env.local
PALS_LOCAL_COGNITO_COMPOSE := docker compose --project-name pals-local --env-file "$(PALS_LOCAL_ENV_FILE)" -f pals-infra/docker-compose.localstack.yml
API_PYTHON ?= .venv/bin/python
AGENT_PYTHON ?= .venv/bin/python
OBSERVABILITY_PYTHON ?= .venv/bin/python
LOAD_ENV = set -a; . ./$(COMPOSE_ENV_FILE); set +a;

.PHONY: pals-up pals-qa local-cognito-bootstrap dev-up dev-down dev-logs dev-ps api-deps api-test web-deps web-test web-build web-lint draft-admin-deps draft-admin-test agent-deps agent-test agent-lean-deps agent-evaluation-history agent-evaluation-smoke agent-evaluation-full agent-evaluation-compare observability-deps observability-test pals-scripts-test repository-gates infra-test test openapi

pals-up:
	./tests/e2e/run-local.sh --up-only

pals-qa:
	./tests/e2e/run-local.sh

local-cognito-bootstrap:
	@test -f "$(PALS_LOCAL_ENV_FILE)" || { printf '%s\n' 'Create .env.local before bootstrapping local Cognito.' >&2; exit 2; }
	$(PALS_LOCAL_COGNITO_COMPOSE) up -d --wait cognito-local
	python3 pals-scripts/bootstrap-local-cognito.py --env-file "$(PALS_LOCAL_ENV_FILE)"

dev-up:
	$(COMPOSE) up -d --wait postgres

dev-down:
	$(COMPOSE) down

dev-logs:
	$(COMPOSE) logs -f postgres

dev-ps:
	$(COMPOSE) ps

api-deps:
	cd pals-api && test -x $(API_PYTHON) || python3 -m venv .venv
	cd pals-api && $(API_PYTHON) -c "import app, boto3, fastapi, mypy, psycopg, pytest" || $(API_PYTHON) -m pip install -e ".[dev]"

api-test: api-deps
	cd pals-api && $(API_PYTHON) -m pytest
	cd pals-api && $(API_PYTHON) -m ruff check .
	cd pals-api && $(API_PYTHON) -m mypy app tests

web-deps:
	cd pals-webfront && npm install

web-test: web-deps
	cd pals-webfront && npm test
	cd pals-webfront && npm run typecheck
	cd pals-webfront && npm run lint

web-build: web-deps
	$(LOAD_ENV) cd pals-webfront && npm run build

web-lint:
	cd pals-webfront && npm run lint

draft-admin-deps:
	cd pals-draft-admin && npm install

draft-admin-test: draft-admin-deps
	cd pals-draft-admin && npm test
	cd pals-draft-admin && npm run typecheck
	cd pals-draft-admin && npm run lint
	cd pals-draft-admin && npm run build

agent-deps:
	cd pals-agent && test -x $(AGENT_PYTHON) || python3 -m venv .venv
	cd pals-agent && $(AGENT_PYTHON) -c "import boto3, mypy, pals_agent, pytest" || $(AGENT_PYTHON) -m pip install -e ".[dev]"

agent-test: agent-deps
	cd pals-agent && $(AGENT_PYTHON) -m pytest
	cd pals-agent && $(AGENT_PYTHON) -m ruff check .
	cd pals-agent && $(AGENT_PYTHON) -m mypy pals_agent tests

agent-lean-deps:
	cd pals-agent/lean-workspace && lake update
	cd pals-agent/lean-workspace && lake exe cache get

agent-evaluation-history: agent-deps
	cd pals-agent && if [ -n "$${RUN_ID:-}" ]; then $(AGENT_PYTHON) -m pals_agent.cli evaluation-history --run-id "$${RUN_ID}"; else $(AGENT_PYTHON) -m pals_agent.cli evaluation-history; fi

agent-evaluation-smoke: agent-deps
	$(LOAD_ENV) cd pals-agent && .venv/bin/python -m pals_agent.cli evaluation-run --profile smoke

agent-evaluation-full: agent-deps
	$(LOAD_ENV) cd pals-agent && .venv/bin/python -m pals_agent.cli evaluation-run --profile full

agent-evaluation-compare: agent-deps
	$(LOAD_ENV) cd pals-agent && .venv/bin/python -m pals_agent.cli evaluation-compare --baseline-run "$${BASELINE_RUN:?Set BASELINE_RUN}" --candidate-run "$${CANDIDATE_RUN:?Set CANDIDATE_RUN}"

observability-deps:
	cd pals-observability && test -x $(OBSERVABILITY_PYTHON) || python3 -m venv .venv
	cd pals-observability && $(OBSERVABILITY_PYTHON) -c "import langfuse, mypy, pals_observability, pytest, ruff" || $(OBSERVABILITY_PYTHON) -m pip install -e ".[dev]"

observability-test: observability-deps
	cd pals-observability && $(OBSERVABILITY_PYTHON) -m pytest
	cd pals-observability && $(OBSERVABILITY_PYTHON) -m ruff check .
	cd pals-observability && $(OBSERVABILITY_PYTHON) -m mypy src tests
	cd pals-observability && $(OBSERVABILITY_PYTHON) -m pip check

.venv-pals-scripts/bin/python: pals-scripts/requirements.txt pals-scripts/bootstrap-pals-scripts-python.sh
	@./pals-scripts/bootstrap-pals-scripts-python.sh

pals-scripts-test: .venv-pals-scripts/bin/python
	@find pals-scripts -type f -name '*.sh' -exec bash -n {} +
	@set -eu; for test_script in pals-scripts/tests/*.sh; do [ -f "$$test_script" ] || continue; bash "$$test_script"; done

repository-gates:
	./pals-scripts/check-secrets.sh
	./pals-scripts/check-public-agent-boundary.sh

infra-test:
	cd pals-infra/terraform && terraform fmt -check -recursive
	cd pals-infra/terraform && terraform init -backend=false -input=false -lockfile=readonly
	cd pals-infra/terraform && terraform validate

test: api-test web-test web-build draft-admin-test agent-test observability-test pals-scripts-test infra-test

openapi:
	cd pals-api && $(API_PYTHON) scripts/generate_openapi.py
