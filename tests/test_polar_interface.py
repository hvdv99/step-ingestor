import pytest
from requests import HTTPError

def test_fetch_day(interface, access_token):
    payload_day = interface.fetch_day("2025-09-01", access_token)
    assert payload_day

def test_fetch_date_historic(interface, date_str_old, access_token):
    """Tests that a date older than 365 days results in an HTTP error"""
    with pytest.raises(HTTPError):
        interface.fetch_day(date_str_old, access_token)

def test_fetch_date_tomorrow(interface, date_str_tomorrow, access_token):
    """Tests that fetching tomorrow's date returns an empty response"""
    payload = interface.fetch_day(date_str_tomorrow, access_token)
    assert payload is None

def test_fetch_date_range_3(interface, access_token):
    activities = interface.fetch_date_range(("2025-09-01", "2025-09-03"), access_token)

    assert isinstance(activities, list)
    assert len(activities) == 3

def test_fetch_date_range_28(interface, access_token):
    activities = interface.fetch_date_range(("2025-07-01", "2025-07-28"), access_token)

    assert isinstance(activities, list)
    assert len(activities) == 28
    assert all(activities)
