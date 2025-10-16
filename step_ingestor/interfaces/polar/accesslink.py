from . import endpoints
from .oauth2 import OAuth2Client


class AccessLink(object):
    """Wrapper class for Polar Open AccessLink API v3"""

    def __init__(self, api_url, auth_url, token_url, client_id, client_secret, redirect_url=None):
        if not client_id or not client_secret:
            raise ValueError("Client id and secret must be provided.")

        self.oauth = OAuth2Client(api_url=api_url,
                                  authorization_url=auth_url,
                                  access_token_url=token_url,
                                  client_id=client_id,
                                  client_secret=client_secret,
                                  redirect_url=redirect_url)

        self.users = endpoints.Users(oauth=self.oauth)
        self.daily_activity_beta = endpoints.DailyActivityBeta(oauth=self.oauth)

    @property
    def authorization_url(self):
        """Get the authorization url for the client"""
        return self.oauth.get_authorization_url()

    def get_access_token(self, authorization_code):
        """Request access token for a user.
        :param authorization_code: authorization code received from authorization endpoint.
        """
        return self.oauth.get_access_token(authorization_code)

    def get_activity_day(self,
                         access_token,
                         day,
                         steps=False,
                         activity_zones=False,
                         inactivity_stamps=False):
        return self.daily_activity_beta.fetch(access_token, day,
                                              steps=steps,
                                              activity_zones=activity_zones,
                                              inactivity_stamps=inactivity_stamps)

    def get_activity_date_range(self,
                                access_token,
                                date_from,
                                date_to=None,
                                steps=False,
                                activity_zones=False,
                                inactivity_stamps=False):
        return self.daily_activity_beta.fetch(access_token=access_token,
                                              from_=date_from,
                                              to=date_to,
                                              steps=steps,
                                              activity_zones=activity_zones,
                                              inactivity_stamps=inactivity_stamps)
