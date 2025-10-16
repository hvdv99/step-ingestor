from dotenv import load_dotenv

load_dotenv('.env')

import os
import json
import random
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from step_ingestor.db import Base, AppUser
from step_ingestor.interfaces import AccessLink, StepIngestorRepository
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO
from step_ingestor.adapters import Adapter


# --- Helpers ---
def _data_path() -> Path:
    """Set path for mockdata"""
    here = Path(__file__).resolve()
    repo_root = here.parent.parent
    return repo_root / "tests" / "mockserver" / "mockdata" / "Activities-1758134751844.json"


@pytest.fixture(scope="session")
def test_users():
    """Test users ids to seed the database"""
    return ["123", "456", "789"]


# --- Polar API ---
@pytest.fixture(scope="session")
def mockserver(request):
    image = DockerImage(path="./tests/mockserver", tag="mockserver/mockserver:latest").build()
    container = DockerContainer(image=str(image)).with_bind_ports(container=6000, host=6000)
    mockserver_ = container.waiting_for(
        strategy=LogMessageWaitStrategy("Application startup complete.")
    )
    mockserver_.start()

    def stop_mockserver():
        container.stop(force=True)
    request.addfinalizer(stop_mockserver)
    return mockserver_.get_exposed_port(6000)


@pytest.fixture(scope="session")
def polar_interface(mockserver):
    host = os.environ["MOCKSERVER_HOST"]
    port = mockserver
    api_url = f"http://{host}:{port}"
    print(api_url)
    return AccessLink(
        api_url=api_url,
        auth_url=None,
        token_url=None,
        client_id=os.environ["POLAR_CLIENT_ID"],
        client_secret=os.environ["POLAR_CLIENT_SECRET"],
        redirect_url=os.environ["POLAR_CALLBACK_URL"]
    )


@pytest.fixture(scope="session")
def access_token():
    token_db = os.environ["TEST_ACCESS_TOKENS"].split(",")
    return random.choice(token_db)


# --- Adapter fixtures ---
@pytest.fixture(scope="session")
def adapter(polar_interface):
    return Adapter(
        adaptee=polar_interface,
        dto_dact=ActivitySummaryDTO,
        dto_step=StepSampleDTO
    )


@pytest.fixture(scope="module")
def raw_payloads():
    with _data_path().open("r") as f:
        return json.load(f)


@pytest.fixture(scope="function")
def random_raw_payload(raw_payloads):
    return random.choice(raw_payloads)


@pytest.fixture(scope="module")
def all_dtos(adapter, raw_payloads, test_users):
    uid = random.choice(test_users)
    return adapter._raw_payload_to_dto(raw_payloads, user_id=uid)


@pytest.fixture(scope="function")
def random_dto(all_dtos, k=1):
    """Returns random daily activity in DTO format from mock data"""
    selected = random.sample(all_dtos, k=k)
    if k == 1:
        return selected[0]
    return selected


# --- DB fixtures ---
@pytest.fixture(scope="session")
def testdb_config():
    return dict(
        host=os.environ["T_DB_HOSTNAME"],
        port=int(os.environ["T_DB_PORT"]),
        username=os.environ["T_POSTGRES_USER"],
        password=os.environ["T_POSTGRES_PASSWORD"],
        dbname=os.environ["T_POSTGRES_DB"],
        driver=os.environ["T_DB_DRIVER"]
    )


# Ref.: https://mariogarcia.github.io/blog/2019/10/pytest_fixtures.html
# Ref.: https://github.com/testcontainers/testcontainers-python/blob/5c1504c217d8cd3debd99dee54db826e49bfa579/core/testcontainers/core/wait_strategies.py
@pytest.fixture(scope="session")
def engine(testdb_config, request):
    pg = PostgresContainer(
        image="timescale/timescaledb:latest-pg16",
        username=testdb_config["username"],
        password=testdb_config["password"],
        dbname=testdb_config["dbname"]).waiting_for(
        LogMessageWaitStrategy("database system is ready to accept connections")
    )

    pg.start()
    url = pg.get_connection_url()
    engine = sa.create_engine(url)
    Base.metadata.create_all(engine)

    def stop_db():
        pg.stop()
    request.addfinalizer(stop_db)

    return engine


@pytest.fixture(autouse=True, scope="session")
def seed_test_users(session_factory, test_users):

    test_users_rows = [
        {"user_id": uid, "created_at": datetime.now(), "updated_at": datetime.now()} for uid in test_users
    ]

    stmt = sa.insert(AppUser).values(
        test_users_rows
    )

    with session_factory() as db:
        db.execute(stmt)
        db.commit()


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def repo(session_factory):
    return StepIngestorRepository(session_factory=session_factory,
                                  autocommit=False)
