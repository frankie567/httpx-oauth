PIPENV_RUN := pipenv run

isort-src:
	$(PIPENV_RUN) isort -rc ./httpx_oauth

isort-docs:
	$(PIPENV_RUN) isort -rc ./docs/src -o httpx_oauth

format: isort-src isort-docs
	$(PIPENV_RUN) black .

test:
	$(PIPENV_RUN) pytest --cov=httpx_oauth/

docs-serve:
	$(PIPENV_RUN) mkdocs serve

docs-publish:
	$(PIPENV_RUN) mkdocs gh-deploy

bumpversion-major:
	$(PIPENV_RUN) bumpversion major

bumpversion-minor:
	$(PIPENV_RUN) bumpversion minor

bumpversion-patch:
	$(PIPENV_RUN) bumpversion patch
