import datetime
import enum
import ipaddress

from dataclasses import dataclass
from decimal import Decimal
from typing import Union


@dataclass
class Account:
    user_id: int
    balance: Decimal
    currency: str


@dataclass
class PriceInformation:
    price: float
    price_single: float
    period: int
    count: int
    currency: str


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
