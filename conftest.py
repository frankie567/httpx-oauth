import httpx2

httpx2.alias_httpx()  # respx still imports `httpx`; make it patch the httpx2 classes.
