import datetime
import enum
import ipaddress

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence, Union
from urllib.parse import urljoin

import requests

from . import schemas
from .types import Account, PriceInformation, Proxy, ProxyType


class ProxyVersion(enum.IntEnum):
    IPv4 = 4
    IPv4_SHARED = 3
    IPv6 = 6


class ProxyState(enum.Enum):
    ALL = 'all'
    ACTIVE = 'active'
    NOT_ACTIVE = 'expiring'
    EXPIRED = 'expired'


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
        for key in ('user_id', 'balance', 'currency'):
            del data[key]

    def get_account(self) -> Account:
        """
        Get account information

        :returns: account information

        :raises Proxy6Error:
        """
        data = self._request('getcountry')
        return Account(
            user_id=int(data['user_id']),
            balance=Decimal(data['balance']),
            currency=data['currency'],
        )

    def get_price(
        self, *, count: int, period: int, version: Optional[ProxyVersion] = None
    ) -> PriceInformation:
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

        return PriceInformation(
            price=data['price'],
            price_single=data['price_single'],
            period=data['period'],
            count=data['count'],
        )

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

    def get_proxies(
        self, *, state: Optional[ProxyState] = None, description: Optional[str] = None
    ) -> Sequence[Proxy]:
        """
        Get the list of proxies

        :param state: filter proxies by state
        :param description: filter proxies by technical comment

        :returns: list of proxies

        :raises Proxy6Error:
        """
        params = _cleaned_dict(state=state, descr=description, nokey=True)
        data = self._request('getproxy', params=params)

        self.__class__._pop_common_fields(data)

        proxies = schemas.ProxySchema().load(data['list'], many=True)

        assert len(proxies) == data['list_count']
        if description is not None:
            assert all(proxy.description == description for proxy in proxies)

        return proxies

    def set_type(self, *, proxies: Iterable[Proxy], type: ProxyType) -> None:
        """
        Change the protocol type of proxies

        :param proxies: proxies to set the protocol for
        :param type: new proxy type

        :raises Proxy6Error:
        """
        params = _cleaned_dict(ids=(proxy.id for proxy in proxies), type=type)
        self._request('settype', params=params)

    def set_description(
        self,
        *,
        new: str,
        old: Optional[str] = None,
        proxies: Optional[Iterable[Proxy]] = None,
    ) -> int:
        """
        Update technical comments in the proxy list that was added when buying

        :param proxies: proxies to set the description for
        :param new: new description
        :param old: technical comments to be changed, maximum 50 characters

        :returns: amount of proxies that wer changed

        :raises Proxy6Error:
        """
        assert old is None or len(old) <= 50

        params = _cleaned_dict(new=new, old=old, ids=(proxy.id for proxy in proxies))
        return self._request('setdescr', params=params).pop('count')

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
