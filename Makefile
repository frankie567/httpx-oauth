install:
	python -m pip install --upgrade pip
	pip install flit
	flit install --deps develop

isort-src:
	isort ./httpx_oauth

format: isort-src
	black .

test:
	pytest --cov=httpx_oauth/ --cov-report=term-missing --cov-fail-under=100

docs-serve:
	mkdocs serve

docs-publish:
	mkdocs gh-deploy

bumpversion-major:
	bumpversion major

bumpversion-minor:
	bumpversion minor

bumpversion-patch:
	bumpversion patch
