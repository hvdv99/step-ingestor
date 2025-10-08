import os
import requests
from datetime import datetime
from flask import Blueprint, redirect, url_for, current_app, session, abort
from authlib.integrations.flask_client import OAuth

from step_ingestor.client.src.security.user import create_user_session, clear_user_session

oauth = None

def init_oauth_client():
    """Setup authlib with flask application"""
    global oauth
    oauth = OAuth()
    oauth.init_app(current_app)
    oauth.register(
        name='polar',
        client_id=os.environ["POLAR_CLIENT_ID"],
        client_secret=os.environ["POLAR_CLIENT_SECRET"],
        access_token_url=os.environ["POLAR_ACCESS_TOKEN_URL"],
        access_token_params={'grant_type': 'authorization_code'},
        authorize_url=os.environ["POLAR_AUTHORIZATION_URL"],
        api_base_url=os.environ["POLAR_API_URL"] + "/" # Quick fix
    )
    return oauth

oauth_page = Blueprint('oauth', __name__, template_folder='templates') # OAuth as blueprint

@oauth_page.route("/login")
def login():
    """Login view"""

    # check if user session cookie is already present
    if "user" in session:
        abort(404)

    # Redirect user to external OAuth provider
    redirect_uri = url_for(".callback", _external=True)
    return oauth.polar.authorize_redirect(redirect_uri)

@oauth_page.route("/oauth2_callback")
def callback():
    """Retrieve access token after callback and store"""
    token_response = oauth.polar.authorize_access_token()
    access_token = token_response["access_token"]
    acces_token_c = current_app.cipher.encrypt(access_token.encode()).decode()
    user_id = str(token_response["x_user_id"])
    expires_at = datetime.fromtimestamp(token_response["expires_at"])

    # Create user in the external database
    current_app.service.register_user(user_id)

    # Save encrypted access token in the database
    current_app.service.update_client_credentials(user_id, acces_token_c, expires_at)

    # Register the Polar user as a user of this client
    register_client_user(user_id)

    # Save user information in the session
    create_user_session(user_id=user_id)

    return redirect("/")

@oauth_page.route("/logout")
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
