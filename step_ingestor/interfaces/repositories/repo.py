from __future__ import annotations

from datetime import datetime, timezone
from datetime import date as date_cls
from typing import Sequence, TypeAlias

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker, Session
from pydantic import TypeAdapter

from step_ingestor.db import AppUser, ActivitySummary, StepSample, AccessToken
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO, UserDTO, TokenDTO

DailyPayload: TypeAlias = tuple[ActivitySummaryDTO, Sequence[StepSampleDTO]]

class StepIngestorRepository:
    """Repository that saves DTOs in the database."""

    def __init__(self, session_factory: sessionmaker, *, autocommit: bool = True):
        self._session_factory = session_factory
        self._autocommit = autocommit

    def _begin(self) -> Session:
        """returns a new session for each CRUD operation"""
        return self._session_factory()

    def add_user(self, user: UserDTO) -> bool:
        """Idempotent insert. Returns True if inserted, False if already existed."""
        stmt = pg_insert(AppUser).values(user.model_dump_json(exclude={"access_token"}))
        stmt = stmt.on_conflict_do_nothing(index_elements=[AppUser.user_id])

        with self._begin() as db:
            res = db.execute(stmt).rowcount()
            db.commit()

        if user.access_token:
            self.update_user_access_token(user)

        return res > 0

    def delete_user(self, user: UserDTO) -> int:
        """Deletes the user and associated rows in other tables (cascade)."""
        stmt = sa.delete(AppUser).where(AppUser.user_id == user.user_id)
        with self._begin() as db:
            res = db.execute(stmt)
            db.commit()
            return res.rowcount == 1

    def get_user_by_id(self, user_id) -> UserDTO | None:
        stmt = sa.select([AppUser, AccessToken]).where(AppUser.user_id == user_id)
        with self._begin() as db:
            res = db.execute(stmt).one_or_none()

        if res:
            user, token = res
            t = TokenDTO.model_validate(token)
            u = UserDTO.model_validate(user)
            u.access_token = t
            return u
        else:
            return None

    def update_user_access_token(self, user: UserDTO) -> int:
        """Creates/updates the one-to-one token row for the user.
        Returns 1 on insert/update, 0 on conflict.
        """
        with self._begin() as db:
            stmt = pg_insert(AccessToken).values(
                user.access_token.model_dump_json()
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
            return res.rowcount == 1

    def get_access_token(self, user: UserDTO) -> UserDTO | None:
        with self._begin() as db:
            stmt = sa.select(AccessToken).where(AccessToken.user_id == user.user_id)
            token = db.execute(stmt).one_or_none()
            if token:
                token_dto = TokenDTO.model_validate(token)
                user.access_token = token_dto
                return user
            return None

    def get_user_data(self, user: UserDTO) -> list[ActivitySummaryDTO]:
        stmt_summary = sa.select(ActivitySummary).where(ActivitySummary.user_id == user.user_id)
        data = []
        with self._begin() as db:
            summaries = db.execute(stmt_summary).scalars()
            for s in summaries:
                dto = ActivitySummaryDTO.model_validate(s)

                stmt_steps = sa.select(StepSample).where(StepSample.timestamp == dto.date)
                steps = db.execute(stmt_steps).scalars()
                adapter = TypeAdapter(list[StepSampleDTO])
                samples = adapter.validate_python(steps)

                dto.step_samples = samples
                data.append(dto)
            return data

    def ingest_payload(self, payload: Sequence[ActivitySummaryDTO]) -> bool:
        if not isinstance(payload, list):
            payloads = [payload]
        else:
            payloads = payload

        return all(
            self._upsert_activity_summary(summary) and self._upsert_step_samples_batch(summary.step_samples)
            for summary in payloads
        )

    def _upsert_activity_summary(self, summary: ActivitySummaryDTO | Sequence[ActivitySummaryDTO]) -> int:
        if not isinstance(summary, Sequence):
            summary = [summary]

        summary = [s.model_dump(exclude={"step_samples"}, by_alias=True) for s in summary]

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
                                   samples: Sequence[StepSampleDTO] | Sequence[Sequence[StepSampleDTO]]) -> int:

        # When no samples are available for the day:
        if not samples:
            return 1

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

    def get_latest_summary_date(self, user: UserDTO) -> date_cls | None:
        """Return the most recent date stored in the daily summary table."""
        with self._begin() as db:
            stmt = sa.select(sa.func.max(ActivitySummary.date)).where(ActivitySummary.user_id == user.user_id)
            result = db.execute(stmt).scalar_one_or_none()
            return result

def _now() -> datetime:
    return datetime.now(timezone.utc)
