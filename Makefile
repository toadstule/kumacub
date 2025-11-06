#!/usr/bin/make

# These need to be at the top
PRESET_VARS := $(.VARIABLES)

# Project variables
PROJECT_NAME    := $(shell grep -e '^name =' pyproject.toml | cut -d'"' -f2)
PY_FILES        := $(shell find . -name '*.py' | grep -v "/.venv/" | grep -v "/dist/")
PYTHON_VERSION_ := $(shell cat .python-version)
VERSION         := $(shell grep -e '^version =' pyproject.toml | cut -d'"' -f2)
WHEEL           := dist/$(PROJECT_NAME)-$(VERSION)-py3-none-any.whl

# Tool variables
PYTHON := $(shell command -v python$(PYTHON_VERSION_))
UV     := $(shell command -v uv)
MYPY   := $(UV) run -m mypy
PIP    := $(UV) pip
PYTEST := $(UV) run pytest
RUFF   := $(UV) run ruff

# Verify that we have the required tools.
ifndef UV
$(error "uv is not installed.")
endif


.PHONY: all
all: build

.PHONY: build
build: $(WHEEL)  ## Build the package.

.PHONY: check
check: lint test  ## Check the code.

.PHONY: clean
clean:  ## Clean up.
	@find . -name "__pycache__" | grep -v "/.venv/" | xargs rm -rf
	@rm -rf .pytest_cache tests/.pytest_cache
	@rm -rf htmlcov .coverage
	@rm -rf .pytype
	@rm -rf .ruff_cache .mypy_cache
	@$(UV) clean
	@rm -rf dist

.PHONY: dep
dep:  ## Install dependencies.
	@$(UV) sync

.PHONY: dep-upgrade
dep-upgrade:  ## Upgrade the dependencies.
	@$(UV) lock --upgrade

.PHONY: format
format:  ## Format the code; sort the imports.
	@$(RUFF) format $(PY_FILES)
	@$(RUFF) check --fix --select I $(PY_FILES)

.PHONY: help
help:  ## Display this help.
	@grep -h -E '^[a-zA-Z0-9._-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: venv-check $(WHEEL)  ## Install the package (locally).
	@$(PIP) install --editable .

.PHONY: lint
lint: format  ## Lint the code.
	@$(RUFF) format --check $(PY_FILES)
	@$(RUFF) check $(PY_FILES)
	@$(MYPY) --non-interactive $(PY_FILES)

.PHONY: showvars
showvars:  ## Display variables available in the Makefile.
	$(foreach v, $(filter-out $(PRESET_VARS) PRESET_VARS,$(.VARIABLES)), $(info $(v) = $($(v))))

.PHONY: test
test:  ## Run unit tests.
	$(PYTEST) --verbose tests

.PHONY: venv-check
venv-check:  # Verify that we are in a virtual environment (or in a Python container).
ifndef VIRTUAL_ENV
ifndef PYTHON_VERSION
	$(error this should only be executed in a Python virtual environment)
endif
endif

uv.lock:
	@$(UV) lock

$(WHEEL): $(PY_FILES) pyproject.toml uv.lock dep
	@$(UV) build
