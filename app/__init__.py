import os
from flask import Flask
from .config import DevConfig, ProdConfig
from .extensions import db, login_manager, migrate, csrf
from .auth import auth_bp
from .main import main_bp
from .admin import admin_bp
from .cli import register_cli


def create_app():
    app = Flask(__name__)

    # Flask 3+ nu mai are app.env, deci folosim env vars
    is_production = (
        os.getenv("RENDER") is not None
        or os.getenv("FLASK_ENV") == "production"
        or os.getenv("ENV") == "production"
    )

    if is_production:
        app.config.from_object(ProdConfig)
    else:
        app.config.from_object(DevConfig)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    register_cli(app)
    return app
