import datetime as dt
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException, Query

from src import SampleMocker, token_ok, get_dates_interval

sample_mocker = SampleMocker(fp="mockdata/mockdata.json")

USER_DB = {"a263a8c1610f45df8125348bd0de72e1": "123",
           "a8f90d69837b4c3d840413beaed4c799": "456",
           "6789b404d3d446b8b896d4453f574f1e": "789"}
app = FastAPI()


@app.get("/users/activities/")
async def get_daily_activity(access_token: Annotated[str, Header(alias="Authorization")],
                             date_from: Annotated[str, Query(alias="from")],
                             date_to: Annotated[str | None, Query(alias="to")] = None):
    """Get mockdata for a date range"""

    # Check token
    if not token_ok(access_token, USER_DB):
        raise HTTPException(
            status_code=404,
            detail="User not found",
            headers={"X-Error": "There goes my user"},
        )

    # Fetch query params
    if not date_to:
        date_to = dt.date.today().isoformat()

    dt_date_from = dt.date.fromisoformat(date_from)
    dt_date_to = dt.date.fromisoformat(date_to)

    d_interval = (dt_date_to - dt_date_from).days
    n_d_hist = (dt.date.today() - dt_date_from).days

    # Check query params: days old
    # a. not older than 365
    # b. not older than 28 days
    if (n_d_hist > 365) or (d_interval > 28):
        raise HTTPException(
            status_code=400,
            detail="Invalid or too old date. Cannot be older than 365 days."
        )

    # Get date ranges
    dates = get_dates_interval(date_from, date_to)

    # Create mocks
    mocks = []
    for d in dates:
        mocks.append(
            sample_mocker.create_mock_sample(d)
        )

    # Return result
    return mocks
