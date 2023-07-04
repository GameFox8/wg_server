from sqlalchemy import MetaData, create_engine
from databases import Database

DB_PATH = 'sqlite:///db/wg_server.db'

database = Database(DB_PATH)
engine = create_engine(DB_PATH, echo=True)
metadata = MetaData()
