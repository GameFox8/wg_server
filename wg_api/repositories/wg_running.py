from io import StringIO
from datetime import datetime, timedelta
from typing import Any, List, Optional, \
    Callable, Dict
from wg_api.repositories.wg_firewall import WGFirewall
from wg_api.models.wg_peer import WGPeer, WGRunningPeer
from wg_api.models.wg_interface import WGInterface, WGRunningInterface
from wg_api.utils.exceptions import ShellError, BaseInterfaceException, \
    NotFoundInterface, BasePeerException, NotFoundPeerException
from wg_api.utils.wg_utils import shell_exec, escape, \
    escape_to_str, check_interface_name


class WGRunning:

    CONNECTION_DELTA = timedelta(minutes=2)

    @classmethod
    def _prepare(cls, value: str, cast: Callable = None) -> Any:
        value = value.strip()
        if value in ('(none)', ''):
            return None

        return value if cast is None else cast(value)

    @classmethod
    def _int_zero_none(cls, value: str) -> Optional[int]:
        value = int(value)
        return value if value else None

    @classmethod
    def _off(cls, value: str) -> Optional[str]:
        return None if value == 'off' else value

    @classmethod
    def _int_off(cls, value: str) -> Optional[int]:
        return cls._off(value) and int(value)

    @classmethod
    def _array(cls, value: str) -> Optional[List[str]]:
        return value.split(',')

    @classmethod
    def _is_connected(cls, latest_handshakes: int) -> bool:
        if latest_handshakes is None:
            return False

        return datetime.now() - datetime.fromtimestamp(latest_handshakes) < cls.CONNECTION_DELTA

    @classmethod
    def _parse_interface(cls, *parts) -> WGRunningInterface:
        return WGRunningInterface(
            private_key=cls._prepare(parts[1]),
            public_key=cls._prepare(parts[2]),
            listen_port=cls._prepare(parts[3], int),
            fw_mark=cls._prepare(parts[4], cls._off)
        )

    @classmethod
    def _parse_peer(cls, *parts) -> WGRunningPeer:
        latest_handshake = cls._prepare(parts[5], cls._int_zero_none)
        return WGRunningPeer(
            public_key=cls._prepare(parts[1]),
            preshared_key=cls._prepare(parts[2]),
            end_point=cls._prepare(parts[3]),
            allowed_ips=cls._prepare(parts[4], cls._array),
            latest_handshake=latest_handshake,
            transfer_rx=cls._prepare(parts[6], int),
            transfer_tx=cls._prepare(parts[7], int),
            keepalive=cls._prepare(parts[8], cls._int_off),
            connected=cls._is_connected(latest_handshake)
        )

    @classmethod
    def _parse_connected(cls, name, public_key, latest_handshakes):
        latest_handshake = cls._prepare(latest_handshakes, cls._int_zero_none)
        return name, public_key, cls._is_connected(latest_handshake)

    @classmethod
    async def get_status(cls, name: str) -> dict:
        check_interface_name(name)
        data = await shell_exec(f"wg show interfaces | grep -wq '{escape(name)}' "
                                f"&& wg show '{escape(name)}' latest-handshakes")
        if not data:
            raise NotFoundInterface(name)

        connected_data = {}
        with StringIO(data) as str_io:
            for line in str_io:
                parts = line.strip().split('\t')
                _, pk, conn = cls._parse_connected(name, *parts)
                connected_data[pk] = conn

        return connected_data

    @classmethod
    async def get_status_all(cls) -> dict:
        connected_data = {}
        data = await shell_exec(f"wg show all latest-handshakes")
        if not data:
            return connected_data

        with StringIO(data) as str_io:
            for line in str_io:
                parts = line.strip().split('\t')
                name, pk, conn = cls._parse_connected(*parts)
                connected_data.setdefault(name, {})[pk] = conn

        return connected_data

    @staticmethod
    async def _fill_disabled_peers(*interfaces: WGRunningInterface):
        disabled_peers = await WGFirewall.get_disabled_peers(*interfaces)
        for peer in disabled_peers:
            peer.disabled = True

    @staticmethod
    async def _fill_interface_addresses(interface_by_name: Dict[str, WGInterface]):
        if not interface_by_name:
            return

        addresses_by_name = await WGFirewall.get_interfaces_addresses(*interface_by_name)
        for name, addresses in addresses_by_name.items():
            interface = interface_by_name.get(name)
            interface.address = addresses

    @classmethod
    async def get_all(cls) -> Dict[str, WGRunningInterface]:
        all_interfaces = {}
        all_data = await shell_exec(f"wg show all dump")
        if not all_data:
            return all_interfaces

        curr_name = None
        interface = None
        with StringIO(all_data) as str_io:
            for line in str_io:
                parts = line.strip().split('\t')
                interface_name = parts[0]
                if interface is None or interface_name != curr_name:
                    curr_name = interface_name
                    all_interfaces[curr_name] = interface = cls._parse_interface(*parts)
                else:
                    interface.peers.append(cls._parse_peer(*parts))

        await cls._fill_disabled_peers(*all_interfaces.values())
        await cls._fill_interface_addresses(all_interfaces)
        return all_interfaces

    @classmethod
    async def get_by_name(cls, name: str) -> WGRunningInterface:
        check_interface_name(name)
        data = await shell_exec(f"wg show interfaces | grep -wq '{escape(name)}' "
                                f"&& wg show '{escape(name)}' dump")
        if not data:
            raise NotFoundInterface(name)

        interface = None
        with StringIO(data) as str_io:
            for line in str_io:
                parts = line.strip().split('\t')
                if interface is None:
                    interface = cls._parse_interface(None, *parts)
                else:
                    interface.peers.append(cls._parse_peer(None, *parts))

        await cls._fill_disabled_peers(interface)
        await cls._fill_interface_addresses({name: interface})
        return interface

    @classmethod
    async def get_peers_pks(cls, name: str) -> List[str]:
        check_interface_name(name)
        peers_pks = await shell_exec(f"wg show interfaces | grep -wq '{escape(name)}' "
                                     f"&& wg show '{escape(name)}' peers")
        return peers_pks.strip().split('\n')

    @classmethod
    async def set_interface(cls, name, interface: WGInterface):
        peers_pks = await cls.get_peers_pks(name)

        input_args = []
        command = f"wg set '{escape(name)}'"
        command += f" listen-port {interface.listen_port or 0}"
        command += f" fwmark '{escape_to_str(interface.fw_mark or 0)}'"
        if interface.private_key:
            command += f" private-key <(read -r; echo \"$REPLY\")"
            input_args.append(interface.private_key)
        else:
            command += f" private-key /dev/null"

        for peer in interface.peers:
            command += f" peer '{escape(peer.public_key)}'"
            if peer.preshared_key:
                command += f" preshared-key <(read -r; echo \"$REPLY\")"
                input_args.append(peer.preshared_key)
            else:
                command += f" preshared-key /dev/null"

            if peer.end_point:
                command += f" endpoint '{escape_to_str(peer.end_point)}'"

            command += f" persistent-keepalive {peer.keepalive or 0}"
            if peer.allowed_ips:
                command += f" allowed-ips '{','.join(map(str, peer.allowed_ips))}'"
            else:
                command += f" allowed-ips ''"

            if peer.public_key in peers_pks:
                peers_pks.remove(peer.public_key)

        for peer_pk in peers_pks:
            command += f" peer '{escape(peer_pk)}' remove"

        try:
            await shell_exec(command, *input_args)
        except ShellError as ex:
            raise BaseInterfaceException(name, 'interface is not set') from ex

    @classmethod
    async def get_peer(cls, name: str, public_key: str) -> WGRunningPeer:
        if not public_key:
            raise ValueError('Empty peer public key')

        interface = await cls.get_by_name(name)
        for peer in interface.peers:
            if peer.public_key == public_key:
                return peer

        raise NotFoundPeerException(name, public_key)

    @classmethod
    async def set_peer(cls, name: str, saved_peer: WGPeer):
        interface: WGInterface = await cls.get_by_name(name)
        for idx, peer in enumerate(interface.peers):
            if peer.public_key == saved_peer.public_key:
                interface.peers[idx] = saved_peer
        else:
            interface.peers.append(saved_peer)

        await cls.set_interface(name, interface)

    @classmethod
    async def remove_peer(cls, name: str, public_key: str) -> WGRunningPeer:
        peer = await cls.get_peer(name, public_key)
        try:
            await shell_exec(f"wg set '{escape(name)}' peer '{peer.public_key}' remove")
        except ShellError as ex:
            raise BasePeerException(name, public_key, 'peer is not removed') from ex

        return peer

    @classmethod
    async def disable_peer(cls, name: str, public_key: str):
        peer = await cls.get_peer(name, public_key)
        try:
            await WGFirewall.disable_peer(peer)
        except ShellError as ex:
            raise BasePeerException(name, public_key, 'peer is not disabled') from ex

    @classmethod
    async def enable_peer(cls, name: str, public_key: str):
        peer = await cls.get_peer(name, public_key)
        try:
            await WGFirewall.enable_peer(peer)
        except ShellError as ex:
            raise BasePeerException(name, public_key, 'peer is not enabled') from ex

    @classmethod
    async def start(cls, name: str):
        check_interface_name(name)
        try:
            await shell_exec(f"wg show interfaces | grep -wq '{escape(name)}' "
                             f"|| wg-quick up '{escape(name)}'")
        except ShellError as ex:
            raise BaseInterfaceException(name, 'interface is not started') from ex

    @classmethod
    async def stop(cls, name: str):
        check_interface_name(name)
        try:
            await shell_exec(f"wg show interfaces | grep -wq '{escape(name)}' "
                             f"&& wg-quick down '{escape(name)}'")
        except ShellError as ex:
            raise BaseInterfaceException(name, f'interface is not stopped') from ex

    @classmethod
    async def save_config(cls, name: str):
        check_interface_name(name)
        try:
            await shell_exec(f"wg-quick save '{escape(name)}'")
        except ShellError as ex:
            raise BaseInterfaceException(name, 'interface is not saved') from ex

    @classmethod
    async def sync_with_config(cls, name: str):
        check_interface_name(name)
        try:
            await shell_exec(f"wg syncconf '{escape(name)}' <(wg-quick strip '{escape(name)}')")
        except ShellError as ex:
            raise BaseInterfaceException(name, 'interface is not synchronized') from ex
