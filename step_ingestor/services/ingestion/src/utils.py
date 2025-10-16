from datetime import date, timedelta
from typing import List, Tuple, Optional

def date_windows_28d(today: Optional[date] = None,
                     days_back: int = 365,
                     window_days: int = 28) -> List[Tuple[str, str]]:
    """
    Build non-overlapping date windows counting backwards from `today`.

    - The start date and the end date of each window are considered part of the range
    - The first window ends on `today`.
    - The last window starts exactly `days_back` days before `today`
      and may be shorter than `window_days`.

    Args:
        days_back: How many days back from today to cover (default 365).
        window_days: Size of each window in days (default 28).
        today: Override for current date (useful for testing).

    Returns:
        List of (start_date, end_date) tuples as 'YYYY-MM-DD' strings,
        ordered from newest to oldest window.
    """
    if today is None:
        today = date.today()

    start_bound = today - timedelta(days=days_back)
    windows: List[Tuple[str, str]] = []

    window_end = today
    one_day = timedelta(days=1)
    span = timedelta(days=window_days - 1)  # inclusive span

    while window_end >= start_bound:
        window_start = max(start_bound, window_end - span)
        windows.append((window_start.isoformat(), window_end.isoformat()))
        window_end = window_start - one_day  # step back with no overlap

    return windows
