import os
from datetime import timedelta
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix


def init_app():
    app = Flask(__name__, template_folder="../../templates")

    app.config.update(
        DEBUG=False,
        SECRET_KEY=os.environ["FLASK_SECRET_KEY"],
        SESSION_COOKIE_SECURE=True,    # Session cookies can only be sent over HTTPS
        SESSION_COOKIE_HTTPONLY=True,  # Session cookies can only be read with HTML and not with JavaScript
        SESSION_COOKIE_SAMESITE="Lax", # How cookies are send with requests from external sites
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2) # Session expires after 2 hours
    )

    # See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For
    # App is behind one proxy that sets the -For and -Host headers.
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_host=1
    )

    return app
