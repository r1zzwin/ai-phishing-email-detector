import os

from dotenv import load_dotenv
from flask import Flask, render_template

from . import db
from .logging_setup import setup_logging

load_dotenv()

CSP = (
    "default-src 'self'; style-src 'self'; script-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


def create_app(test_config=None):
    setup_logging()

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "scans.db")
    if test_config:
        app.config.update(test_config)

    db.init_db(app.config["DATABASE"])

    from .routes import bp
    app.register_blueprint(bp)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = CSP
        return response

    def show_error(error):
        messages = {
            404: ("Page not found", "That page does not exist."),
            413: ("Request too large",
                  "The data you sent was too large. Shorten the email text and try again."),
        }
        title, message = messages.get(
            error.code,
            ("Something went wrong", "An unexpected error happened. Please try again."),
        )
        return render_template("error.html", title=title, message=message), error.code

    for code in (404, 413, 500):
        app.register_error_handler(code, show_error)

    return app