"""
Contains DTOs for Step Samples and for Daily Activity Summary
"""

import datetime as dt
from typing import Any, Iterable, Mapping

from pydantic import BaseModel

class UserDTO(BaseModel):
    user_id: str
    access_token: str
    created_at: dt.datetime
    updated_at: dt.datetime

class StepSampleDTO(BaseModel):
    user_id: str
    timestamp: dt.datetime
    steps: int

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "StepSampleDTO":
        return cls(timestamp=raw["timestamp"], steps=raw["steps"])

class ActivitySummaryDTO(BaseModel):
    user_id: str
    date: dt.date
    start_time: dt.datetime | None = None
    end_time: dt.datetime | None = None
    active_duration: dt.timedelta | None = None
    inactive_duration: dt.timedelta | None = None

    daily_activity: float | None = None
    calories: int | None = None
    active_calories: int | None = None
    steps: int | None = None
    inactivity_alert_count: int | None = None
    distance_from_steps: float | None = None

    def step_samples(self) -> list[StepSampleDTO]:

        steps_payload = self.raw_payload.get("samples", {}).get("steps", {}) if self.raw_payload else {}

        raw_samples: Iterable[Mapping[str, Any]] = steps_payload.get("samples", []) if isinstance(steps_payload, Mapping) else []
        samples: list[StepSampleDTO] = []

        for sample in raw_samples:
            if not isinstance(sample, Mapping):
                continue
            if "timestamp" not in sample or "steps" not in sample:
                continue
            samples.append(StepSampleDTO.from_raw(sample))
        return samples
