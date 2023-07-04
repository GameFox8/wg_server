import json
from typing import List, Dict, Optional
from ipaddress import IPv4Interface, IPv4Address
from wg_api.models import WGInterface, WGPeer
from wg_api.utils.wg_utils import shell_exec


class WGFirewall:

    TABLE = 'wg-table'
    DISABLED_SET = 'disabled-peers'
    INTERFACES_SET = 'running-interfaces'

    @classmethod
    def _get_set_elements(cls, nft_data: dict, set_name: str):
        if not nft_data:
            return []

        nft_data = nft_data.get('nftables')
        if not nft_data:
            return []

        for nft_obj in nft_data:
            set_data = nft_obj.get('set')
            if set_data is None:
                continue

            if (set_data.get('table') != cls.TABLE
                    or set_data.get('name') != set_name):
                continue

            return set_data.get('elem') or []

    @classmethod
    async def _get_disabled_ips(cls) -> List[IPv4Address]:
        nft_data = json.loads(await shell_exec(f'nft --json list set inet '
                                               f'{cls.TABLE} {cls.DISABLED_SET}'))
        disabled_ips = cls._get_set_elements(nft_data, cls.DISABLED_SET)
        if not disabled_ips:
            return []

        return list(map(IPv4Address, disabled_ips))

    @classmethod
    async def get_disabled_peers(cls, *interfaces: WGInterface) -> List[WGPeer]:
        disabled_peers = []
        if not interfaces:
            return disabled_peers

        disabled_ips = await cls._get_disabled_ips()
        if not disabled_ips:
            return disabled_peers

        for interface in interfaces:
            for peer in interface.peers:
                for peer_addr in peer.allowed_ips:
                    if peer_addr.ip in disabled_ips:
                        disabled_peers.append(peer)

        return disabled_peers

    @staticmethod
    def _get_peer_ips_str(peer: WGPeer) -> Optional[str]:
        if not peer.allowed_ips:
            return None

        return ', '.join(str(peer_ip.ip) for peer_ip in peer.allowed_ips)

    @classmethod
    async def disable_peer(cls, peer: WGPeer):
        peer_ips_str = cls._get_peer_ips_str(peer)
        if not peer_ips_str:
            return

        await shell_exec(f'nft add element inet '
                         f'{cls.TABLE} {cls.DISABLED_SET} {{ {peer_ips_str} }}')

    @classmethod
    async def enable_peer(cls, peer: WGPeer):
        peer_ips_str = cls._get_peer_ips_str(peer)
        if not peer_ips_str:
            return

        await shell_exec(f'nft delete element inet '
                         f'{cls.TABLE} {cls.DISABLED_SET} {{ {peer_ips_str} }}')

    @classmethod
    async def get_interfaces_addresses(cls, *interface_names: str) -> Dict[str, List[IPv4Interface]]:
        addresses_by_interface = {}
        if not interface_names:
            return addresses_by_interface

        ip_data = json.loads(await shell_exec('ip -j -br a show'))
        if not ip_data:
            return addresses_by_interface

        for if_data in ip_data:
            if_name = if_data.get('ifname')
            if if_name not in interface_names:
                continue

            addr_list = if_data.get('addr_info') or []
            for addr in addr_list:
                if_addr = IPv4Interface(f'{addr.get("local")}/{addr.get("prefixlen")}')
                addresses_by_interface.setdefault(if_name, []).append(if_addr)

        return addresses_by_interface
