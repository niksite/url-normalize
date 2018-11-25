tox:
	@tox

test:
	@py.test

build:
	@poetry build

publish: build
	@poetry publish
