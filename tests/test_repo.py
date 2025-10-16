import sqlalchemy as sa
from step_ingestor.db.models import StepSample, ActivitySummary


# Single day
# Tests for table ActivitySummary
def test_upsert_activity_summary(repo, random_dto):
    """Adds one row to the daily activity table for one user"""
    d_activ, _ = random_dto
    result = repo._upsert_activity_summary(summary=d_activ)

    with repo._begin() as db:
        stmt = sa.select(sa.func.count()).select_from(ActivitySummary)
        n_rows = db.execute(stmt).scalar()

    assert result
    assert n_rows == 1


# Test for table Steps
def test_upsert_steps(repo, random_dto):
    """Adds step samples belonging to a single day to the database for a single user"""
    _, steps = random_dto
    upsert_result = repo._upsert_step_samples_batch(samples=steps)

    with repo._begin() as db:
        stmt = sa.select(sa.func.count(StepSample.user_id.distinct())).select_from(StepSample)
        n_users = db.execute(stmt).scalar()

    assert upsert_result > 0
    assert n_users == 1


# Test for both
def test_upsert_both_tables(repo, random_dto):
    result = repo.ingest_payload(payload=random_dto)
    assert result

# # Multiple days
# # Test for table ActivitySummary
# def test_upsert_activity_summary_three_days(repo, three_days_payload_dto):
#     result = repo._upsert_activity_summary(summary=three_days_payload_dto)
#     assert result > 0
#
# # Test for table Steps
# def test_upsert_steps_minute_batch_three_days(repo, three_days_step_samples):
#     result = repo._upsert_step_samples_batch(samples=three_days_step_samples)
#     assert result > 0
#
# # Test for both
# def test_upsert_both_tables_three_days(repo, all_payloads):
#     payloads = random.sample(all_payloads, 3)
#     result = repo.ingest_payload(payload=payloads)
#     assert result
#
# def test_upsert_both_tables_all(repo, all_payloads):
#     result = repo.ingest_payload(payload=all_payloads)
#     assert result