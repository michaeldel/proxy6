check: lint test

lint:
	black --check .

test:
	pytest
