import random as rd
import datetime as dt
import isodate
import json


class SampleMocker:
    def __init__(self, fp):
        self.fp = fp
        self._mockdata = None

    @property
    def mockdata(self):
        if self._mockdata is None:
            with open(self.fp, "r") as f:
                data = json.load(f)
                self._mockdata = data
        return self._mockdata

    def create_mock_sample(self, date: str):
        # Get random existing sample
        r_d_activ = rd.choice(self.mockdata)

        # Do date updates
        r_d_activ_upd = self._update_time_values(date, r_d_activ)

        # Return
        return r_d_activ_upd

    def _update_time_values(self, date: str, d_activities):
        new_dates = self.__create_time_values(date)
        activities_start = new_dates["start_time"]
        for k, v in new_dates.items():
            d_activities[k] = v

        samples = d_activities.get("samples")
        if "steps" in samples:
            s_samples = samples["steps"]["samples"]
            s_samples_upd = self.__update_samples(activities_start, s_samples)
            d_activities["samples"]["steps"]["samples"] = s_samples_upd
        return d_activities

    @staticmethod
    def __create_time_values(date: str):
        start_dt_obj = dt.datetime.fromisoformat(date)

        rmin = rd.randint(0, 4)
        rsec = rd.randint(0, 59)
        rhour = rd.randint(20, 23)

        start_dt_obj += dt.timedelta(minutes=rmin, seconds=rsec)
        end_dt_obj = start_dt_obj + dt.timedelta(hours=rhour)

        duration = end_dt_obj - start_dt_obj
        ratio_active = duration * 0.67
        ratio_inactive = duration * 0.33

        start = isodate.isodatetime.datetime_isoformat(start_dt_obj)
        end = isodate.isodatetime.datetime_isoformat(end_dt_obj)
        active = isodate.duration_isoformat(ratio_active)
        inactive = isodate.duration_isoformat(ratio_inactive)

        return {"start_time": start, "end_time": end, "active_duration": active, "inactive_duration": inactive}

    @staticmethod
    def __update_samples(dt_start: str, samples):
        dt_start = dt.datetime.fromisoformat(dt_start)
        dt_new = dt_start
        for s in samples:
            s_rd = rd.randint(1, 10)
            s_offset = dt.timedelta(seconds=s_rd)
            dt_new += s_offset
            s["timestamp"] = isodate.datetime_isoformat(dt_new)
        return samples
