# Makefile for developing leat

all: # Prepare code for committing to git.
	$(MAKE) format
#	$(MAKE) lint
	$(MAKE) test

# Automatically format python code. WARNING: unsaved changes may be lost.
black:
	python -m black --extend-exclude data leat tests leat/search/config/config_data.py

check-black:  
	python -m black --extend-exclude data leat tests leat/search/config/config_data.py --check

# Automatically format python code. WARNING: unsaved changes may be lost.
format: black

# Lint Python code.
lint:   check-black mypy

mypy:
	python -m mypy leat/store
	python -m mypy leat/search

# Test Python code.
test:
	python -m pytest tests/unit/
	python -m pytest tests/integration/

# Generate documentation
doc:
	${MAKE} -C docs html


