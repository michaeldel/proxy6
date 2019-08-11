import toml

from proxy6 import __version__


def test_version():
    assert __version__ == toml.load('pyproject.toml')['tool']['poetry']['version']
