# Where: Makefile
# What: Local Docker/uv entrypoints plus a shorthand target for experiment run.py execution.
# Why: Keep common workflows short and forward Hydra overrides from `make` safely.

CPU_FLAG :=
ifneq ($(CPU),)
    CPU_FLAG := -f compose.cpu.yaml
endif

empty :=
space := $(empty) $(empty)
DOCKER_COMPOSE := docker compose$(if $(CPU_FLAG),$(space)$(CPU_FLAG),)

# GNU make stores command-line variable overrides in reverse order, so reverse
# them again before forwarding them to Hydra.
reverse = $(if $(1),$(call reverse,$(wordlist 2,$(words $(1)),$(1))) $(firstword $(1)))
RUN_PYTHON_OVERRIDES := $(strip $(call reverse,$(filter-out CPU=%,$(MAKEOVERRIDES))))

default: build

build:
	$(DOCKER_COMPOSE) build

bash:
	$(DOCKER_COMPOSE) run --rm kaggle bash

jupyter:
	$(DOCKER_COMPOSE) up

down:
	$(DOCKER_COMPOSE) down

# === uv環境用コマンド ===
uv-setup:
	uv sync --group dev

uv-jupyter:
	uv run jupyter lab --port=8889

.PHONY: default build bash jupyter down uv-setup uv-jupyter FORCE

exp%/run.py: FORCE
	$(DOCKER_COMPOSE) run --rm -d -t kaggle python experiments/$@ $(RUN_PYTHON_OVERRIDES)

FORCE:
