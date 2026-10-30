import os

from dotenv import load_dotenv
from flask import Flask

from . import db

load_dotenv()


def create_app(test_config=None):
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
    return app