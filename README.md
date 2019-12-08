# HTTPX OAuth

<p align="center">
    <em>Async OAuth client using HTTPX</em>
</p>

[![build](https://github.com/frankie567/httpx-oauth/workflows/Build/badge.svg)](https://github.com/frankie567/httpx-oauth/actions)
[![codecov](https://codecov.io/gh/frankie567/httpx-oauth/branch/master/graph/badge.svg)](https://codecov.io/gh/frankie567/httpx-oauth)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=frankie567/httpx-oauth)](https://dependabot.com)
[![PyPI version](https://badge.fury.io/py/httpx-oauth.svg)](https://badge.fury.io/py/httpx-oauth)

---

**Documentation**: <a href="https://frankie567.github.io/httpx-oauth/" target="_blank">https://frankie567.github.io/httpx-oauth/</a>

**Source Code**: <a href="https://github.com/frankie567/httpx-oauth" target="_blank">https://github.com/frankie567/httpx-oauth</a>

---

<p align="center">⚠️ This library is still in early development stage ⚠️</p>

## Installation

```bash
pip install httpx-oauth
```

## Development

### Setup environement

You should have [Pipenv](https://pipenv.readthedocs.io/en/latest/) installed. Then, you can install the dependencies with:

```bash
pipenv install --dev
```

After that, activate the virtual environment:

```bash
pipenv shell
```

### Run unit tests

You can run all the tests with:

```bash
make test
```

Alternatively, you can run `pytest` yourself:

```bash
pytest
```

### Format the code

Execute the following command to apply `isort` and `black` formatting:

```bash
make format
```

## License

This project is licensed under the terms of the MIT license.
