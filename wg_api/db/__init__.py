from .client_app import client_app
from .engine import metadata, engine

metadata.create_all(bind=engine)
