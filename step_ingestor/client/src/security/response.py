from flask import make_response


def make_response_secure(*args):
    resp = make_response(*args)
    resp.headers["Strict-Transport-Security"] = "max-age=3600; includeSubDomains" # Force browser to use HTTPS

    # Set CSRF when using forms
    # resp.headers["Content-Security-Policy"] = ""

    # Force browser to respect MIME types in the Content-Type header
    resp.headers["X-Content-Type-Options"] = "nosniff"

    # Forbid the use of the client app to be embedded in other apps
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
