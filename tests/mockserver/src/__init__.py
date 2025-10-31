import datetime as dt
from .mocker import SampleMocker as SampleMocker


# Helpers
def token_ok(access_token, user_db) -> bool:
    """Checks if a given access token is in the user db"""
    access_token = access_token.split(" ")[1]
    if access_token in user_db:
        return True
    return False

def get_dates_interval(date_from, date_to) -> list:
    """Retrieves all dates as strings in format YYYY-MM-DD between the closed interval of date_from and date_to.
    """
    d_start = dt.date.fromisoformat(date_from)
    d_end = dt.date.fromisoformat(date_to)
    d_range = []
    d_current = d_start
    while d_current != d_end + dt.timedelta(days=1):
        d_range.append(d_current.isoformat())
        d_current += dt.timedelta(days=1)
    return d_range
