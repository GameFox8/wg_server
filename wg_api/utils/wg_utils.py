import re
import asyncio
from typing import Any
from base64 import b64encode
from secrets import token_bytes
from ipaddress import IPv4Interface
from wg_api.utils.exceptions import ShellError, \
    IncorrectInterfaceName


PIPE = asyncio.subprocess.PIPE


async def shell_exec(cmd: str, *input_args: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        f"/bin/bash -c '{escape(cmd)}'",
        stdin=PIPE, stdout=PIPE, stderr=PIPE
    )
    stdout, stderr = await proc.communicate('\n'.join(input_args).encode('utf-8') if input_args else None)
    if stderr and proc.returncode != 0:
        raise ShellError(unescape(cmd), stderr.decode('utf-8').strip(), proc.returncode)

    return stdout.decode('utf-8').strip()


def escape_to_str(value: Any) -> str:
    return escape(str(value))


def escape(value: str) -> str:
    return value.replace("'", "'\\''")


def unescape(value: str) -> str:
    return value.replace("'\\''", "'")


async def get_private_key() -> str:
    return b64encode(token_bytes(32)).decode('utf-8')


async def get_public_key(private_key: str) -> str:
    return str(await shell_exec('wg pubkey', private_key)).strip()


def check_interface_name(name: str):
    if not (name and re.match(r'^[a-zA-Z0-9_=+.-]{1,15}$', name)):
        raise IncorrectInterfaceName(name)
