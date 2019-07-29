import urllib.parse

from unittest import mock

import pytest
import responses

from proxy6.api import Proxy6, ProxyVersion, Proxy6Error


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
def test_requests_failed():
    """
    Requests not having the `'status'` result field set to `'yes'` should
    raise a Proxy6Error
    """
    client = Proxy6(api_key='key')

    responses.add(
        responses.GET,
        'https://proxy6.net/api/key/foo',
        json={'status': 'no', 'error_id': 123, 'error': "Lorem ipsum"},
    )

    with pytest.raises(Proxy6Error) as exc_info:
        client._request('foo')

    e = exc_info.value
    assert e.code == 123
    assert str(e) == "Lorem ipsum"


@mock.patch('proxy6.api.Proxy6._request')
def test_get_price(request, client):
    request.return_value = {
        'status': 'yes',
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'price': 1800,
        'price_single': 0.6,
        'period': 30,
        'count': 100,
    }

    assert client.get_price(count=100, period=30) == {
        'price': 1800,
        'price_single': 0.6,
        'period': 30,
        'count': 100,
    }

    request.assert_called_once_with('getprice', params={'count': 100, 'period': 30})
    request.reset_mock()

    request.return_value = {
        'status': 'yes',
        'user_id': '1',
        'balance': '48.80',
        'currency': 'RUB',
        'price': 600,
        'price_single': 0.2,
        'period': 15,
        'count': 200,
    }

    assert client.get_price(count=200, period=15, version=ProxyVersion.IPv4) == {
        'price': 600,
        'price_single': 0.2,
        'period': 15,
        'count': 200,
    }

    request.assert_called_once_with(
        'getprice', params={'count': 200, 'period': 15, 'version': ProxyVersion.IPv4}
    )
