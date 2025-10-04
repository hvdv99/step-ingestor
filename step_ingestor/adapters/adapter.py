import datetime as dt
from typing import Any, Sequence, TypeAlias, Mapping

from step_ingestor.interfaces import PolarApiFetcher
from step_ingestor.dto import ActivitySummaryDTO, StepSampleDTO

RawDailyPayload: TypeAlias = Mapping[str, Any]
DailyPayload: TypeAlias = tuple[ActivitySummaryDTO, Sequence[StepSampleDTO]]


class Adapter:
    """Adapter that maps JSON (source) to DTOs (target)
    Source: Polar API interface
    Target: Repository"""

    def __init__(self, client_id, client_secret):
        self._adaptee = PolarApiFetcher(client_id, client_secret)

    def fetch_day(self, day: str, access_token, user_id) -> Sequence[DailyPayload] | None:

        raw = self._adaptee.fetch_day(day, access_token)

        # Polar response is empty
        if not raw:
            return None

        return self._raw_payload_to_dto(raw, user_id)

    def fetch_date_range(self, from_to: tuple[str, str], access_token, user_id) -> Sequence[DailyPayload] | None:
        raw = self._adaptee.fetch_date_range(from_to, access_token)

        # Polar response is empty
        if not raw:
            return None

        return self._raw_payload_to_dto(raw, user_id)

    @staticmethod
    def _raw_payload_to_dto(raw, user_id) -> Sequence[DailyPayload]:
        if not isinstance(raw, list):
            raws = [raw]
        else:
            raws = raw

        payloads_ = []
        for r in raws:
            summary_dto = ActivitySummaryDTO(
                **{
                    **r,
                    "user_id": user_id,
                    "date": dt.datetime.fromisoformat(r["start_time"]).date().isoformat(),
                }
            )

            samples = r.get("samples").get("steps").get("samples")
            if samples:
                sample_dtos = [StepSampleDTO(**{**s, "user_id": user_id}) for s in samples]
            else:
                sample_dtos = []

            payloads_.append(
                (summary_dto, sample_dtos)
            )
        return payloads_
