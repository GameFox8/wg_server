import re
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Optional
from wg_api.models.wg_interface import WGInterface, WGPeer


OPTION_CONF_KEY = '__option_key__'


def option(opt_key):
    def wrapper(func):
        setattr(func, OPTION_CONF_KEY, opt_key)
        return func

    return wrapper


def extract_options(namespace):
    opt_setters = {}
    for member in namespace.values():
        if opt_key := getattr(member, OPTION_CONF_KEY, None):
            opt_setters[opt_key] = member

    return opt_setters


class ConfigParser:

    _interface_data: Dict = None
    _peers_data: List[Dict] = None

    _interface_config: str = None

    _options: Dict = None
    _new_section: bool = None

    _SECTION_R = re.compile(r'^\[(?P<section>.+)\]$')
    _OPTION_R = re.compile(r'^(?P<option>.*?)\s*=\s*(?P<value>.*)$')

    PEER_SECT = 'Peer'
    INTERFACE_SECT = 'Interface'

    def __init__(self):
        self._options = self.get_options()

    @classmethod
    def get_options(cls):
        return extract_options(cls.__dict__)

    def _init_option(self, sect_name, opt_key, opt_val):
        option_func = self._options.get(f'{sect_name}:{opt_key}')
        if option_func is None:
            return

        option_func(self, opt_val)

    def _reset_local_data(self):
        self._peers_data = []
        self._new_section = False
        self._interface_data = {}
        self._interface_config = ''

    @staticmethod
    def _str_val(opt_val: str):
        return None if opt_val in ('off', '0') else opt_val or None

    @staticmethod
    def _bool_val(opt_val: str):
        if opt_val.lower() in ('yes', 'on', 'true', '1'):
            return True

        if opt_val.lower() in ('no', 'off', 'false', '0'):
            return False

        return None

    @staticmethod
    def _int_val(opt_val: str):
        return None if opt_val in ('off', '0') else (opt_val or None) and int(opt_val)

    @staticmethod
    def _array_val(opt_val: str):
        return opt_val.split(', ') if opt_val else None

    @option('Interface:PrivateKey')
    def _read_option_1(self, value):
        self._add_interface_data['private_key'] = self._str_val(value)

    @option('Interface:PublicKey')
    def _read_option_2(self, value):
        self._add_interface_data['public_key'] = self._str_val(value)

    @option('Interface:ListenPort')
    def _read_option_3(self, value):
        self._add_interface_data['listen_port'] = self._int_val(value)

    @option('Interface:FwMark')
    def _read_option_4(self, value):
        self._add_interface_data['fw_mark'] = self._str_val(value)

    @option('Interface:Address')
    def _read_option_5(self, value):
        if address_array := self._array_val(value):
            self._add_interface_data.setdefault('address', []).extend(address_array)

    @option('Interface:DNS')
    def _read_option_6(self, value):
        if dns_array := self._array_val(value):
            self._add_interface_data.setdefault('dns', []).extend(dns_array)

    @option('Interface:MTU')
    def _read_option_7(self, value):
        self._add_interface_data['mtu'] = self._int_val(value)

    @option('Interface:Table')
    def _read_option_8(self, value):
        self._add_interface_data['table'] = self._str_val(value)

    @option('Interface:PreUp')
    def _read_option_9(self, value):
        self._add_interface_data.setdefault('pre_up', []).append(self._str_val(value))

    @option('Interface:PostUp')
    def _read_option_10(self, value):
        self._add_interface_data.setdefault('post_up', []).append(self._str_val(value))

    @option('Interface:PreDown')
    def _read_option_11(self, value):
        self._add_interface_data.setdefault('pre_down', []).append(self._str_val(value))

    @option('Interface:PostDown')
    def _read_option_12(self, value):
        self._add_interface_data.setdefault('post_down', []).append(self._str_val(value))

    @option('Interface:SaveConfig')
    def _read_option_13(self, value):
        self._add_interface_data['save_conf'] = self._bool_val(value)

    @option('Peer:PublicKey')
    def _read_option_14(self, value):
        self._add_peer_data['public_key'] = self._str_val(value)

    @option('Peer:PresharedKey')
    def _read_option_15(self, value):
        self._add_peer_data['preshared_key'] = self._str_val(value)

    @option('Peer:Endpoint')
    def _read_option_16(self, value):
        self._add_peer_data['end_point'] = self._str_val(value)

    @option('Peer:AllowedIPs')
    def _read_option_17(self, value):
        if allowed_ips := self._array_val(value):
            self._add_peer_data.setdefault('allowed_ips', []).extend(allowed_ips)

    @option('Peer:PersistentKeepalive')
    def _read_option_18(self, value):
        self._add_peer_data['keepalive'] = self._int_val(value)

    @option('Interface:private_key')
    def _write_option_1(self, value):
        if not value:
            return

        self._add_interface_config(True, 'PrivateKey', value)

    @option('Interface:public_key')
    def _write_option_2(self, value):
        if not value:
            return

        self._add_interface_config(True, 'PublicKey', value)

    @option('Interface:listen_port')
    def _write_option_3(self, value):
        if not value:
            return

        self._add_interface_config(True, 'ListenPort', value)

    @option('Interface:fw_mark')
    def _write_option_4(self, value):
        if not value:
            return

        self._add_interface_config(True, 'FwMark', value)

    @option('Interface:address')
    def _write_option_5(self, value):
        if not value:
            return

        for address in value:
            if not address:
                continue

            self._add_interface_config(True, 'Address', address)

    @option('Interface:dns')
    def _write_option_6(self, value):
        if not value:
            return

        for dns in value:
            if not dns:
                continue

            self._add_interface_config(True, 'DNS', dns)

    @option('Interface:mtu')
    def _write_option_7(self, value):
        if not value:
            return

        self._add_interface_config(True, 'MTU', value)

    @option('Interface:table')
    def _write_option_8(self, value):
        if not value:
            return

        self._add_interface_config(True, 'Table', value)

    @option('Interface:pre_up')
    def _write_option_9(self, value):
        if not value:
            return

        for command in value:
            if not command:
                continue

            self._add_interface_config(True, 'PreUp', command)

    @option('Interface:post_up')
    def _write_option_10(self, value):
        if not value:
            return

        for command in value:
            if not command:
                continue

            self._add_interface_config(True, 'PostUp', command)

    @option('Interface:pre_down')
    def _write_option_11(self, value):
        if not value:
            return

        for command in value:
            if not command:
                continue

            self._add_interface_config(True, 'PreDown', command)

    @option('Interface:post_down')
    def _write_option_12(self, value):
        if not value:
            return

        for command in value:
            if not command:
                continue

            self._add_interface_config(True, 'PostDown', command)

    @option('Interface:save_conf')
    def _write_option_13(self, value):
        if not value:
            return

        self._add_interface_config(True, 'SaveConfig', 'true')

    @option('Peer:public_key')
    def _write_option_14(self, value):
        if not value:
            return

        self._add_interface_config(False, 'PublicKey', value)

    @option('Peer:preshared_key')
    def _write_option_15(self, value):
        if not value:
            return

        self._add_interface_config(False, 'PresharedKey', value)

    @option('Peer:end_point')
    def _write_option_16(self, value):
        if not value:
            return

        self._add_interface_config(False, 'Endpoint', value)

    @option('Peer:allowed_ips')
    def _write_option_17(self, value):
        if not value:
            return

        for allowed_ip in value:
            if not allowed_ip:
                continue

            self._add_interface_config(False, 'AllowedIPs', allowed_ip)

    @option('Peer:keepalive')
    def _write_option_18(self, value):
        if not value:
            return

        self._add_interface_config(False, 'PersistentKeepalive', value)

    @property
    def _add_peer_data(self) -> dict:
        if not self._peers_data and self._new_section:
            self._peers_data.append({})

        self._new_section = False
        return self._peers_data[-1]

    @property
    def _add_interface_data(self) -> dict:
        self._new_section = False
        return self._interface_data

    def _add_interface_config(self, is_interface, opt_key, opt_val):
        if self._new_section:
            section = self.INTERFACE_SECT if is_interface else self.PEER_SECT
            if self._interface_config:
                self._interface_config += '\n\n'

            self._interface_config += f'[{section}]'

        self._new_section = False
        self._interface_config += f'\n{opt_key} = {opt_val}'

    async def load(self, path: Path) -> Optional[WGInterface]:
        curr_section = None
        self._reset_local_data()
        async with aiofiles.open(path, 'r') as file:
            async for line in file:
                line = str(line).strip()
                if not line or line.startswith('#'):
                    continue

                section = self._SECTION_R.match(line)
                section_name = section and section.group('section')
                if section_name:
                    self._new_section = True
                    curr_section = section_name
                elif not curr_section:
                    continue
                else:
                    option_groups = self._OPTION_R.match(line)
                    if not option_groups:
                        continue

                    opt_name, opt_val = option_groups.group('option', 'value')
                    if not (opt_name and opt_val):
                        continue

                    self._init_option(curr_section, opt_name, opt_val)

        if not self._interface_data:
            return None

        interface = WGInterface.parse_obj(self._interface_data)
        for peer_data in self._peers_data:
            if not peer_data:
                continue

            interface.peers.append(WGPeer.parse_obj(peer_data))

        return interface

    def dumps(self, interface: WGInterface) -> Optional[str]:
        self._reset_local_data()
        if not interface:
            return None

        peers_data = None
        self._new_section = True
        for opt_key, opt_val in interface.dict().items():
            if opt_key == 'peers':
                peers_data = opt_val
            else:
                self._init_option(self.INTERFACE_SECT, opt_key, opt_val)

        if not peers_data:
            return self._interface_config

        for peer_data in peers_data:
            self._new_section = True
            for opt_key, opt_val in peer_data.items():
                self._init_option(self.PEER_SECT, opt_key, opt_val)

        return self._interface_config

    async def dump(self, path: Path, interface: WGInterface):
        config = self.dumps(interface)
        if not config:
            raise ValueError('Failed to save the interface')

        async with aiofiles.open(path, 'w+') as file:
            await file.write(config)


