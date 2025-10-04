import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.orm import Session

load_dotenv('.env')

from step_ingestor.interfaces import PolarApiFetcher
from step_ingestor.repositories import StepIngestorRepository
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO
from step_ingestor.services import IngestionService
from step_ingestor.adapters import Adapter

# --- Helpers ---
def _data_path() -> Path:
    # Resolve from repo root no matter where pytest is invoked
    # tests/ is a sibling of data/, so go up one and into data/
    here = Path(__file__).resolve()
    repo_root = here.parent.parent
    return repo_root / "data" / "Activities-1758134751844.json"

# --- API fixture ---
@pytest.fixture
def interface():
    return PolarApiFetcher(
        os.environ["POLAR_CLIENT_ID"],
        os.environ["POLAR_CLIENT_SECRET"]
    )

@pytest.fixture
def access_token():
    return os.environ["POLAR_ACCESS_TOKEN"]

# --- Adapter fixture ---
@pytest.fixture
def adapter():
    return Adapter()

# --- Date string fixtures
@pytest.fixture
def random_day_str(start=datetime(2025, 1, 1), end=datetime.now()) -> str:
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_date = start + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

@pytest.fixture
def date_str_tomorrow():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    return datetime.strftime(tomorrow, "%Y-%m-%d")

@pytest.fixture
def date_str_old():
    """Date string older than 365 days"""
    now = datetime.now()
    year_ago_1 = now - timedelta(days=366)
    return datetime.strftime(year_ago_1, "%Y-%m-%d")


# --- DB fixtures ---
DB_TEST_USER_ID='test-user123'

@pytest.fixture(scope="module")
def engine():
    db_uname = os.environ["POSTGRES_USER"]
    db_pw = os.environ["POSTGRES_PASSWORD"]
    db_name = os.environ["POSTGRES_DB"]
    port = os.environ["DB_PORT"]
    host = os.environ["DB_HOSTNAME"]

    db_driver = "postgresql+psycopg2"

    url = sa.URL.create(
        db_driver,
        username=db_uname,
        password=db_pw,
        host=host,
        port=int(port),
        database=db_name
    )

    sqlalchemy_url = url.render_as_string(
        hide_password=False
    )

    return sa.create_engine(sqlalchemy_url, pool_pre_ping=True, future=True)

@pytest.fixture(scope="module")
def db_session(engine):
    conn = engine.connect()
    trans = conn.begin()                  # outer transaction
    session = Session(bind=conn, expire_on_commit=False)

    try:
        yield session
    finally:
        session.close()
        trans.rollback()                  # wipes all changes
        conn.close()

@pytest.fixture(scope="module")
def repo(db_session):
    # Factory that always returns THE SAME session object for this test
    session_factory = lambda: db_session
    return StepIngestorRepository(session_factory=session_factory,
                                  autocommit=False)

@pytest.fixture(autouse=True, scope="module")
def seed_test_user(db_session):
    (db_session
     .execute(sa.text("""INSERT INTO app_user (user_id, created_at, updated_at) 
                         VALUES (:uid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
                         ON CONFLICT (user_id) DO NOTHING;""")
              .bindparams(uid=DB_TEST_USER_ID))
     )
    db_session.flush()
    yield

# --- Data fixtures ---
@pytest.fixture
def all_day_payloads_dto():
    with _data_path().open("r") as f:
        data = json.load(f)

    return [
        ActivitySummaryDTO(
            **{
                **day,
                "polar_user_id": DB_TEST_USER_ID,
                "date": datetime.fromisoformat(day["start_time"]).date().isoformat(),
            }
        )
        for day in data
    ]


@pytest.fixture
def all_minute_samples_dto():
    with _data_path().open("r") as f:
        data = json.load(f)

    all_step_samples = []
    for d in data:
        samples = d.get("samples").get("steps").get("samples")
        all_step_samples.append(
            [StepSampleDTO(**{**s,
                              "polar_user_id": DB_TEST_USER_ID}) for s in samples]
        )
    return all_step_samples

@pytest.fixture
def all_payloads():
    with _data_path().open("r") as f:
        data = json.load(f)

    all_payloads_ = []
    for d in data:
        summary = ActivitySummaryDTO(
            **{
                **d,
                "polar_user_id": DB_TEST_USER_ID,
                "date": datetime.fromisoformat(d["start_time"]).date().isoformat(),
            }
        )

        samples = d.get("samples").get("steps").get("samples")

        all_payloads_.append(
            (summary,
            [StepSampleDTO(**{**s,
                              "polar_user_id": DB_TEST_USER_ID}) for s in samples])
        )
    return all_payloads_


@pytest.fixture
def day_payload_dto(all_day_payloads_dto):
    """Returns random DTO object from sample data"""
    return random.choice(all_day_payloads_dto)


@pytest.fixture
def minute_samples_dto(all_minute_samples_dto):
    return random.choice(all_minute_samples_dto)


@pytest.fixture
def three_days_payload_dto(all_day_payloads_dto):
    return random.sample(all_day_payloads_dto, 3)


@pytest.fixture
def three_days_step_samples(all_minute_samples_dto):
    return random.sample(all_minute_samples_dto, 3)
