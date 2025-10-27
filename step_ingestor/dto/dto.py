"""Contains DTOs for Step Samples and for Daily Activity Summary"""
import datetime as dt

from pydantic import BaseModel, Field, ConfigDict


class TokenDTO(BaseModel):
    token: str = Field(alias="access_token")
    issuer: str
    issued_at: dt.datetime
    expires_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)


class UserDTO(BaseModel):
    user_id: str
    polar_user_id: str
    access_token: TokenDTO | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)


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

if __name__ == "__main__":
    from datetime import datetime
    import uuid
    from zoneinfo import ZoneInfo
    now = datetime.now(tz=ZoneInfo("Europe/Amsterdam"))
    print([UserDTO(user_id=uuid.uuid4().hex,
             polar_user_id=uid,
             created_at=now,
             updated_at=now).model_dump_json() for uid in ["123", "456", "789"]])
