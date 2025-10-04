from __future__ import annotations
from typing import Protocol, Sequence, TypeAlias
from datetime import datetime, date as date_cls

from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO

DailyPayload: TypeAlias = tuple[ActivitySummaryDTO, Sequence[StepSampleDTO]]

class StepRepository(Protocol):
    """Target interface for persistence used by the service layer."""

    # --- User management ---
    def add_user(self, user_id: str) -> int:
        """Idempotent insert. Returns 1 if inserted, 0 if already existed."""

    def delete_user(self, user_id: str) -> int:
        """Deletes user (+ cascades). Returns 0 or 1."""

    # --- Tokens ---
    def upsert_access_token(
        self, *,
        user_id: str,
        access_token: str,
        issuer: str,
        expires_at: datetime | None = None,
    ) -> int:
        """Insert or update the user's access token. Returns affected row count (0/1)."""

    # --- Ingestion ---
    def ingest_payload(self, payload: DailyPayload | Sequence[DailyPayload]) -> bool:
        """Persist one or many (summary, steps[]) payloads. Returns True on success."""

    # --- Queries ---
    def get_latest_summary_date(self, user_id: str) -> date_cls | None:
        """Return the most recent ActivitySummary.date for the user, else None."""
