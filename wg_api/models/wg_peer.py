from typing import List, Optional
from ipaddress import IPv4Interface, IPv4Address, \
    AddressValueError
from pydantic import BaseModel, validator


class WGPeer(BaseModel):

    public_key: str
    keepalive: Optional[int]
    end_point: Optional[str]
    preshared_key: Optional[str]
    allowed_ips: Optional[List[IPv4Interface]]

    @classmethod
    def validate_port(cls, port: Optional[int]) -> Optional[int]:
        if not (port is None or 0 <= port < 65536):
            raise ValueError('listen_port must be in the range [0;65535]')

        return port

    @validator('keepalive')
    def validate_keepalive(cls, keepalive: Optional[int]) -> Optional[int]:
        if not (keepalive is None or 0 < keepalive < 65536):
            raise ValueError('keepalive must be in the range [1;65535]')

        return keepalive

    @validator('end_point')
    def validate_endpoint(cls, endpoint: Optional[str]) -> Optional[str]:
        if endpoint is None:
            return None

        address, _, port = endpoint.partition(':')
        if not (address and port):
            raise ValueError('end_point must match the format <address>:<port>')

        try:
            address = IPv4Address(address)
        except AddressValueError as ex:
            raise ValueError('end_point address is incorrect') from ex

        try:
            port = cls.validate_port(int(port))
        except (ValueError, TypeError) as ex:
            raise ValueError('end_point port is incorrect') from ex

        return f'{address}:{port}'

    class Config:
        validate_assignment = True
