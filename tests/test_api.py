import datetime
import ipaddress

from decimal import Decimal
from unittest import mock

import pytest
import responses

from proxy6.api import (
    Account,
    _clean_params,
    PriceInformation,
    Proxy6,
    ProxyState,
    ProxyVersion,
)
from proxy6.errors import Proxy6Error
from proxy6.types import Proxy, ProxyType, Purchase

from .factories import ProxyFactory


@responses.activate
def test_requests():
    """
    Requests should be formed according to the following layout

        https://proxy6.net/api/{api_key}/{method}?{params}

    and return JSON data stripped from the `'status'` field
    """
    api_key = '1e339044'

    client = Proxy6(api_key=api_key)

    responses.add(
        responses.GET,
        'https://proxy6.net/api/1e339044/foo',
        json={'status': 'yes', 'result': 3},
    )

    data = client._request('foo', params={'a': 1, 'b': 2})
    assert data == {'result': 3}

    assert len(responses.calls) == 1

    request = responses.calls[0].request
    assert request.url == 'https://proxy6.net/api/1e339044/foo?a=1&b=2'

    # request should work with no param

    data = client._request('foo')
    assert data == {'result': 3}

    assert len(responses.calls) == 2

    request = responses.calls[1].request
    assert request.url == 'https://proxy6.net/api/1e339044/foo'


@responses.activate
@mock.patch('proxy6.errors.select')
def test_requests_failed(select):
    """
    Requests not having the `'status'` result field set to `'yes'` should
    raise error according to errors.select
    """
    client = Proxy6(api_key='key')

    class MockError(Proxy6Error):
        """Mock error"""

        code = 123
        description = "Lorem ipsum"

    select.return_value = MockError

    responses.add(
        responses.GET,
        'https://proxy6.net/api/key/foo',
        json={'status': 'no', 'error_id': 123, 'error': "Lorem ipsum"},
    )

    with pytest.raises(MockError) as exc_info:
        client._request('foo')

    e = exc_info.value
    assert e.code == 123
    assert str(e) == "Mock error"


def test_clean_params():
    assert _clean_params() == {}
    assert _clean_params(foo=None) == {}
    assert _clean_params(foo=0) == {'foo': 0}
    assert _clean_params(foo=0, bar="", baz=None) == {'foo': 0, 'bar': ""}

    import enum

    class E(enum.Enum):
        A = 'a'
        B = 'b'

    assert _clean_params(foo=E.A, bar=E.B) == {'foo': 'a', 'bar': 'b'}


