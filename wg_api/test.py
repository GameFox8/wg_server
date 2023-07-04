import asyncio
from wg_api.repositories.wg_client_app import WGClientApp
from wg_api.db.engine import database

async def create_app():
    apps = WGClientApp(database)
    print(await apps.get('asgw@yandex.ru'))

asyncio.run(create_app())
