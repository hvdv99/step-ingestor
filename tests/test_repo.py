import pytest
import sqlalchemy as sa
from step_ingestor.interfaces import StepIngestorRepository


@pytest.mark.parametrize("user_index", [0, 1, 2])
def test_repo_can_insert_user(user_index, test_users, test_session):
    repo = StepIngestorRepository(session=test_session, autocommit=False)
    user = test_users[user_index]
    repo.add_user(user=user)

    stmt = sa.text("""SELECT DISTINCT COUNT(*) FROM app_user""")
    n_users = test_session.execute(stmt).scalar()
    assert n_users == 1
    test_session.rollback()


@pytest.mark.parametrize("user_index", [0, 1, 2])
def test_repo_can_retrieve_a_user_by_id(user_index, seeded_user, test_session):
    repo = StepIngestorRepository(session=test_session, autocommit=False)  # only flush
    data = repo.get_user_by_id(user_id=seeded_user.user_id)
    assert data == seeded_user


@pytest.mark.parametrize("user_index", [0, 1, 2])
def test_repo_can_ingest_daily_activities(user_index, seeded_user, user_activity_dto, test_session):
    repo = StepIngestorRepository(session=test_session, autocommit=False)  # only flush
    result = repo.ingest_payload(payload=user_activity_dto)
    assert result


@pytest.mark.parametrize("user_index", [0, 1, 2])
def test_repo_can_retrieve_user_data(user_index, seeded_user, seed_user_data, test_users, test_session):
    repo = StepIngestorRepository(session=test_session, autocommit=False)  # only flush
    user = test_users[user_index]
    data = repo.get_user_data(user=user)
    assert data
