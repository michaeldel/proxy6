check: lint test

lint:
	poetry check
	black --check .

test:
	pytest
