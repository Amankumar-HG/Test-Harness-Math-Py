import os

from flask import Flask


QUIZ_LENGTH = 10
QUIZ_TIME_LIMIT = 60


def create_app(test_config=None):
    """Application factory for the Math Quiz web app."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        QUIZ_LENGTH=QUIZ_LENGTH,
        QUIZ_TIME_LIMIT=QUIZ_TIME_LIMIT,
    )
    if test_config is not None:
        app.config.update(test_config)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
