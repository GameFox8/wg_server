import datetime
import sqlalchemy
from .engine import metadata

client_app = sqlalchemy.Table(
    'client_app', metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True),
    sqlalchemy.Column('app_key', sqlalchemy.String, nullable=False, unique=True),
    sqlalchemy.Column('app_name', sqlalchemy.String, nullable=False),
    sqlalchemy.Column('auth_dt', sqlalchemy.DateTime),
    sqlalchemy.Column('create_dt', sqlalchemy.DateTime, default=datetime.datetime.utcnow),
    sqlalchemy.Column('hashed_password', sqlalchemy.String, nullable=False),
)
