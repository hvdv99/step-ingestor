from __future__ import annotations

from datetime import datetime, timezone
from datetime import date as date_cls
from typing import Sequence, TypeAlias, Protocol

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker

from step_ingestor.db import AppUser, ActivitySummary, StepSample, AccessToken
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO

DailyPayload: TypeAlias = tuple[ActivitySummaryDTO, Sequence[StepSampleDTO]]

class StepIngestorRepository:
    """Repository that saves DTOs in the database."""

    def __init__(self, session_factory: sessionmaker, *, autocommit: bool = True):
        self._session_factory = session_factory
        self._autocommit = autocommit

    def _begin(self):
        """Allows a fresh session for each CRUD operation"""
        return self._session_factory()

    def add_user(self, user_id: str) -> int:
        """Idempotent insert. Returns 1 if inserted, 0 if already existed."""
        stmt = pg_insert(AppUser).values({"user_id": user_id})
        stmt = stmt.on_conflict_do_nothing(index_elements=[AppUser.user_id])

        with self._begin() as db:
            res = db.execute(stmt)
            db.commit()
            return res.rowcount or 0

    def delete_user(self, user_id: str) -> int:
        """Deletes the user and associated rows in other tables (cascade).
        Returns the number of rows deleted (0 or 1)."""
        stmt = sa.delete(AppUser).where(AppUser.user_id == user_id)
        with self._begin() as db:
            res = db.execute(stmt)
            db.commit()
            return res.rowcount or 0

    def upsert_access_token(self, *,
                            user_id: str,
                            access_token: str,
                            issuer: str,
                            expires_at: datetime | None = None) -> int:
        """Creates/updates the one-to-one token row for the user.
        Returns 1 on insert/update, 0 on conflict.
        """
        with self._begin() as db:
            stmt = pg_insert(AccessToken).values(
                {
                    "user_id": user_id,
                    "access_token": access_token,
                    "issuer": issuer,
                    "expires_at": expires_at,
                }
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=[AccessToken.user_id],
                set_={
                    "access_token": stmt.excluded.access_token,
                    "issuer": stmt.excluded.issuer,
                    "expires_at": stmt.excluded.expires_at,
                    "updated_at": sa.func.now()
                },
            )

            res = db.execute(stmt)
            db.commit()
            return res.rowcount or 0

    def fetch_access_token(self, user_id):
        with self._begin() as db:
            stmt = sa.select(AccessToken.access_token).where(AccessToken.user_id == user_id)
            result = db.execute(stmt).scalar_one_or_none()
            return result


    def ingest_payload(self, payload: DailyPayload | Sequence[DailyPayload]) -> bool:
        if isinstance(payload, tuple):
            payloads = [payload]
        else:
            payloads = payload

        return all(
            bool(self._upsert_activity_summary(summary)) and
            bool(self._upsert_step_samples_batch(samples))
            for summary, samples in payloads
        )

    def _upsert_activity_summary(self, summary: ActivitySummaryDTO | Sequence[ActivitySummaryDTO]) -> int:

        if not isinstance(summary, Sequence):
            summary = [summary]

        summary = [s.model_dump() for s in summary]

        stmt = pg_insert(ActivitySummary).values(
            summary
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[ActivitySummary.user_id, ActivitySummary.date],
            set_={
                "start_time": stmt.excluded.start_time,
                "end_time": stmt.excluded.end_time,
                "active_duration": stmt.excluded.active_duration,
                "inactive_duration": stmt.excluded.inactive_duration,
                "daily_activity": stmt.excluded.daily_activity,
                "calories": stmt.excluded.calories,
                "active_calories": stmt.excluded.active_calories,
                "steps": stmt.excluded.steps,
                "inactivity_alert_count": stmt.excluded.inactivity_alert_count,
                "distance_from_steps": stmt.excluded.distance_from_steps,
                "updated_at": sa.func.now(),
            },
        )

        with self._begin() as db:
            result = db.execute(stmt)
            db.commit()
            return 0 if result.rowcount in (None, -1) else result.rowcount

    def _upsert_step_samples_batch(self,
                                   samples: Sequence[StepSampleDTO] | Sequence[Sequence[StepSampleDTO]]
                                   ) -> int:

        # When no samples are available for the day:
        if not samples:
            return 0

        # Situation when there are multiple days in samples
        if isinstance(samples[0], StepSampleDTO):
            samples = [samples]  # Creates nested list

        # Flatten nested list
        rows = [s.model_dump() for day in samples for s in day]

        stmt = pg_insert(StepSample).values(rows)
        stmt = stmt.on_conflict_do_nothing()

        with self._begin() as db:
            result = db.execute(stmt)
            db.commit()
            return 0 if result.rowcount in (None, -1) else result.rowcount

    def get_latest_summary_date(self, user_id) -> date_cls | None:
        """Return the most recent date stored in the daily summary table."""
        with self._begin() as db:
            stmt = sa.select(sa.func.max(ActivitySummary.date)).where(ActivitySummary.user_id == user_id)
            result = db.execute(stmt).scalar_one_or_none()
            return result

    def get_user_steps(self, user_id):
        # TODO: Move to a query repo
        with self._begin() as db:
            stmt = sa.select(StepSample.timestamp, StepSample.steps).where(StepSample.user_id == user_id)
            result = db.execute(stmt).all()
            return result

def _now() -> datetime:
    return datetime.now(timezone.utc)
