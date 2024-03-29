import ipaddress

import factory

from proxy6.types import Proxy, ProxyType, ProxyVersion


class ProxyFactory(factory.Factory):
    class Meta:
        model = Proxy

    id = factory.Sequence(lambda i: i)

    ip = factory.Sequence(ipaddress.ip_address)
    host = factory.Sequence(lambda i: str(ipaddress.ip_address(i)))
    port = factory.Faker('pyint')

    user = factory.Sequence(lambda i: f'user{i}')
    password = 'password'

    version = ProxyVersion.IPv6
    type = ProxyType.HTTP
    country = 'ru'

    purchased_at = factory.Faker('past_datetime', start_date='-30d')
    expires_at = factory.Faker('future_datetime', end_date='+30d')

    active = True
