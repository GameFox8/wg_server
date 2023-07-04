from typing import Optional
from datetime import datetime
from pydantic import BaseModel, constr


class WGClientApp(BaseModel):

    app_key: str
    app_name: str
    auth_dt: Optional[datetime]
    create_dt: Optional[datetime]


class WGClientAppDB(WGClientApp):

    id: int
    hashed_password: constr(min_length=8)
