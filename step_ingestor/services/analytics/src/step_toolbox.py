import pandas as pd
import plotly.express as px


class UserStepPlotter:
    def __init__(self, user_steps):
        self.user_steps = pd.DataFrame(user_steps).set_index("timestamp")

    def create_plot(self, freq, from_=None, to=None):
        sel = self.user_steps[from_:to]["steps"].resample(freq).sum()
        fig = px.bar(sel, x=sel.index, y="steps")

        return fig.to_html(include_plotlyjs='cdn', full_html=False)
