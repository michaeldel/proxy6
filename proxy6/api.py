from typing import Optional
from urllib.parse import urljoin

import requests


class Proxy6Error(Exception):
    def __init__(self, data: dict):
        self.code = data['error_id']
        super().__init__(data['error'])


class Proxy6:
    def __init__(self, api_key: str):
        self._base_url = f'https://proxy6.net/api/{api_key}/'
        self._session = requests.Session()

    def _request(self, method: str, *, params: Optional[dict] = None) -> dict:
        url = urljoin(self._base_url, method)
        response = self._session.get(url, params=params)

        assert response.ok  # TODO: handle other cases

        data = response.json()
        if data.pop('status') != 'yes':
            raise Proxy6Error(data)

        return data

