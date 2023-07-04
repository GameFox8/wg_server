from typing import Dict
from fastapi import APIRouter, Depends, status
from wg_api.utils import handle_http_exception
from wg_api.repositories import WGConfigs, WGClients
from wg_api.models import WGConfigInterface, WGPeer


def configs_repo():
    return WGConfigs('/etc/wireguard/')


configs_router = APIRouter(prefix='/configs', tags=['configs'])


@configs_router.get('/all')
@handle_http_exception()
async def get_all_interfaces(wg_configs: WGConfigs = Depends(configs_repo)) -> Dict[str, WGConfigInterface]:
    return await wg_configs.get_all()


@configs_router.get('/')
@handle_http_exception()
async def get_interface(name: str, wg_configs: WGConfigs = Depends(configs_repo)) -> WGConfigInterface:
    return await wg_configs.get_by_name(name)


@configs_router.put('/', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def set_interface(name: str, interface: WGConfigInterface, wg_configs: WGConfigs = Depends(configs_repo)):
    await wg_configs.set_interface(name, interface)


@configs_router.get('/peers')
@handle_http_exception()
async def get_peer(name: str, public_key: str, wg_configs: WGConfigs = Depends(configs_repo)) -> WGPeer:
    return await wg_configs.get_peer(name, public_key)


@configs_router.put('/peers', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def set_peer(name: str, peer: WGPeer, wg_configs: WGConfigs = Depends(configs_repo)):
    await wg_configs.set_peer(name, peer)


@configs_router.delete('/peers', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def remove_peer(name: str, public_key: str, wg_configs: WGConfigs = Depends(configs_repo)):
    await wg_configs.remove_peer(name, public_key)


@configs_router.post('/peers/disable', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def disable_peer(name: str, public_key: str, wg_configs: WGConfigs = Depends(configs_repo)):
    await wg_configs.disable_peer(name, public_key)


@configs_router.post('/peers/enable', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def enable_peer(name: str, public_key: str, wg_configs: WGConfigs = Depends(configs_repo)):
    await wg_configs.enable_peer(name, public_key)


@configs_router.put('/peers/clients')
@handle_http_exception()
async def create_client(name: str, wg_configs: WGConfigs = Depends(configs_repo)) -> Dict[str, str]:
    interface = await wg_configs.get_by_name(name)
    client_peer, client_interface = await WGClients.create_client(interface)
    await wg_configs.set_peer(name, client_peer)
    return {
        'public_key': client_peer.public_key,
        'client_config': WGConfigs.make_config(client_interface),
    }
