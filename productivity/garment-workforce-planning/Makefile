.PHONY: data validate test train plan

data:
	python scripts/download_data.py

validate:
	python scripts/validate_data.py

test:
	pytest -q

train:
	python -m src.train --config config.yaml

plan:
	python -m src.plan --config config.yaml
