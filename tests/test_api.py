import urllib.parse

import responses

from proxy6.api import Proxy6


@responses.activate
def test_requests():
    """
    Requests should be formed according to the following layout

        https://proxy6.net/api/{api_key}/{method}?{params}

    and return JSON data
    """
    api_key = '1e339044'

    client = Proxy6(api_key=api_key)

    responses.add(
        responses.GET,
        'https://proxy6.net/api/1e339044/foo',
        json={'success': 'yes'}
    )

    data = client._request('foo', params={'a': 1, 'b': 2})
    assert data == {'success': 'yes'}

    assert len(responses.calls) == 1

    request = responses.calls[0].request
    assert request.url == 'https://proxy6.net/api/1e339044/foo?a=1&b=2'
