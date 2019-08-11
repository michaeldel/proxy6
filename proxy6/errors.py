class Proxy6Error(Exception):
    """Proxy6 API error"""

    def __init__(self, *, code: int = None, description: str = None):
        if code is not None:
            self.code = code
        if description is not None:
            self.description = description

        if self.__class__ != Proxy6Error:
            super().__init__(self.__class__.__doc__)
        else:
            super().__init__(f"{description} (code {code})")


class CountError(Proxy6Error):
    """Wrong proxies quantity, wrong amount or no quantity input"""

    code = 200
    description = "Error count"


class NoMoneyError(Proxy6Error):
    """Balance error. Zero or low balance on your account"""

    code = 400
    description = "Error no money"


def select(data: dict) -> Proxy6Error:
    code = data.pop('error_id')
    description = data.pop('error')

    for Error in (CountError, NoMoneyError):
        if code == Error.code:
            assert description == Error.description
            return Error

    return Proxy6Error(code=code, description=description)
