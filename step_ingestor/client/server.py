# TODO:
# 1) refactor session handling so secrets never leave the server,
# 2) harden logout with POST/CSRF.

import os
import sys
import logging

from flask import render_template, request, g, abort
from markupsafe import Markup
from cryptography import fernet

from step_ingestor.client.src.security.init_app import init_app
from step_ingestor.client.src.routes.oauth import init_oauth_client, oauth_page
from step_ingestor.client.src.security.user import get_user_from_session
from step_ingestor.client.src.security.decorators import login_required

from step_ingestor.services import IngestionService
from step_ingestor.analytics.step_toolbox import UserStepPlotter

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

app = init_app()

with app.app_context():
    init_oauth_client()
    app.service = service = IngestionService(os.environ["POLAR_CLIENT_ID"],
                                             os.environ["POLAR_CLIENT_SECRET"],
                                             os.environ["POLAR_CALLBACK_URL"])
    app.cipher = fernet.Fernet(app.secret_key.encode())

app.register_blueprint(oauth_page, urlprefix="/oauth")

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/dashboard/<freq>")
@login_required
def dashboard(freq):

    refresh_user_data()

    freqs = {"hour": "h", "day": "d", "week": "W",
             "month": "ME", "quarterly": "QE", "year": "YE"}

    if freq not in freqs:
        abort(404)
    else:
        freq = freqs.pop(freq)

    g.freqs = freqs

    # Fetch optional query params from request
    from_ = request.args.get("from", None)
    to = request.args.get("to", None)

    # Retrieve user data to make plot
    user = get_user_from_session()
    # TODO: This is authorization risk, use different key in database
    user_data = app.service.repo.get_user_steps(user["user_id"]) # TODO: Abstraction for repo in service layer

    # Create plot
    plotter = UserStepPlotter(user_data)
    g.plot = Markup(plotter.create_plot(freq, from_, to))

    return render_template("dashboard.html")

def refresh_user_data():
    user = get_user_from_session()
    if user:
        user_id = user.get("user_id")
        access_token_c = app.service.fetch_access_token(user_id)
        access_token = app.cipher.decrypt(access_token_c.encode()).decode()
        service.refresh_user_data(access_token, user_id)
        return True
    return False


if __name__ == "__main__":
    app.run(
        host=os.environ["CLIENT_HOST"],
        port=int(os.environ["CLIENT_PORT"])
    )
