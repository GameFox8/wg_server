class ShellError(RuntimeError):

    command = None
    err_msg = None
    err_code = None

    def __init__(self, command, err_msg=None, err_code=None):
        self.command = command
        self.err_msg = err_msg
        self.err_code = err_code

    def __str__(self):
        msg = f'Command "{self.command}" execution error'
        if self.err_msg:
            msg += f' "{self.err_msg}"'

        if self.err_code:
            msg += f' (code: {self.err_code})'

        return msg


class ParseConfigError(RuntimeError):

    reason = None
    option = None
    section = None
    file_path = None

    def __init__(self, section=None, option=None, reason=None, file_path=None):
        self.reason = reason
        self.option = option
        self.section = section
        self.file_path = file_path

    def __str__(self):
        msg = 'Configuration parsing error'
        if self.file_path:
            msg += f' (file: "{self.file_path}")'
        if self.section and self.option:
            msg += f' [{self.section}][{self.option}]'

        if self.reason:
            msg += f': {self.reason}'

        return msg


class BaseInterfaceException(ValueError):

    name = None
    message = None

    def __init__(self, name: str, msg: str = None):
        self.name = name
        self.message = msg

    def __str__(self):
        msg = f'Interface "{self.name}" error'
        if self.message:
            msg += f': "{self.message}"'

        return msg


class IncorrectInterfaceName(BaseInterfaceException):

    def __str__(self):
        return f'Incorrect interface name "{self.name}"'


class NotFoundInterface(BaseInterfaceException):

    def __str__(self):
        return f'Not found interface "{self.name}"'


class BasePeerException(BaseInterfaceException):

    public_key = None

    def __init__(self, name: str, public_key: str, msg: str = None):
        super().__init__(name, msg)
        self.public_key = public_key

    def __str__(self):
        msg = f'Peer "{self.public_key}" in interface "{self.name}" error'
        if self.message:
            msg += f': "{self.message}"'

        return msg


class NotFoundPeerException(BasePeerException):

    def __str__(self):
        return f'Interface "{self.name}" does not have a peer "{self.public_key}"'
