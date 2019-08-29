from .factories import ProxyFactory


def test_proxy_url():
    proxy = ProxyFactory(host='example.com', port=54321, user='alice', password='p')
    assert proxy.url == 'http://alice:p@example.com:54321'
