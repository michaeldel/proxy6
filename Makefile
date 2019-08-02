check: lint test

lint:
	poetry check
	black --check .
	flake8

test:
	pytest
