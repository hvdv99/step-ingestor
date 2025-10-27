from __future__ import annotations

from datetime import date as date_cls
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from pydantic import TypeAdapter

from step_ingestor.db import AppUser, ActivitySummary, StepSample, AccessToken
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO, UserDTO, TokenDTO

class StepIngestorRepository:
    """Repository that saves DTOs in the database."""
    def __init__(self, session: Session, *, autocommit: bool = False):
        if session is None:
            raise ValueError("session must be provided")
        self.session: Session = session
        self.autocommit: bool = autocommit

    def _maybe_flush(self) -> None:
        self.session.flush()

    def _maybe_commit(self) -> None:
        if self.autocommit:
            self.session.commit()

    # --- USERS ---
    def add_user(self, user: UserDTO) -> bool:
        """Idempotent insert. Returns True if inserted, False if already existed."""
        stmt = (
            pg_insert(AppUser)
            .values(user.model_dump(exclude={"access_token"}))
            .on_conflict_do_nothing(index_elements=[AppUser.user_id])
        )

        res = self.session.execute(stmt)
        self._maybe_flush()

        if user.access_token:
            self.update_user_access_token(user)

        self._maybe_commit()
        # rowcount can be 0 if no insert happened due to conflict
        return (res.rowcount or 0) > 0

    def update_user_access_token(self, user: UserDTO) -> bool:
        """Create/update the user's access token (one-to-one).
        Returns True when an insert/update occurred, False on no-op conflict.
        """
        if not user.access_token:
            raise ValueError("No access token provided.")

        stmt = pg_insert(AccessToken).values(user.access_token.model_dump())
        stmt = stmt.on_conflict_do_update(
            index_elements=[AccessToken.user_id],
            set_={
                "access_token": stmt.excluded.access_token,
                "issuer": stmt.excluded.issuer,
                "expires_at": stmt.excluded.expires_at,
                "updated_at": sa.func.now(),
            },
        )
        res = self.session.execute(stmt)
        self._maybe_flush()
        self._maybe_commit()
        # With Postgres dialect, upsert returns rowcount 1 for insert or update
        return (res.rowcount or 0) == 1

    def delete_user(self, user: UserDTO) -> bool:
        """Deletes the user and associated rows in other tables (via cascade)."""
        stmt = sa.delete(AppUser).where(AppUser.user_id == user.user_id)
        res = self.session.execute(stmt)
        self._maybe_flush()
        self._maybe_commit()
        return (res.rowcount or 0) == 1

    def get_user_by_id(self, user_id=None, polar_user_id=None) -> UserDTO | None:
        if user_id:
            stmt = (
                sa.select(AppUser, AccessToken)
                .outerjoin(AccessToken, AppUser.user_id == AccessToken.user_id)
                .where(AppUser.user_id == user_id)
            )

        if polar_user_id:
            stmt = (
                sa.select(AppUser, AccessToken)
                .outerjoin(AccessToken, AppUser.user_id == AccessToken.user_id)
                .where(AppUser.polar_user_id == polar_user_id)
            )

        row = self.session.execute(stmt).one_or_none()
        if not row:
            return None
        user, token = row
        u = UserDTO.model_validate(user)
        if token:
            u.access_token = TokenDTO.model_validate(token)
        return u

    def get_access_token(self, user: UserDTO) -> UserDTO | None:
        stmt = sa.select(AccessToken).where(AccessToken.user_id == user.user_id)

        token = self.session.execute(stmt).scalar_one_or_none()
        if token is None:
            return None
        user.access_token = TokenDTO.model_validate(token)
        return user

    # --- ACTIVITY DATA ---
    def get_user_data(self, user: UserDTO) -> list[ActivitySummaryDTO]:
        stmt_summary = sa.select(ActivitySummary).where(ActivitySummary.user_id == user.user_id)

        data: list[ActivitySummaryDTO] = []
        for s in self.session.execute(stmt_summary).scalars():
            dto = ActivitySummaryDTO.model_validate(s)

            stmt_steps = sa.select(StepSample).where(StepSample.timestamp == dto.date)
            steps = self.session.execute(stmt_steps).scalars().all()
            adapter = TypeAdapter(list[StepSampleDTO])
            samples = adapter.validate_python(steps)

            dto.step_samples = samples
            data.append(dto)
        return data

    def ingest_payload(self, payload: Sequence[ActivitySummaryDTO] | ActivitySummaryDTO) -> bool:
        payloads = [payload] if not isinstance(payload, list) else payload

        return all(
            self._upsert_activity_summary(summary) and self._upsert_step_samples_batch(summary.step_samples)
            for summary in payloads
        )

    def _upsert_activity_summary(self, summary: ActivitySummaryDTO | Sequence[ActivitySummaryDTO]) -> int:
        if isinstance(summary, ActivitySummaryDTO):
            summary = [summary]

        rows = [s.model_dump(exclude={"step_samples"}, by_alias=True) for s in summary]

        stmt = pg_insert(ActivitySummary).values(rows)
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
        result = self.session.execute(stmt)
        self._maybe_flush()
        self._maybe_commit()
        return 0 if result.rowcount in (None, -1) else result.rowcount

    def _upsert_step_samples_batch(self,
                                   samples: Sequence[StepSampleDTO] | Sequence[Sequence[StepSampleDTO]]) -> int:
        # When no samples are available for the day:
        if not samples:
            return 1

        # If it's a flat list for a single day, wrap it
        if samples and isinstance(samples[0], StepSampleDTO):
            samples = [samples]

        # Flatten nested list
        rows = [s.model_dump() for day in samples for s in day]

        stmt = pg_insert(StepSample).values(rows).on_conflict_do_nothing()
        result = self.session.execute(stmt)
        self._maybe_flush()
        self._maybe_commit()
        return 0 if result.rowcount in (None, -1) else result.rowcount

    def get_latest_summary_date(self, user: UserDTO) -> date_cls | None:
        """Return the most recent date stored in the daily summary table."""
        stmt = sa.select(sa.func.max(ActivitySummary.date)).where(
            ActivitySummary.user_id == user.user_id
        )
        return self.session.execute(stmt).scalar_one_or_none()
