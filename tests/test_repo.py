# TODO: Scalability test
#  Mockeroo (sample data)
#  locust https://github.com/locustio/locust

import random

# Single day
# Tests for table ActivitySummary
def test_upsert_activity_summary(repo, day_payload_dto):
    result = repo._upsert_activity_summary(summary=day_payload_dto)
    assert result

# Test for table Steps
def test_upsert_steps_minute_batch(repo, minute_samples_dto):
    result = repo._upsert_step_samples_batch(samples=minute_samples_dto)
    assert result > 0

# Test for both
def test_upsert_both_tables(repo, all_payloads):
    payload = random.choice(all_payloads)
    result = repo.ingest_payload(payload)
    assert result

# Multiple days
# Test for table ActivitySummary
def test_upsert_activity_summary_three_days(repo, three_days_payload_dto):
    result = repo._upsert_activity_summary(summary=three_days_payload_dto)
    assert result > 0

# Test for table Steps
def test_upsert_steps_minute_batch_three_days(repo, three_days_step_samples):
    result = repo._upsert_step_samples_batch(samples=three_days_step_samples)
    assert result > 0

# Test for both
def test_upsert_both_tables_three_days(repo, all_payloads):
    payloads = random.sample(all_payloads, 3)
    result = repo.ingest_payload(payload=payloads)
    assert result

def test_upsert_both_tables_all(repo, all_payloads):
    result = repo.ingest_payload(payload=all_payloads)
    assert result