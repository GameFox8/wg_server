from typing import Tuple
from ipaddress import IPv4Address, IPv4Interface
from wg_api.utils import config
from wg_api.models import WGPeer, WGInterface, WGConfigInterface
from wg_api.utils.wg_utils import get_private_key, get_public_key


class WGClients:

    DNS = ['1.1.1.1']
    MTU = '1420'
    KEEAPALIVE = '20'

    @staticmethod
    def _is_address_reserved(peer: WGPeer, addr: IPv4Address):
        if not peer.allowed_ips:
            return False

        for peer_ip in peer.allowed_ips:
            if addr in peer_ip.network:
                return True

        return False

    @classmethod
    def _get_client_address(cls, interface: WGInterface) -> IPv4Interface:
        for addr in interface.address:
            for host in addr.network:
                if host <= addr.ip:
                    continue

                for peer in interface.peers:
                    if cls._is_address_reserved(peer, host):
                        break
                else:
                    return IPv4Interface(host)

        raise RuntimeError('All addresses are reserved')

    @classmethod
    async def create_client(cls, interface: WGInterface) -> Tuple[WGPeer, WGConfigInterface]:
        client_address = cls._get_client_address(interface)
        client_interface = WGConfigInterface(
            private_key=await get_private_key(),
            address=[client_address],
            dns=cls.DNS,
            mtu=cls.MTU,
            peers=[WGPeer(
                public_key=await get_public_key(interface.private_key),
                end_point=f'{config.SERVER_IP}:{interface.listen_port}',
                allowed_ips=[IPv4Interface('0.0.0.0/0')],
                keepalive=cls.KEEAPALIVE,
            )]
        )
        client_peer = WGPeer(
            public_key=await get_public_key(client_interface.private_key),
            allowed_ips=[client_address],
        )
        return client_peer, client_interface
