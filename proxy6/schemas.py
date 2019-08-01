import enum
import ipaddress

from marshmallow import EXCLUDE, fields, post_load, Schema

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


class ProxySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)

    ip = IPAddressField(required=True)

    host = fields.String(required=True)
    port = fields.Integer(required=True)

    user = fields.String(required=True)
    password = fields.String(required=True, data_key='pass')

    type = EnumField(types.ProxyType, required=True)
    country = fields.String(required=True)

    date_purchased = fields.DateTime(required=True, data_key='date')
    date_expires = fields.DateTime(required=True, data_key='date_end')

    description = fields.String(required=True, data_key='descr')

    active = fields.Boolean(required=True)

    @post_load
    def make_proxy(self, data, **kwargs):
        return types.Proxy(**data)
