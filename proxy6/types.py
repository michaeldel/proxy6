import datetime
import enum
import ipaddress

from dataclasses import dataclass
from typing import Union


class ProxyType(enum.Enum):
    HTTP = 'http'
    SOCKS5 = 'socks'


@dataclass
class Proxy:
    id: int

    ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

    host: str
    port: int

    user: str
    password: str

    type: ProxyType
    country: str

    date_purchased: datetime.datetime
    date_expires: datetime.datetime

    description: str

    active: bool
