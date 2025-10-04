from .polar_resource import Resource


class DailyActivityBeta(Resource):
    """"""
    def fetch(self, access_token,
              date: str=None,
              from_: str=None,
              to: str=None,
              steps=False,
              activity_zones=False,
              inactivity_stamps=False):
        """Fetch activities for a given date or for a date range"""

        if date and from_:
            raise ValueError("Can only fetch single day or range of dates")

        params = {}

        query_flags = {
            "from": from_,
            "to": to,
            "steps": steps,
            "activity_zones": activity_zones,
            "inactivity_stamps": inactivity_stamps,
        }

        for key, value in query_flags.items():
            if value is None:
                continue
            params[key] = str(value).lower() if isinstance(value, bool) else value

        if date is None: date = ''
        response = self._get(endpoint="/users/activities/{date}".format(date=date),
                         access_token=access_token,
                         params=params if params else None)

        if not response:
            return None
        return response
