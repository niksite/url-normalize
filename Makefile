install:
	@uv pip install -e ".[dev]"

tox:
	@uvx --with tox-uv tox

update: install
	@uv run -- pre-commit autoupdate

lint: install
	@uv run -- pre-commit run -a

test: install
	@uv run -- pytest

build:
	@rm -rf dist
	@uv build

publish: build
	@uv publish

