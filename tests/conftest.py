import os
import json
import random
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import pytest
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from step_ingestor.db import Base, AppUser, ActivitySummary, StepSample
from step_ingestor.interfaces import AccessLink
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO, UserDTO
from step_ingestor.adapters import Adapter


load_dotenv('.env')


# --- Helpers ---
def _data_path() -> Path:
    """Set path for mockdata"""
    here = Path(__file__).resolve()
    repo_root = here.parent.parent
    return repo_root / "tests" / "mockserver" / "mockdata" / "mockdata.json"


@pytest.fixture(scope="session")
def test_users():
    """Test users to seed the database. Fixture with scope 'session'
    ensures the uuids are consistent within the session"""
    now = datetime.now(tz=ZoneInfo("Europe/Amsterdam"))
    return [UserDTO(user_id=uuid.uuid4().hex,
                    polar_user_id=uid,
                    created_at=now,
                    updated_at=now) for uid in ["123", "456", "789"]]


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
@pytest.fixture(scope="function")
def adapter(polar_interface):
    return Adapter(
        adaptee=polar_interface,
        dto_dact=ActivitySummaryDTO,
        dto_step=StepSampleDTO
    )


@pytest.fixture(scope="session")
def raw_payloads():
    with _data_path().open("r") as f:
        return json.load(f)


@pytest.fixture(scope="function")
def random_raw_payload(raw_payloads):
    return random.choice(raw_payloads)


@pytest.fixture(scope="function")
def user_activity_dto(user_index, test_users, raw_payloads):
    user_id = test_users[user_index].user_id
    adapter = Adapter(dto_dact=ActivitySummaryDTO, dto_step=StepSampleDTO, adaptee=None)
    return adapter._raw_payload_to_dto(raw_payloads, user_id=user_id)


@pytest.fixture(scope="function")
def random_dto(user_activity_dtos, k=1):
    """Returns random daily activity in DTO format from mock data"""
    selected = random.sample(user_activity_dtos, k=k)
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


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine,
                        expire_on_commit=True)


@pytest.fixture(scope="function")
def test_session(session_factory):
    return session_factory()


@pytest.fixture(scope="function")
def user_index(request):
    return request.param


@pytest.fixture(scope="function")
def seeded_user(user_index, test_session, test_users):
    """Insert a single user (chosen by index) just for this test."""
    user = test_users[user_index]

    stmt = sa.insert(AppUser).values(user.model_dump(exclude={"access_token"}))
    with test_session as db:
        db.execute(stmt)
        db.commit()

    yield user

    # Cleanup
    with test_session as db:
        db.execute(sa.delete(AppUser).where(AppUser.user_id == user.user_id))
        db.commit()

def iter_step_samples(summaries):
    for s in summaries:
        if s.step_samples:
            yield from s.step_samples

@pytest.fixture(scope="function")
def seed_user_data(user_activity_dto, test_session):
    rows_act = [s.model_dump(exclude={"step_samples"}, by_alias=True) for s in user_activity_dto]
    rows_steps = []
    for ss in iter_step_samples(user_activity_dto):
        rows_steps.append(ss.model_dump(include={"user_id", "timestamp", "steps"}))

    stmt_act = sa.insert(ActivitySummary).values(rows_act)
    stmt_steps = sa.insert(StepSample).values(rows_steps)

    with test_session as db:
        db.execute(stmt_act)
        db.execute(stmt_steps)
        db.commit()
    yield

    # Cleanup not required because of cascasde
