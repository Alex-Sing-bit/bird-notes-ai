import os

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient

from config import GOOGLE_CLIENT_ID

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from app import views
    app.register_blueprint(views.bp)

    with app.app_context():
        from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.get(user_id)

    return app