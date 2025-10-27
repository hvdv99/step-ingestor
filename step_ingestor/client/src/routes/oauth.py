import os
import uuid
import requests
from datetime import datetime
from flask import Blueprint, redirect, url_for, current_app, session, abort
from authlib.integrations.flask_client import OAuth

from step_ingestor.client.src.security.user import create_user_session, clear_user_session
from step_ingestor.client.src.service.service import get_service
from step_ingestor.dto import UserDTO, TokenDTO

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

    polar_user_id = str(token_response["x_user_id"])

    access_token = token_response["access_token"]
    expires_at = datetime.fromtimestamp(token_response["expires_at"])
    token_obj = TokenDTO(access_token=access_token, issuer="polar", issued_at=datetime.now(), expires_at=expires_at)

    service = get_service()
    # Check if user is already registered
    user = service.get_user(polar_user_id=polar_user_id)
    if user:  # Yes -> update access token
        user.access_token = token_obj
        service.update_access_token(user=user)
    else:  # No -> register and store
        user = UserDTO(user_id=uuid.uuid4().hex,
                       polar_user_id=polar_user_id,
                       access_token=token_obj,
                       created_at=datetime.now(),
                       updated_at=datetime.now())
        service.add_user(user=user)

        # Register the Polar user as a user of this client
        register_client_user(user.user_id)

    # Save user information in the session
    create_user_session(user_id=user.user_id)

    # Update latest user data
    service.refresh_user_data(user=user)

    return redirect("/")

@oauth_page.route("/logout")
def logout():
    clear_user_session()
    return redirect(url_for("index", _external=True))

def register_client_user(user_id):
    """Polar API requirement to register the user with this client application"""

    # Send post request to users endpoint
    resp = oauth.polar.post('users', json={"member-id": "polarclient-" + user_id})

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        # Error 409 Conflict means that the user has already been registered for this client.
        if err.response.status_code != 409:
            raise err
