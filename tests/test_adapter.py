# --- Mapping to DTOs test
def test_mapping_empty_daily_summary(adapter):
    raw = {}
    result = adapter.map_daily_payload_to_dto(raw)
    assert result is None

def test_mapping_single_empty_step_samples(adapter, day_payload_dto):
    raw = day_payload_dto.raw_payload
    del raw["samples"]
    result = adapter.map_daily_payload_to_dto(raw)
    assert not result[1] # Check if step samples is empty

def test_mapping_multiple_empty_step_samples(adapter, all_day_payloads_dto):
    raws = [dto.raw_payload for dto in all_day_payloads_dto]
    _ = [r.pop("samples") for r in raws]
    result = adapter.map_daily_payload_to_dto(raws)

    steps = list(map(lambda x: x is True, result)) # Check if steps samples has content

    assert not all(steps) # Check if all empty
