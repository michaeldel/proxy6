from urllib.parse import urljoin

import requests


class Proxy6:
    def __init__(self, api_key: str):
        self._base_url = f'https://proxy6.net/api/{api_key}/'
        self._session = requests.Session()

    def _request(self, method: str, params: dict) -> dict:
        url = urljoin(self._base_url, method)
        return self._session.get(url, params=params).json()
