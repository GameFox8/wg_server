from typing import List, Optional
from pydantic import BaseModel, validator
from ipaddress import IPv4Address, IPv4Interface
from wg_api.models.wg_peer import WGPeer


class WGInterface(BaseModel):

    private_key: str
    address: List[IPv4Interface]
    mtu: Optional[int]
    table: Optional[str]
    fw_mark: Optional[str]
    save_conf: Optional[bool]
    listen_port: Optional[int]
    pre_up: Optional[List[str]]
    post_up: Optional[List[str]]
    pre_down: Optional[List[str]]
    post_down: Optional[List[str]]
    dns: Optional[List[IPv4Address]]
    peers: List[WGPeer] = []

    @validator('listen_port')
    def validate_listen_port(cls, listen_port):
        return WGPeer.validate_port(listen_port)

    class Config:
        validate_assignment = True
