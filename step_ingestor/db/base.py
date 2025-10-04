import os

from sqlalchemy import URL, make_url, create_engine
from sqlalchemy.orm import sessionmaker

db_uname = os.environ["POSTGRES_USER"]
db_pw = os.environ["POSTGRES_PASSWORD"]
db_name = os.environ["POSTGRES_DB"]
port = os.environ["DB_PORT"]
host = os.environ["DB_HOSTNAME"]

db_driver = "postgresql+psycopg2"

sqlalchemy_url = URL.create(
    db_driver,
    username=db_uname,
    password=db_pw,
    host=host,
    port=int(port),
    database=db_name
)

stringified_sqlalchemy_url = sqlalchemy_url.render_as_string(
    hide_password=False
)

assert make_url(stringified_sqlalchemy_url) == sqlalchemy_url

percent_replaced_url = stringified_sqlalchemy_url.replace("%", "%%")

# assert percent-interpolated plus make_url round trip
assert make_url(percent_replaced_url % {}) == sqlalchemy_url

engine = create_engine(stringified_sqlalchemy_url,
                       pool_pre_ping=True,
                       future=True)

SessionFactory = sessionmaker(engine,
                              expire_on_commit=False,
                              autocommit=False)
