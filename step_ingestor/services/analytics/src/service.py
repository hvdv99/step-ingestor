import pandas as pd
import plotly.express as px


class UserStepPlotter:
    def __init__(self, user_data):
        self.user_data = user_data

    @property
    def user_steps(self):
        step_records = [
            step.model_dump() for summary in self.user_data
            if summary.step_samples  # Case: no step samples
            for step in summary.step_samples
        ]
        return pd.DataFrame(step_records).set_index("timestamp")

    def create_plot(self, freq, from_=None, to=None):
        sel = self.user_steps[from_:to]["steps"].resample(freq).sum()
        fig = px.bar(sel, x=sel.index, y="steps")

        return fig.to_html(include_plotlyjs='cdn', full_html=False)
