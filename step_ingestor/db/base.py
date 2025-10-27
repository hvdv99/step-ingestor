import os
from sqlalchemy import URL

db_uname = os.environ["POSTGRES_USER"]
db_pw = os.environ["POSTGRES_PASSWORD"]
db_name = os.environ["POSTGRES_DB"]
port = os.environ["DB_PORT"]
host = os.environ["DB_HOSTNAME"]
db_driver = os.environ["DB_DRIVER"]

db_url = URL.create(
    db_driver,
    username=db_uname,
    password=db_pw,
    host=host,
    port=int(port),
    database=db_name
)

