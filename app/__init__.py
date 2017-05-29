from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()
migrate = Migrate()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db=db)
    login_manager.init_app(app)

    from .quiz import quiz as quiz_blueprint
    app.register_blueprint(quiz_blueprint)

    from .dashboard import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)

    from .topic import topic as topic_blueprint
    app.register_blueprint(topic_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from .utils import utils as utils_blueprint
    app.register_blueprint(utils_blueprint)

    from .store import store as store_blueprint
    app.register_blueprint(store_blueprint)

    # Initialise flask-admin
    from app.models import User, Answer, Sentence, Language, Quiz, Score, Topic, Product, Purchase
    admin = Admin(app, name='ludolatin', template_mode='bootstrap3')

    # Add administrative views here
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Language, db.session))
    admin.add_view(ModelView(Topic, db.session, endpoint="admin_topic"))
    admin.add_view(ModelView(Quiz, db.session, endpoint="admin_quiz"))
    admin.add_view(ModelView(Sentence, db.session))
    admin.add_view(ModelView(Answer, db.session))
    admin.add_view(ModelView(Score, db.session))
    admin.add_view(ModelView(Product, db.session))
    admin.add_view(ModelView(Purchase, db.session))

    return app
