from typing import List, Dict
from fastapi import APIRouter, status
from wg_api.utils import handle_http_exception
from wg_api.repositories import WGConfigs, \
    WGRunning, WGClients
from wg_api.models import WGInterface, \
    WGRunningInterface, WGPeer, WGRunningPeer


running_router = APIRouter(prefix='/running', tags=['running'])


@running_router.get('/all')
@handle_http_exception()
async def get_interfaces() -> Dict[str, WGRunningInterface]:
    return await WGRunning.get_all()


@running_router.get('/all/status')
@handle_http_exception()
async def get_statuses() -> dict:
    return await WGRunning.get_status_all()


@running_router.post('/start', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def start_interface(name: str):
    await WGRunning.start(name)


@running_router.post('/stop', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def stop_interface(name: str):
    await WGRunning.stop(name)


@running_router.post('/save_config', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def save_config(name: str):
    await WGRunning.save_config(name)


@running_router.post('/sync_with_config', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def sync_with_config(name: str):
    await WGRunning.sync_with_config(name)


@running_router.get('/status')
@handle_http_exception()
async def get_status(name: str) -> dict:
    return await WGRunning.get_status(name)


@running_router.get('/')
@handle_http_exception()
async def get_interface(name: str) -> WGRunningInterface:
    return await WGRunning.get_by_name(name)


@running_router.put('/', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def set_interface(name: str, interface: WGInterface):
    await WGRunning.set_interface(name, interface)


@running_router.get('/peers/public_keys')
@handle_http_exception()
async def get_peers_public_keys(name: str) -> List[str]:
    return await WGRunning.get_peers_pks(name)


@running_router.get('/peers')
@handle_http_exception()
async def get_peer(name: str, public_key: str) -> WGRunningPeer:
    return await WGRunning.get_peer(name, public_key)


@running_router.put('/peers', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def set_peer(name: str, peer: WGPeer):
    await WGRunning.set_peer(name, peer)


@running_router.delete('/peers', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def remove_peer(name: str, public_key: str):
    await WGRunning.remove_peer(name, public_key)


@running_router.put('/peers/clients')
@handle_http_exception()
async def create_client(name: str) -> Dict[str, str]:
    interface = await WGRunning.get_by_name(name)
    client_peer, client_interface = await WGClients.create_client(interface)
    await WGRunning.set_peer(name, client_peer)
    return {
        'public_key': client_peer.public_key,
        'client_config': WGConfigs.make_config(client_interface),
    }


@running_router.post('/peers/disable', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def disable_peer(name: str, public_key: str):
    await WGRunning.disable_peer(name, public_key)


@running_router.post('/peers/enable', status_code=status.HTTP_204_NO_CONTENT)
@handle_http_exception()
async def enable_peer(name: str, public_key: str):
    await WGRunning.enable_peer(name, public_key)
