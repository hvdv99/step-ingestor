import datetime as dt
from step_ingestor.services.ingestion import date_windows_28d

def test_date_range_util():
    ranges = date_windows_28d()
    assert len(ranges) == (365 // 28) + 1

def test_range_short():
    last_saved = dt.date.fromisoformat("2025-06-16")
    today = dt.date.fromisoformat("2025-10-01")
    days_back = (today - last_saved).days
    ranges = date_windows_28d(today=today, days_back=days_back)
    print(ranges)
    assert len(ranges) == 4