def test_date_range_util():
    from step_ingestor.services.utils import date_windows_28d
    ranges = date_windows_28d()
    assert len(ranges) == (365 // 28) + 1
