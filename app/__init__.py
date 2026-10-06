import os
from pathlib import Path

from flask import Flask

from app.store import LearnerStore


SESSION_LENGTH = 8


def create_app(test_config=None):
    """Application factory for the Adaptive Problem Engine."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    base_dir = Path(app.root_path).parent
    default_db = base_dir / "data" / "ape.sqlite3"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SESSION_LENGTH=SESSION_LENGTH,
        DATABASE=os.environ.get("APE_DATABASE", str(default_db)),
    )
    if test_config is not None:
        app.config.update(test_config)

    db_path = Path(app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    app.extensions["store"] = LearnerStore(db_path)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
