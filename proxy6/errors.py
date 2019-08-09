class Proxy6Error(Exception):
    """Proxy6 API error"""

    def __init__(self, *, code: int = None, description: str = None):
        if code is not None:
            self.code = code
        if description is not None:
            self.description = description

        super().__init__(self.__class__.__doc__)


class NoMoneyError(Proxy6Error):
    """Balance error. Zero or low balance on your account"""

    code = 400
    description = "Error no money"


def select(data: dict) -> Proxy6Error:
    code = data.pop('error_id')
    description = data.pop('error')

    for Error in (NoMoneyError,):
        if code == Error.code:
            assert description == Error.description
            return Error

    return Proxy6Error(code=code, description=description)
