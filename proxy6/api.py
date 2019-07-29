import enum

from typing import List, Optional
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

    def get_count(self, *, country: str, version: Optional[ProxyVersion] = None) -> int:
        """
        Get information about the amount of proxies available to purchase for
        a selected country

        :param count: Country code in ISO2 format
        :param version: Proxy version (default is IPv6)

        :returns: available amount of proxies

        :raises Proxy6Error:
        """
        params = _cleaned_dict(country=country, version=version)
        data = self._request('getcount', params=params)

        self.__class__._pop_common_fields(data)
        assert len(data) == 1

        return data['count']

    def get_countries(self, *, version: Optional[ProxyVersion] = None) -> List[str]:
        """
        Get information on available for proxies purchase countries

        :param version: Proxy version (default is IPv6)

        :returns: list of country codes in ISO2 format

        :raises Proxy6Error:
        """
        params = _cleaned_dict(version=version)
        data = self._request('getcountry', params=params)

        self.__class__._pop_common_fields(data)
        assert len(data) == 1

        return data['list']

    def is_proxy_valid(self, *, proxy_id: int) -> bool:
        """
        Checks the validity of a proxy

        :param proxy_id: proxy identifier

        :returns: proxy validity status

        :raises Proxy6Error:
        """
        params = _cleaned_dict(ids=proxy_id)
        data = self._request('check', params=params)

        self.__class__._pop_common_fields(data)

        assert data.pop('proxy_id') == proxy_id
        assert len(data) == 1

        return data['proxy_status']
