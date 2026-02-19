.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  install	Install dependencies"
	@echo "  lint   	Run all linters"
	@echo "  test   	Run all tests"
	@echo "  tag    	Create release tag"

# -- dependencies --------------------------------------------------------------

.PHONY: install
install:
	uv sync --locked

# -- linting -------------------------------------------------------------------

.PHONY: lint
lint: ruff unbehead mypy

.PHONY: ruff
ruff:
	ruff check .

.PHONY: mypy
mypy:
	# FIXME: Remove flag once it's possible to disable color via envvar.
	#        The uncolored output is necessary on CI for the matcher to work.
	mypy . --no-color-output

.PHONY: unbehead
unbehead:
	unbehead --check

# -- testing -------------------------------------------------------------------

.PHONY: test
test: pytest

.PHONY: pytest
pytest:
	pytest

# -- releasing -----------------------------------------------------------------

.PHONY: tag
tag:
	bin/tag.sh
