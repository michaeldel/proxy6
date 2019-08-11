from __future__ import annotations

import datetime
import enum
import ipaddress

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence, Union


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


@dataclass
class Purchase(PriceInformation):
    proxies: Sequence[Proxy]


Prolongation = Purchase


class ProxyState(enum.Enum):
    ALL = 'all'
    ACTIVE = 'active'
    NOT_ACTIVE = 'expiring'
    EXPIRED = 'expired'


class ProxyType(enum.Enum):
    HTTP = 'http'
    SOCKS5 = 'socks'


class ProxyVersion(enum.IntEnum):
    IPv4 = 4
    IPv4_SHARED = 3
    IPv6 = 6


@dataclass
class Proxy:
    id: int

    ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

    host: str
    port: int

    user: str
    password: str

    version: ProxyVersion
    type: ProxyType
    country: str

    purchased_at: datetime.datetime
    expires_at: datetime.datetime

    active: bool
    description: str = field(default="")
