import copy
import enum

from decimal import Decimal
from typing import Iterable, List, Optional, Sequence
from urllib.parse import urljoin

import requests

from . import errors, schemas
from .types import (
    Account,
    Purchase,
    PriceInformation,
    Prolongation,
    Proxy,
    ProxyState,
    ProxyType,
    ProxyVersion,
)


def _clean_params(**kwargs) -> dict:
    return {
        k: (v.value if isinstance(v, enum.Enum) else v)
        for k, v in kwargs.items()
        if v is not None
    }


def _format_list_param(items: list) -> str:
    """Format list for Proxy6's non-standard GET query parameters format"""
    return ','.join(map(str, items))


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
            raise errors.select(data)

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
        params = _clean_params(count=count, period=period, version=version)
        data = self._request('getprice', params=params)

        return schemas.PriceInformationSchema().load(data)

    def get_count(self, *, country: str, version: Optional[ProxyVersion] = None) -> int:
        """
        Get information about the amount of proxies available to purchase for
        a selected country

        :param count: Country code in ISO2 format
        :param version: Proxy version (default is IPv6)

        :returns: available amount of proxies

        :raises Proxy6Error:
        """
        params = _clean_params(country=country, version=version)
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
        params = _clean_params(version=version)
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
        params = _clean_params(state=state, descr=description, nokey=True)
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
        params = _clean_params(
            ids=_format_list_param(proxy.id for proxy in proxies), type=type
        )
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

        params = _clean_params(
            new=new, old=old, ids=_format_list_param(proxy.id for proxy in proxies)
        )
        return self._request('setdescr', params=params).pop('count')

    def buy(
        self,
        *,
        count: int,
        period: int,
        country: str,
        version: Optional[ProxyVersion] = None,
        type: Optional[ProxyType] = None,
        description: str = "",
        auto_renew: bool = False,
    ) -> Purchase:
        """
        Buy proxies

        :param count: amount of proxies to purchase
        :param period: period for which proxies are purchased in days
        :param country: country in ISO2 format
        :param version: proxy version, defaults to IPv6
        :param type: proxy protocol
        :param description: technical comment for proxies list, max 50 characters
        :param auto_renew: enable auto-renewal for purchased proxies

        :returns: purchase information

        :raises Proxy6Error:
        """
        assert len(description) <= 50

        params = _clean_params(
            count=count,
            period=period,
            country=country,
            version=version,
            type=type,
            descr=description or None,
            auto_prolong=auto_renew or None,
            nokey=True,
        )
        return schemas.PurchaseSchema().load(
            {'description': description or "", **self._request('buy', params=params)}
        )

    def prolong(self, *, period: int, proxies: Iterable[Proxy]) -> Prolongation:
        """
        Extend existing proxies period

        :param period: extension of the period in days
        :param proxies: proxies to prolong

        :returns: prolongation information

        :raises Proxy6Error:
        """
        proxies = copy.deepcopy(proxies)

        params = _clean_params(
            period=period, ids=_format_list_param(proxy.id for proxy in proxies)
        )
        return schemas.ProlongationSchema(proxies).load(
            self._request('prolong', params=params)
        )

    def delete(self, *, proxies: Iterable[Proxy]) -> int:
        """
        Delete proxies

        :param proxies: proxies to delete

        :returns: amount of proxies deleted

        :raises Proxy6Error:
        """
        params = _clean_params(ids=_format_list_param(proxy.id for proxy in proxies))
        return self._request('delete', params=params)['count']

    def delete_by_description(self, *, description: str) -> int:
        """
        Delete proxies having the given description

        :param description: description to select proxies with

        :returns: amount of proxies deleted

        :raises Proxy6Error:
        """
        params = _clean_params(descr=description)
        return self._request('delete', params=params)['count']

    def is_proxy_valid(self, *, proxy_id: int) -> bool:
        """
        Checks the validity of a proxy

        :param proxy_id: proxy identifier

        :returns: proxy validity status

        :raises Proxy6Error:
        """
        params = _clean_params(ids=proxy_id)
        data = self._request('check', params=params)

        self.__class__._pop_common_fields(data)

        assert data.pop('proxy_id') == proxy_id
        assert len(data) == 1

        return data['proxy_status']
