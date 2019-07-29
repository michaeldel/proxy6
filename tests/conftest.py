import pytest


@pytest.fixture
def api_key():
    import uuid

    return uuid.uuid4()


@pytest.fixture
def client(api_key):
    from proxy6.api import Proxy6

    return Proxy6(api_key)
