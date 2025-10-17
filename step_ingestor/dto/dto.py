"""Contains DTOs for Step Samples and for Daily Activity Summary"""
import datetime as dt

from pydantic import BaseModel, Field, ConfigDict


class TokenDTO(BaseModel):
    token: str
    issuer: str
    issued_at: dt.datetime
    expires_at: dt.datetime


class UserDTO(BaseModel):
    user_id: str
    access_token: TokenDTO | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class StepSampleDTO(BaseModel):
    user_id: str
    timestamp: dt.datetime
    steps: int
    model_config = ConfigDict(from_attributes=True)


class ActivitySummaryDTO(BaseModel):
    user_id: str
    date: dt.date
    start_time: dt.datetime
    end_time: dt.datetime
    active_duration: dt.timedelta
    inactive_duration: dt.timedelta

    daily_activity: float
    calories: int
    active_calories: int
    total_steps: int = Field(alias="steps")
    step_samples: list[StepSampleDTO] | None = None
    inactivity_alert_count: int
    distance_from_steps: float
    model_config = ConfigDict(from_attributes=True)
