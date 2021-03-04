isort-src:
	isort ./httpx_oauth

format: isort-src
	black .

test:
	pytest --cov=httpx_oauth/

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
