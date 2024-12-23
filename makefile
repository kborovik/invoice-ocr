.EXPORT_ALL_VARIABLES:
.ONESHELL:
.SILENT:
.default: settings

MAKEFLAGS += --no-builtin-rules --no-builtin-variables

PATH := $(HOME)/.cargo/bin:$(abspath .venv)/bin:$(PATH)

LOGFIRE_TOKEN := $(file < $(HOME)/.secrets/LOGFIRE_TOKEN)
GEMINI_API_KEY := $(file < $(HOME)/.secrets/GEMINI_API_KEY)

ifneq (,$(wildcard pyproject.toml))
NAME := $(shell yq -p toml -o yaml '.project.name' pyproject.toml)
MODULE := $(shell yq -p toml -o yaml '.project.scripts' pyproject.toml | cut -d':' -f2 | xargs)
VERSION := $(shell yq -p toml -o yaml '.project.version' pyproject.toml)
endif

settings: setup
	$(call header,Settings)
	$(call var,VERSION,$(VERSION))
	$(call var,NAME,$(NAME))
	$(call var,MODULE,$(MODULE))
	$(call var,LOGFIRE_TOKEN,$(LOGFIRE_TOKEN))
	$(call var,GEMINI_API_KEY,$(GEMINI_API_KEY))

help:
	echo "Usage: make [recipe]"
	echo "Recipes:"
	awk '/^[a-zA-Z0-9_-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-15s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH); \
		} \
	}' $(MAKEFILE_LIST)

setup: $(uv_bin) .gitignore data .venv uv.lock

build: setup ## Build Python package
	uv build --wheel

update: ## Update Python packages
	rm uv.lock
	$(MAKE) uv.lock

clean: ## Reset development environment
	rm -rf .venv requirements.txt build/ dist/ *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} +

run-generate: ## Run Python generate module
	uv run -m invoice_ocr.generate

uv_bin := $(HOME)/.cargo/bin/uv

$(uv_bin):
	$(call header,uv - Install)
	mkdir -p $(@D)
	curl -LsSf https://astral.sh/uv/install.sh | sh

.gitignore:
	cat << EOF > $(@)
	**/__pycache__/
	**/data/
	EOF

data:
	mkdir -p $(@)

.venv:
	uv venv

define INIT_PY
from .__main__ import main
__all__ = ["main", "$(MODULE)"]
endef

define MAIN_PY
def main() -> None:
    print("Hello world!")
if __name__ == "__main__":
    main()
endef

src-init:
	echo "$$INIT_PY" >| src/$(MODULE)/__init__.py
	echo "$$MAIN_PY" >| src/$(MODULE)/__main__.py
	ruff format .

pyproject.toml:
	uv init --package
	uv add --dev ruff

uv.lock: pyproject.toml
	uv sync --inexact && touch $(@)

requirements.txt: uv.lock
	uv pip freeze --exclude-editable --color never >| $(@)

ruff-format:
	ruff format .

ruff-lint:
	ruff check --fix .

lint: ruff-lint ruff-format ## Lint Python code

version: db-schema
	$(eval pre_release := $(shell date '+%H%M' | sed 's/^0*//'))
	$(eval version := $(shell date '+%Y.%m.%d.post$(pre_release)'))
	set -e
	sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+.*"/version = "$(version)"/' pyproject.toml
	uv sync --inexact
	git add --all

commit: db-schema ruff-lint ruff-format
	git commit -m "Patch: $(NAME) v$(VERSION)"

release: setup db-schema ## Create GitHub Release
	$(eval version := $(shell date '+%Y.%m.%d'))
	set -e
	sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+.*"/version = "$(version)"/' pyproject.toml
	uv sync --inexact
	git add --all
	rm -rf dist/
	uv build --wheel
	gpg --detach-sign dist/*.whl
	git commit -m "Release: $(NAME) v$(version)" || true
	git push origin main
	gh release create $(version) --title "$(version)" --generate-notes ./dist/*.*

###############################################################################
# Google CLI
###############################################################################

google_project ?= lab5-gcp-dev1
google_region ?= us-central1

GOOGLE_PROJECT_ID ?= $(google_project)
GOOGLE_REGION ?= $(google_region)

google: google-config

google-auth:
	gcloud auth revoke --all
	gcloud auth login --update-adc --no-launch-browser

google-config:
	set -e
	gcloud auth application-default set-quota-project $(google_project)
	gcloud config set core/project $(google_project)
	gcloud config set compute/region $(google_region)
	gcloud config list

###############################################################################
# Docker Compose
###############################################################################

POSTGRES_HOST ?= localhost
POSTGRES_PORT ?= 5432
POSTGRES_DB ?= invoice_ocr
POSTGRES_USER ?= postgres
POSTGRES_PASSWORD ?= postgres

POSTGRES_URI := postgres://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)

.docker-init:
	set -e
	docker volume create postgres
	docker volume create invoice-ocr
	touch $@

docker-start: .docker-init ## Start Docker Compose
	docker compose up --detach --remove-orphans --wait

docker-stop: ## Stop Docker Compose
	docker compose down --remove-orphans

docker-status: ## Show Docker Compose status
	docker container ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
	echo

###############################################################################
# DB Schema Management https://atlasgo.io/docs
###############################################################################

db_tables := invoices
atlas_db := atlas_validate

db-init: ## Initialize Database
	-psql $(POSTGRES_URI) -c 'CREATE DATABASE $(POSTGRES_DB);'
	-psql $(POSTGRES_URI) -c 'CREATE DATABASE $(atlas_db);'

db-schema: ## Apply Database Schema
	$(info ==> Applying Database Schema...<==)
	atlas schema apply \
	--url $(POSTGRES_URI)/$(POSTGRES_DB)?sslmode=disable \
	--dev-url $(POSTGRES_URI)/$(atlas_db)?sslmode=disable \
	--to file://src/invoice_ocr/schema.sql

db-inspect: ## Inspect Database Schema
	atlas schema inspect \
	--url $(POSTGRES_URI)/$(POSTGRES_DB)?sslmode=disable \
	--format '{{ sql . }}'

db-clean: ## Drop Database Schema
	-psql $(POSTGRES_URI)/$(POSTGRES_DB) -c 'DROP TABLE invoices;'

###############################################################################
# Colors and Headers
###############################################################################

TERM := xterm-256color

black := $$(tput setaf 0)
red := $$(tput setaf 1)
green := $$(tput setaf 2)
yellow := $$(tput setaf 3)
blue := $$(tput setaf 4)
magenta := $$(tput setaf 5)
cyan := $$(tput setaf 6)
white := $$(tput setaf 7)
reset := $$(tput sgr0)

define header
echo "$(blue)==> $(1) <==$(reset)"
endef

define var
echo "$(magenta)$(1)$(reset)=$(yellow)$(2)$(reset)"
endef

prompt:
	echo -n "$(blue)Continue $(yellow)$(google_project)? $(green)(yes/no)$(reset)"
	read -p ": " answer && [ "$$answer" = "yes" ] || exit 1