class WGConfigs:

    _parser = None
    _configs_dir = None

    def __init__(self, configs_dir: str):
        self._configs_dir = configs_dir
        self._parser = ConfigParser()

    async def get_configs_paths(self) -> List[Path]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: list(Path(self._configs_dir).glob('*.conf'))
        )

    async def get_all(self) -> Dict[Path, WGInterface]:
        interface_by_path = {}
        configs_paths = await self.get_configs_paths()
        for config_path in configs_paths:
            interface_by_path[config_path] = await self.get(config_path)

        return interface_by_path

    async def get(self, config_path: Path) -> WGInterface:
        return await self._parser.load(config_path)

    async def set(self, config_path: Path, interface: WGInterface):
        await self._parser.dump(config_path, interface)

    async def get_peer(self, config_path: Path, public_key: str) -> WGPeer:
        if not public_key:
            raise ValueError('Empty peer public key')

        interface = await self.get(config_path)
        for peer in interface.peers:
            if peer.public_key == public_key:
                return peer

        raise KeyError(f'Not found peer with public key "{public_key}"')

    async def set_peer(self, config_path: Path, peer: WGPeer):
        interface = await self.get(config_path)
        for idx, peer in enumerate(interface.peers):
            if peer.public_key == peer.public_key:
                interface.peers[idx] = peer
        else:
            interface.peers.append(peer)

        await self.set(config_path, interface)

    async def remove_peer(self, config_path: Path, public_key: str):
        interface = await self.get(config_path)
        for idx, peer in enumerate(interface.peers):
            if peer.public_key == public_key:
                interface.peers.pop(idx)
                break
        else:
            raise KeyError(f'Not found peer with public key "{public_key}"')

        await self.set(config_path, interface)
        return peer
