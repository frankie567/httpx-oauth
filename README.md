# HTTPX OAuth

<p align="center">
    <em>Async OAuth client using HTTPX</em>
</p>

[![build](https://github.com/frankie567/httpx-oauth/workflows/Build/badge.svg)](https://github.com/frankie567/httpx-oauth/actions)
[![codecov](https://codecov.io/gh/frankie567/httpx-oauth/branch/master/graph/badge.svg)](https://codecov.io/gh/frankie567/httpx-oauth)
[![PyPI version](https://badge.fury.io/py/httpx-oauth.svg)](https://badge.fury.io/py/httpx-oauth)

<p align="center">
    <a href="https://www.buymeacoffee.com/frankie567"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=frankie567&button_colour=FF5F5F&font_colour=ffffff&font_family=Lato&outline_colour=000000&coffee_colour=FFDD00"></a>
</p>

---

**Documentation**: <a href="https://frankie567.github.io/httpx-oauth/" target="_blank">https://frankie567.github.io/httpx-oauth/</a>

**Source Code**: <a href="https://github.com/frankie567/httpx-oauth" target="_blank">https://github.com/frankie567/httpx-oauth</a>

---

## Installation

```bash
pip install httpx-oauth
```

## Development

### Setup environment

You should create a virtual environment and activate it:

```bash
python -m venv venv/
```

```bash
source venv/bin/activate
```

And then install the development dependencies:

```bash
pip install -r requirements.dev.txt
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
