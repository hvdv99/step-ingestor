"""Contains operational application logic"""
import logging
from datetime import date, timedelta
from typing import Sequence, TypeAlias

from step_ingestor.adapters import Adapter
from step_ingestor.repositories import StepIngestorRepository
from step_ingestor.db import SessionFactory
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO

from .utils import date_windows_28d

DailyPayload: TypeAlias = tuple[ActivitySummaryDTO, Sequence[StepSampleDTO]]

class IngestionService:
    """Service that uses adapters for the DB and Polar API source code"""
    def __init__(self, client_id, client_secret):
        self.provider = Adapter(client_id, client_secret)
        self.repo = StepIngestorRepository(SessionFactory)

    def register_user(self, user_id):
        return self.repo.add_user(user_id)

    def update_client_credentials(self, user_id, access_token, expires_at):
        return self.repo.upsert_access_token(user_id=user_id, access_token=access_token,
                                             issuer="polar", expires_at=expires_at)

    def fetch_access_token(self, user_id):
        return self.repo.fetch_access_token(user_id=user_id)

    def retrieve_user_steps(self, user_id):
        pass

    def populate_db_historical(self, access_token, user_id):
        """Stores data from Polar API from last 365 days in DB."""
        ranges = date_windows_28d()
        for r in ranges:
            logging.debug("Fetching range {}".format(r))
            payload = self.provider.fetch_date_range(from_to=r,
                                                     access_token=access_token, user_id=user_id)
            if payload:
                self.repo.ingest_payload(payload=payload)
        return True

    def refresh_user_data(self, access_token, user_id):
        # When the user does not have data in the DB
        latest_date = self.repo.get_latest_summary_date(user_id)
        if latest_date is None:
            return self.populate_db_historical(access_token, user_id)

        # Get date after latest saved day
        next_date = latest_date + timedelta(days=1)
        today = date.today()

        # When all available data has been saved already
        if next_date > today:
            return True

        # When there are other dates in the API and not in the DB
        else:
            date_range = (next_date.isoformat(), today.isoformat())
            date_range_data = self.provider.fetch_date_range(from_to=date_range,
                                                             access_token=access_token, user_id=user_id)

            if date_range_data:
                self.repo.ingest_payload(payload=date_range_data)
        return True