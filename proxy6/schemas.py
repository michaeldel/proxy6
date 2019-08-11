import enum
import ipaddress

from typing import Sequence

from marshmallow import EXCLUDE, fields, post_load, pre_load, Schema

from . import types


class IPAddressField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return ipaddress.ip_address(value)


class EnumField(fields.Field):
    def __init__(self, cls, *args, **kwargs):
        assert issubclass(cls, enum.Enum)
        self.enum = cls

        return super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return value.value

    def _deserialize(self, value, attr, data, **kwargs):
        return self.enum(value)


class PriceInformationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    price = fields.Float(required=True)
    price_single = fields.Float(required=True)
    period = fields.Integer(required=True)
    count = fields.Integer(required=True)
    currency = fields.String(required=True)

    @post_load
    def make_obj(self, data, **kwargs):
        return types.PriceInformation(**data)


class ProxySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)

    ip = IPAddressField(required=True)

    host = fields.String(required=True)
    port = fields.Integer(required=True)

    user = fields.String(required=True)
    password = fields.String(required=True, data_key='pass')

    version = EnumField(types.ProxyVersion, required=True)
    type = EnumField(types.ProxyType, required=True)
    country = fields.String(required=True)

    purchased_at = fields.DateTime(required=True, data_key='date')
    expires_at = fields.DateTime(required=True, data_key='date_end')

    description = fields.String(required=True, data_key='descr')

    active = fields.Boolean(required=True)

    @pre_load
    def parse_version(self, data, **kwargs):
        """Convert version from string to integer"""
        data['version'] = int(data['version'])
        return data

    @post_load
    def make_proxy(self, data, **kwargs):
        return types.Proxy(**data)


class PurchaseSchema(PriceInformationSchema):
    proxies = fields.Nested(ProxySchema, many=True, required=True, data_key='list')

    @pre_load
    def set_country_and_description(self, data, **kwargs):
        country = data.pop('country')
        description = data.pop('description')

        for proxy in data['list']:
            proxy.update({'country': country, 'descr': description})

        return data

    @post_load
    def make_obj(self, data, **kwargs):
        return types.Purchase(**data)


class ProlongationSchema(PriceInformationSchema):
    def __init__(self, existing_proxies: Sequence[types.Proxy], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_proxies = existing_proxies

    proxies = fields.Nested(ProxySchema, many=True, required=True, data_key='list')

    @pre_load
    def use_existing_proxies(self, data, **kwargs):
        temp = data.pop('list')
        assert len(temp) <= len(self.existing_proxies)

        used_proxies = (
            proxy for proxy in self.existing_proxies if str(proxy.id) in temp
        )

        data['list'] = [
            {**ProxySchema().dump(proxy), 'date_end': temp[str(proxy.id)]['date_end']}
            for proxy in used_proxies
        ]

        return data

    @post_load
    def make_obj(self, data, **kwargs):
        return types.Prolongation(**data)
