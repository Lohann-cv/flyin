MAP ?= maps/easy/01_linear_path.txt
DELAY ?= 0.5

install:
	uv venv --python 3.13
	uv sync

run:
	@echo "If you want to choose the map put 'make run MAP=<>'"
	uv run main.py $(MAP)

visual:
	@echo "If you want to choose the map put 'make visual MAP=<>' or if you want to put a choosen delay do 'make visual DELAY=<>'"
	uv run main.py $(MAP) --visual --delay=$(DELAY)

debug:
	uv run python -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

lint:
	uv run flake8 . --exclude=.venv
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude "(.venv)"

lint-strict:
	uv run flake8 . --exclude=.venv
	uv run mypy . --strict --exclude "(.venv)"

.PHONY: install run visual debug clean lint lint-strict