@mock.patch('proxy6.api.Proxy6._request')
def test_get_account(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'list': ['ru', 'ua', 'us'],
    }

    assert client.get_account() == Account(
        user_id=1, balance=Decimal('48.80'), currency='RUB'
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_get_price(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'price': 1800,
        'price_single': 0.6,
        'period': 30,
        'count': 100,
    }

    assert client.get_price(count=100, period=30) == PriceInformation(
        price=1800, price_single=0.6, period=30, count=100, currency='RUB'
    )

    request.assert_called_once_with('getprice', params={'count': 100, 'period': 30})
    request.reset_mock()

    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'price': 600,
        'price_single': 0.2,
        'period': 15,
        'count': 200,
    }

    assert client.get_price(
        count=200, period=15, version=ProxyVersion.IPv4
    ) == PriceInformation(
        price=600, price_single=0.2, period=15, count=200, currency='RUB'
    )

    request.assert_called_once_with(
        'getprice',
        params={'count': 200, 'period': 15, 'version': ProxyVersion.IPv4.value},
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_get_count(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'count': 971,
    }

    assert client.get_count(country='ru') == 971

    request.assert_called_once_with('getcount', params={'country': 'ru'})
    request.reset_mock()

    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'count': 179,
    }

    assert client.get_count(country='ru', version=ProxyVersion.IPv4) == 179

    request.assert_called_once_with(
        'getcount', params={'country': 'ru', 'version': ProxyVersion.IPv4.value}
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_get_country(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'list': ['ru', 'ua', 'us'],
    }

    assert client.get_countries() == ['ru', 'ua', 'us']

    request.assert_called_once_with('getcountry', params={})
    request.reset_mock()

    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'list': ['de', 'fr', 'es'],
    }

    assert client.get_countries(version=ProxyVersion.IPv4) == ['de', 'fr', 'es']

    request.assert_called_once_with(
        'getcountry', params={'version': ProxyVersion.IPv4.value}
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_get_proxies(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'list_count': 2,
        'list': [
            {
                'id': '11',
                'ip': '2a00:1838:32:19f:45fb:2640::330',
                'host': '185.22.134.250',
                'port': '7330',
                'user': '5svBNZ',
                'pass': 'iagn2d',
                'version': '6',
                'type': 'http',
                'country': 'ru',
                'date': '2016-06-19 16:32:39',
                'date_end': '2016-07-12 11:50:41',
                'unixtime': 1466379159,
                'unixtime_end': 1468349441,
                'descr': "foo",
                'active': '1',
            },
            {
                'id': '14',
                'ip': '123.234.213.0',
                'host': '185.22.134.242',
                'port': '7386',
                'user': 'nV5TFK',
                'pass': '3Itr1t',
                'version': '3',
                'type': 'socks',
                'country': 'ru',
                'date': '2016-06-27 16:06:22',
                'date_end': '2016-07-11 16:06:22',
                'unixtime': 1466379151,
                'unixtime_end': 1468349441,
                'descr': "foo",
                'active': '1',
            },
        ],
    }

    assert client.get_proxies(state=ProxyState.ACTIVE, description="foo") == [
        Proxy(
            id=11,
            ip=ipaddress.ip_address('2a00:1838:32:19f:45fb:2640::330'),
            host='185.22.134.250',
            port=7330,
            user='5svBNZ',
            password='iagn2d',
            version=ProxyVersion.IPv6,
            type=ProxyType.HTTP,
            country='ru',
            purchased_at=datetime.datetime(2016, 6, 19, 16, 32, 39),
            expires_at=datetime.datetime(2016, 7, 12, 11, 50, 41),
            description="foo",
            active=True,
        ),
        Proxy(
            id=14,
            ip=ipaddress.ip_address('123.234.213.0'),
            host='185.22.134.242',
            port=7386,
            user='nV5TFK',
            password='3Itr1t',
            version=ProxyVersion.IPv4_SHARED,
            type=ProxyType.SOCKS5,
            country='ru',
            purchased_at=datetime.datetime(2016, 6, 27, 16, 6, 22),
            expires_at=datetime.datetime(2016, 7, 11, 16, 6, 22),
            description="foo",
            active=True,
        ),
    ]

    request.assert_called_once_with(
        'getproxy',
        params={'state': ProxyState.ACTIVE.value, 'descr': "foo", 'nokey': True},
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_set_type(request, client):
    request.return_value = {'user_id': '1', 'balance': '48.80', 'currency': 'RUB'}

    proxies = (
        ProxyFactory(id=10),
        ProxyFactory(id=11),
        ProxyFactory(id=12),
        ProxyFactory(id=15),
    )
    client.set_type(proxies=proxies, type=ProxyType.SOCKS5)

    request.assert_called_once_with(
        'settype', params={'ids': '10,11,12,15', 'type': ProxyType.SOCKS5.value}
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_set_description(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'count': 4,
    }

    proxies = (
        ProxyFactory(id=10),
        ProxyFactory(id=11),
        ProxyFactory(id=12),
        ProxyFactory(id=15),
    )
    assert client.set_description(proxies=proxies, old="test", new="newtest") == 4

    request.assert_called_once_with(
        'setdescr', params={'ids': '10,11,12,15', 'old': "test", 'new': "newtest"}
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_buy(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'count': 1,
        'price': 6.3,
        'price_single': 0.9,
        'period': 7,
        'country': 'ru',
        'list': [
            {
                'id': '15',
                'ip': '2a00:1838:32:19f:45fb:2640::330',
                'host': '185.22.134.250',
                'port': '7330',
                'user': '5svBNZ',
                'pass': 'iagn2d',
                'version': '6',
                'type': 'http',
                'date': '2016-06-19 16:32:39',
                'date_end': '2016-07-12 11:50:41',
                'unixtime': 1466379159,
                'unixtime_end': 1468349441,
                'active': '1',
            }
        ],
    }

    assert client.buy(count=1, period=7, country='ru') == Purchase(
        price=6.3,
        price_single=0.9,
        period=7,
        count=1,
        currency='RUB',
        proxies=[
            Proxy(
                id=15,
                ip=ipaddress.ip_address('2a00:1838:32:19f:45fb:2640::330'),
                host='185.22.134.250',
                port=7330,
                country='ru',
                user='5svBNZ',
                password='iagn2d',
                version=ProxyVersion.IPv6,
                type=ProxyType.HTTP,
                purchased_at=datetime.datetime(2016, 6, 19, 16, 32, 39),
                expires_at=datetime.datetime(2016, 7, 12, 11, 50, 41),
                active=True,
                description="",
            )
        ],
    )

    request.assert_called_once_with(
        'buy', params={'count': 1, 'period': 7, 'country': 'ru', 'nokey': True}
    )
    request.reset_mock()

    client.buy(
        count=1,
        period=7,
        country='ru',
        version=ProxyVersion.IPv4,
        type=ProxyType.HTTP,
        description="foo",
        auto_renew=True,
    )

    request.assert_called_once_with(
        'buy',
        params={
            'count': 1,
            'period': 7,
            'country': 'ru',
            'version': ProxyVersion.IPv4.value,
            'type': ProxyType.HTTP.value,
            'descr': "foo",
            'auto_prolong': True,
            'nokey': True,
        },
    )


@mock.patch('proxy6.api.Proxy6._request')
def test_prolong(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': 29,
        'currency': 'RUB',
        'price': 12.6,
        'price_single': 0.9,
        'period': 7,
        'count': 2,
        'list': {
            '15': {
                'id': 15,
                'date_end': '2016-07-15 06:30:27',
                'unixtime_end': 1468349441,
            },
            '16': {
                'id': 16,
                'date_end': '2016-07-16 09:31:21',
                'unixtime_end': 1468349529,
            },
        },
    }

    proxies = (ProxyFactory(id=15), ProxyFactory(id=16))
    prolongation = client.prolong(proxies=proxies, period=7)

    assert prolongation.price == 12.6
    assert prolongation.price_single == 0.9
    assert prolongation.period == 7
    assert prolongation.count == 2
    assert prolongation.currency == 'RUB'

    a, b = prolongation.proxies
    assert a.id == 15 and a.expires_at == datetime.datetime(2016, 7, 15, 6, 30, 27)
    assert b.id == 16 and b.expires_at == datetime.datetime(2016, 7, 16, 9, 31, 21)

    request.assert_called_once_with('prolong', params={'period': 7, 'ids': '15,16'})


@mock.patch('proxy6.api.Proxy6._request')
def test_delete(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'count': 2,
    }

    proxies = (ProxyFactory(id=15), ProxyFactory(id=16))
    assert client.delete(proxies=proxies) == 2

    request.assert_called_once_with('delete', params={'ids': '15,16'})


@mock.patch('proxy6.api.Proxy6._request')
def test_delete_by_description(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'count': 2,
    }

    assert client.delete_by_description(description="foo") == 2

    request.assert_called_once_with('delete', params={'descr': "foo"})


@mock.patch('proxy6.api.Proxy6._request')
def test_is_proxy_valid(request, client):
    request.return_value = {
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'proxy_id': 15,
        'proxy_status': True,
    }

    assert client.is_proxy_valid(proxy_id=15)

    request.assert_called_once_with('check', params={'ids': 15})
