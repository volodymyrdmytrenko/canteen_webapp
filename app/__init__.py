from flask import Flask

from .config import Config
from .db import close_db
from .routes.auth import auth_bp
from .routes.employees import employees_bp
from .routes.main import main_bp
from .routes.reports import reports_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(reports_bp)

    return app
