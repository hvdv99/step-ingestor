# --- Mapping to DTOs test
def test_mapping_empty_daily_summary(adapter):
    raw = {}
    result = adapter._raw_payload_to_dto(raw, user_id="123")
    assert not result

def test_mapping_single_empty_step_samples(adapter, random_raw_payload):
    del random_raw_payload["samples"]["steps"]["samples"]
    result = adapter._raw_payload_to_dto(random_raw_payload, user_id="123")
    assert not result.pop()[1]  # Check if step samples is empty

def test_mapping_mock_data(adapter, raw_payloads):
    results = adapter._raw_payload_to_dto(raw=raw_payloads, user_id="123")
    assert all(results)
