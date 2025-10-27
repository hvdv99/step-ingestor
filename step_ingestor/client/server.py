# TODO:
# 1) refactor session handling so secrets never leave the server,
# 2) harden logout with POST/CSRF.

import os
from flask import render_template, g, abort
from markupsafe import Markup

from step_ingestor.client.src.service.service import session_factory
from step_ingestor.client.src.routes.oauth import init_oauth_client, oauth_page
from step_ingestor.client.src.security.init_app import init_app
from step_ingestor.client.src.security.user import get_user_from_session
from step_ingestor.client.src.security.decorators import login_required
from step_ingestor.client.src.service.service import get_service

from step_ingestor.services.analytics import UserStepPlotter

app = init_app()
with app.app_context():
    init_oauth_client()


@app.before_request
def create_session():
    """Adds a database session to the current request"""
    g.db = session_factory()

@app.teardown_request
def shutdown_session(exception=None):
    session = g.pop("db", None)
    if session is not None:
        if exception:
            session.rollback()
        else:
            session.commit()
        session.close()

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
    user_id = get_user_from_session().get("user_id")
    service = get_service()
    user = service.get_user(user_id=user_id)

    freqs = {"hour": "h",
             "day": "d",
             "week": "W",
             "month": "ME",
             "quarterly": "QE",
             "year": "YE"}

    if freq not in freqs:
        abort(404)
    else:
        freq = freqs.pop(freq)
    g.freqs = freqs

    # Retrieve user data to make plot
    user_data = service.get_user_data(user=user)

    # Create plot
    plotter = UserStepPlotter(user_data)
    g.plot = Markup(plotter.create_plot(freq))

    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(
        host=os.environ["CLIENT_HOST"],
        port=int(os.environ["CLIENT_PORT"])
    )