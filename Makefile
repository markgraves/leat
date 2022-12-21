# Makefile for developing leat

all: # Prepare code for committing to git.
	$(MAKE) format
#	$(MAKE) lint
	$(MAKE) test

# Automatically format python code. WARNING: unsaved changes may be lost.
black:
	python -m black --extend-exclude data leat tests

check-black:  
	python -m black --extend-exclude data leat tests --check

# Automatically format python code. WARNING: unsaved changes may be lost.
format: black

# Lint Python code.
lint:   check-black mypy

mypy:
	python -m mypy leat/core
	python -m mypy leat/store
	python -m mypy leat/search

# Test Python code.
test:
	python -m pytest tests/unit/
	python -m pytest tests/integration/



