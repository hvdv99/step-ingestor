# TODO:
# 1) add role-based checks (or remove the admin route until you have them),
# 2) refactor session handling so secrets never leave the server,
# 3) harden logout with POST/CSRF.

import os
import sys
import logging

from flask import Flask, render_template, request, g, session, redirect, abort
from markupsafe import Markup

from step_ingestor.client.src.security.user import get_user_from_session
from step_ingestor.client.src.security.decorators import login_required
from step_ingestor.client.src.routeControllers.oauth import oauthPage, initOauthClient
from step_ingestor.client.src.config.appConfig import loadAppConfig

from step_ingestor.services import IngestionService
from step_ingestor.analytics.step_toolbox import UserStepPlotter

# https://gist.github.com/thomasdarimont/6a3905778520b746ff009cf3a41643e9
# https://stackoverflow.com/a/78419713/2746323
# get application config

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

appConfig = loadAppConfig()

initOauthClient()

app = Flask(__name__, template_folder="templates")
app.secret_key = appConfig.flaskSecret
app.register_blueprint(oauthPage, urlprefix="/oauth")

with app.app_context():
    app.service = service = IngestionService(os.environ["POLAR_CLIENT_ID"],
                                             os.environ["POLAR_CLIENT_SECRET"])
@app.route('/')
def index():
    return render_template("home.html")

@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html")

@app.route("/dashboard/<freq>")
@login_required
def dashboard(freq):

    freqs = {'hour': 'h',
             'day': 'd',
             'week': 'W',
             'month': 'ME',
             'quarterly': 'QE',
             'year': 'YE'}

    if freq not in freqs:
        abort(404)
    else:
        freq = freqs.pop(freq)

    g.freqs = freqs

    from_ = request.args.get('from', None)
    to = request.args.get('to', None)

    user = get_user_from_session()
    user_data = app.service.repo.get_user_steps(user["user_id"])
    plotter = UserStepPlotter(user_data)
    g.plot = Markup(plotter.create_plot(freq, from_, to))

    return render_template("dashboard.html")

@app.route('/admin')
@login_required()
def admin():
    return render_template("admin.html")

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)
