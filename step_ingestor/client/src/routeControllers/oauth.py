import os
import logging
import requests
from datetime import datetime
from flask import Blueprint, redirect, url_for, current_app, session, abort, g
from authlib.integrations.flask_client import OAuth

from step_ingestor.analytics import UserStepPlotter
from step_ingestor.client.src.config.appConfig import getAppConfig
from step_ingestor.client.src.security.user import create_user_session, clear_user_session, get_user_from_session

from step_ingestor.services import IngestionService

oauthPage = Blueprint('oauth',
                      __name__,
                      template_folder='templates')

oauth = None


def initOauthClient():
    global oauth
    appConfig = getAppConfig()
    oauth = OAuth(current_app)
    oauth.register(
        name='polar',
        client_id=os.environ["POLAR_CLIENT_ID"],
        client_secret=os.environ["POLAR_CLIENT_SECRET"],
        access_token_url=os.environ["POLAR_ACCESS_TOKEN_URL"],
        access_token_params={'grant_type': 'authorization_code'},
        authorize_url=os.environ["POLAR_AUTHORIZATION_URL"],
        api_base_url=os.environ["POLAR_API_URL"]
    )


service = IngestionService(os.environ["POLAR_CLIENT_ID"],
                           os.environ["POLAR_CLIENT_SECRET"])

@oauthPage.route("/login")
def login():
    # check if session already present
    if "user" in session:
        abort(404)
    redirect_uri = url_for(".callback", _external=True)
    return oauth.polar.authorize_redirect(redirect_uri)


@oauthPage.route("/oauth2_callback")
def callback():
    token_response = oauth.polar.authorize_access_token()
    logging.debug("Polar callback token response: {}".format(token_response)) #  {'access_token': '2135cf2b0985252253ba1e1e637cc208', 'token_type': 'bearer', 'expires_in': 315359999, 'x_user_id': 62846512, 'expires_at': 2074672954}

    acces_token = token_response["access_token"]
    user_id = str(token_response["x_user_id"])
    expires_at = datetime.fromtimestamp(token_response["expires_at"])

    # Create user in the database
    current_app.service.register_user(user_id)

    # Save access token in the database
    current_app.service.update_client_credentials(user_id, acces_token, expires_at)

    # Register the Polar user as a user of this client
    register_client_user(user_id)

    # Save user information in the session
    create_user_session(
        user_id=user_id,
        access_token=acces_token)

    return redirect("/")


@oauthPage.route("/logout")
def logout():
    clear_user_session()
    return redirect(url_for("index", _external=True))

def register_client_user(member_id):
    """Polar API requirement to register the user with this client application"""

    # Send post request to users endpoint
    resp = oauth.polar.post('users', json={"member-id": "polarclient" + member_id})

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        # Error 409 Conflict means that the user has already been registered for this client.
        if err.response.status_code != 409:
            raise err

    profile = resp.json()  # {'error': {'timestamp': '2025-10-01T10:39:27.987', 'status': 409, 'error_type': 'user_already_registered', 'message': 'User userid:62846512 with membertag abc123 has already registered with partner Huub van de Voort', 'corr_id': ''}}
    logging.debug("Polar Client user registration response: {}".format(profile))
