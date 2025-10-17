from step_ingestor.services.ingestion import date_windows_28d

def test_date_range_util():
    ranges = date_windows_28d()
    assert len(ranges) == (365 // 28) + 1

def test_range_short():
    # TODO
    pass
