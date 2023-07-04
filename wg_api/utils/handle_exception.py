import time
from contextlib import asynccontextmanager
from fastapi import HTTPException, status
from wg_api.utils.exceptions import *


@asynccontextmanager
async def handle_http_exception():
    try:
        yield
    except (NotFoundInterface, NotFoundPeerException) as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))
    except (BaseInterfaceException, BasePeerException) as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex))
