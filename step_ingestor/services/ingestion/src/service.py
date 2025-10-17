"""Contains operational application logic to retrieve data from the polar API and store it in the database."""
import logging
import datetime as dt

from step_ingestor.dto import UserDTO
from .utils import date_windows_28d


class IngestionService:
    def __init__(self, provider, repo):
        self.provider = provider
        self.repo = repo

    def add_user(self, *, user: UserDTO):
        """Register the user in the database"""
        return self.repo.add_user(user)

    def get_access_token(self, *, user):
        return self.repo.get_access_token(user)

    def update_access_token(self, *, user: UserDTO):
        return self.repo.upsert_access_token(user)

    def delete_user(self, *, user: UserDTO):
        pass

    def _populate_db_historical(self, user: UserDTO):
        """Stores data from Polar API from last 365 days in DB."""
        ranges = date_windows_28d()
        for r in ranges:
            date_from, date_to = r
            logging.debug("Fetching range from {} to {}".format(date_from, date_to))
            payload = self.provider.get_activity_date_range(date_from=date_from,
                                                            date_to=date_to,
                                                            user=user)
            if payload:
                self.repo.ingest_payload(payload=payload)
        return True

    def refresh_user_data(self, *, user: UserDTO):
        # Get latest stored date
        latest_date = self.repo.get_latest_summary_date(user)

        # When the user does not have data in the DB
        if latest_date is None:
            return self._populate_db_historical(user)

        # Get date after latest saved day
        next_date = latest_date + dt.timedelta(days=1)
        today = dt.date.today()

        # When all available data has been saved already
        if next_date > today:
            return True

        # When there are other dates in the API and not in the DB
        else:
            date_from, date_to = (next_date.isoformat(), today.isoformat())
            date_range_data = self.provider.get_activity_date_range(date_from=date_from,
                                                                    date_to=date_to,
                                                                    user=user)
            if date_range_data:
                self.repo.ingest_payload(payload=date_range_data)
        return True
