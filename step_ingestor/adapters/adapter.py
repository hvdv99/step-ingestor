import datetime as dt
from typing import Any, Sequence, TypeAlias, Mapping
from step_ingestor.dto import ActivitySummaryDTO, UserDTO

RawDailyPayload: TypeAlias = Mapping[str, Any] # Raw JSON Response from API


class Adapter:
    """Adapter that maps JSON (source) to DTOs (target)
    Source: Polar API interface
    Target: Repository"""

    def __init__(self, dto_dact, dto_step, adaptee=None):
        self._adaptee = adaptee
        self._out_forms = {"dto_dact": dto_dact,
                           "dto_step": dto_step}

    def get_activity_day(self, day: str, access_token, user_id) -> Sequence[ActivitySummaryDTO] | None:
        raw = self._adaptee.get_activity_day(day=day,
                                             access_token=access_token,
                                             steps=True)
        # Polar response is empty
        if not raw:
            return None
        return self._raw_payload_to_dto(raw, user_id)

    def get_activity_date_range(self, date_from, date_to, user: UserDTO) -> Sequence[ActivitySummaryDTO] | None:
        raw = self._adaptee.get_activity_date_range(date_from=date_from,
                                                    to=date_to,
                                                    access_token=user.access_token.token,
                                                    steps=True)
        # Polar response is empty
        if not raw:
            return None
        return self._raw_payload_to_dto(raw, user_id=user.user_id)

    def _raw_payload_to_dto(self, raw, user_id) -> Sequence[ActivitySummaryDTO] | None:
        if not raw:
            return None

        if not isinstance(raw, list):
            raws = [raw]
        else:
            raws = raw

        payloads_ = []
        for r in raws:
            # Check what data to parse
            if r:
                try:
                    step_samples = r["samples"]["steps"]["samples"]
                except KeyError:
                    step_samples = None
            else:
                continue

            # Parse step samples
            if step_samples:
                step_samples = [self._out_forms["dto_step"](**{**s, "user_id": user_id}) for s in step_samples]

            # Parse daily activity
            activity_dto = self._out_forms["dto_dact"](
                **{
                    **r,
                    "user_id": user_id,
                    "date": dt.datetime.fromisoformat(r["start_time"]).date().isoformat(),
                    "step_samples": step_samples
                }
            )
            payloads_.append(activity_dto)
        if len(payloads_) == 1:
            return payloads_.pop()
        return payloads_
