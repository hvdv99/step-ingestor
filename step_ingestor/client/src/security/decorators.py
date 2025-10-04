import functools
from flask import redirect, url_for, request

from step_ingestor.client.src.security.user import get_user_from_session


def login_required(_func=None):
    def decorator_login_required(func):
        """Make sure user is logged in before proceeding"""
        @functools.wraps(func)
        def wrapper_login_required(*args, **kwargs):
            user = get_user_from_session()
            if user is None:
                return redirect(url_for("oauth.login", next=request.url))

            return func(*args, **kwargs)
        return wrapper_login_required

    if _func is None:
        return decorator_login_required
    else:
        return decorator_login_required(_func)
