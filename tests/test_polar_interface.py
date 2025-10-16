import pytest
from requests import HTTPError

def test_get_activity_date_range_3(polar_interface, access_token):
    activities = polar_interface.get_activity_date_range(access_token=access_token,
                                                         date_from="2025-09-01",
                                                         date_to="2025-09-03",
                                                         steps=True)
    assert isinstance(activities, list)
    assert len(activities) == 3

def test_get_activity_date_range_28(polar_interface, access_token):
    activities = polar_interface.get_activity_date_range(access_token=access_token,
                                                         date_from="2025-07-01",
                                                         date_to="2025-07-28",
                                                         steps=True)

    assert isinstance(activities, list)
    assert len(activities) == 28
    assert all(activities)

def test_get_activity_date_range_1(polar_interface, access_token, mockserver):
    activities = polar_interface.get_activity_date_range(access_token=access_token,
                                                         date_from="2025-07-01",
                                                         date_to="2025-07-01",
                                                         steps=True)

    assert isinstance(activities, list)
    assert len(activities) == 1
    assert all(activities)

def test_get_range_too_wide(polar_interface, access_token, mockserver):
    with pytest.raises(HTTPError):
        polar_interface.get_activity_date_range(access_token=access_token,
                                                date_from="2025-06-01",
                                                date_to="2025-07-01",
                                                steps=True)

def test_get_range_too_old(polar_interface, access_token, mockserver):
    with pytest.raises(HTTPError):
        polar_interface.get_activity_date_range(access_token=access_token,
                                                date_from="2024-06-01",
                                                steps=True)
