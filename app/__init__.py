from flask import Flask


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # reject huge requests

    from .routes import bp
    app.register_blueprint(bp)
    return app