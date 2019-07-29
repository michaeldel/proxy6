import enum

from typing import Optional
from urllib.parse import urljoin

import requests


class ProxyVersion(enum.IntEnum):
    IPv4 = 4
    IPv4_SHARED = 3
    IPv6 = 6


def _cleaned_dict(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


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

    @staticmethod
    def _pop_common_fields(data: dict):
        for key in ('status', 'user_id', 'balance', 'currency'):
            del data[key]

    def get_price(
        self, *, count: int, period: int, version: Optional[ProxyVersion] = None
    ) -> dict:
        """
        Used to get information about the cost of the order, depending on the
        period and number of proxies

        :param count: Number of proxies
        :param period: Number of days
        :param version: Proxy version (default is IPv6)

        :returns: price data

        :raises Proxy6Error:
        """
        params = _cleaned_dict(count=count, period=period, version=version)
        data = self._request('getprice', params=params)

        self.__class__._pop_common_fields(data)

        return data
