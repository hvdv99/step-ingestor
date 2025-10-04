import os
import logging
import requests
from datetime import datetime
from markupsafe import Markup
from flask import Blueprint, redirect, url_for, current_app, session, abort, request, g, render_template

from step_ingestor.client.src.config.appConfig import getAppConfig
from step_ingestor.client.src.security.user import create_user_session, clear_user_session, get_user_from_session
from step_ingestor.client.src.security.decorators import login_required
from step_ingestor.analytics.step_toolbox import UserStepPlotter

from step_ingestor.services import IngestionService

dashboard_page = Blueprint('dashboard',
                           __name__,
                           template_folder='templates')

service = IngestionService(os.environ["POLAR_CLIENT_ID"],
                           os.environ["POLAR_CLIENT_SECRET"])

@dashboard_page.url_value_preprocessor
def pull_freq(endpoint, values):
    if values.get("freq") is None:
        g.freq = 'm'
        return
    g.freq = values.pop('freq', 'm')

@dashboard_page.url_defaults
def add_freq(endpoint, values):
    if 'freq' not in values and getattr(g, 'freq', None):
        if current_app.url_map.is_endpoint_expecting(endpoint, 'freq'):
            values['freq'] = g.freq

@dashboard_page.route("/<freq>")
@login_required
def dashboard(freq):
    #TODO URL Path input verification

    user = get_user_from_session()

    from_ = request.args.get('from', None)
    to = request.args.get('to', None)

    user_data = service.repo.get_user_steps(user["user_id"])

    plotter = UserStepPlotter(user_data)
    g.plot = Markup(plotter.create_plot(freq, from_, to))

    return render_template("dashboard.html")
