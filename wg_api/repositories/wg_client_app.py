from databases import Database
from wg_api.db import client_app
from wg_api.models import WGClientAppDB


class WGClientApp:

    _db = None

    def __init__(self, db_core: Database):
        self._db = db_core

    async def get(self, app_key: str):
        qwery = client_app.select().where(client_app.c.app_key == app_key)
        print(app_key)
        return await self._db.fetch_one(qwery)

    async def crate(self, app: WGClientAppDB):
        qwery = client_app.insert().values(**app.dict())
        await self._db.execute(qwery)

import asyncio
from wg_api.db.engine import database

async def create_app():
    apps = WGClientApp(database)
    #await apps.crate(WGClientAppDB(id=12, app_key='123', app_name='123', hashed_password='123123234565235'))
    print(await apps.get('123'))

asyncio.run(create_app())