import os
from typing import Sequence, Mapping, Any, TypeAlias

from .polar import AccessLink


RawDailyPayload: TypeAlias = Mapping[str, Any]


class PolarApiFetcher(object):
    """
    Interface for Polar API source code.
    Returns data in JSON format.
    """
    def __init__(self, client_id, client_secret):
        self.link = AccessLink(client_id, client_secret)

    @property
    def authenticated(self):
        if os.environ.get("POLAR_ACCESS_TOKEN", False):
            return True

    def fetch_day(self, day: str, access_token) -> RawDailyPayload | None:
        payload = self.link.get_activity_day(access_token,
                                          day,
                                          steps=True)
        if payload:
            return payload


    def fetch_date_range(self, from_to: tuple[str, str], access_token) -> Sequence[RawDailyPayload] | None:
        from_, to = from_to
        payloads = self.link.get_activity_date_range(access_token,
                                                     from_=from_,
                                                     to=to,
                                                     steps=True)
        return payloads
