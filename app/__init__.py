from flask import Flask, redirect, url_for, request, session
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_blogging import SQLAStorage, BloggingEngine
from flask_login import LoginManager, current_user, login_user
from flask_migrate import Migrate
from flask_misaka import Misaka  # Markdown support
from flask_principal import Principal, UserNeed, RoleNeed, identity_loaded
from flask_sslify import SSLify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData

from config import config

engine = create_engine('sqlite:////tmp/blog.db')
meta = MetaData()
meta.create_all(bind=engine)
sql_storage = SQLAStorage(engine, metadata=meta)

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    SSLify(app)

    db.init_app(app)

    migrate = Migrate()
    migrate.init_app(app, db=db)

    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    principal = Principal()
    principal.init_app(app)

    blog_engine = BloggingEngine(app, sql_storage)

    misaka = Misaka(
        app=None,
        renderer=None,
        strikethrough=True,
        underline=True,
        tables=True,
        wrap=True
    )
    misaka.init_app(app)

    from app.models import User, Answer, Sentence, Language, Quiz, Score, Topic, Product, Purchase

    # TODO: Move these auth handlers out of __init__.py
    @login_manager.user_loader
    @blog_engine.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def handle_unauthorized():
        if session.get('_id'):
            return redirect(url_for('auth.login'))
        else:
            login_user(User().save())
            return redirect(request.url)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        identity.user = current_user

        if hasattr(current_user, "id"):
            identity.provides.add(UserNeed(current_user.id))

        # TODO: Fully implement roles
        # # Assuming the User model has a list of roles, update the
        # # identity with the roles that the user provides
        # if hasattr(current_user, 'roles'):
        #     for role in current_user.roles:
        #         identity.provides.add(RoleNeed(role.rolename))

        # Shortcut to the above: give admins "blogger" role.
        if hasattr(current_user, "is_admin"):
            if current_user.is_admin:
                identity.provides.add(RoleNeed("blogger"))

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

    from .misc import misc as misc_blueprint
    app.register_blueprint(misc_blueprint)

    class AuthenticatedAdminIndex(AdminIndexView):
        @expose('/')
        def index(self):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.is_admin:
                return redirect(url_for('dashboard.dashboard'))
            return super(AuthenticatedAdminIndex, self).index()

    # Initialise flask-admin
    admin = Admin(
        app,
        name='LudoLatin',
        template_mode='bootstrap3',
        base_template='admin_base.html',
        index_view=AuthenticatedAdminIndex()
    )

    class AuthenticatedModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

        def inaccessible_callback(self, name, **kwargs):
            # redirect to login page if user doesn't have access
            return redirect(url_for('auth.login', next=request.url))

        column_exclude_list = ('password_hash')

    # Add administrative views here
    admin.add_view(AuthenticatedModelView(User, db.session))
    admin.add_view(AuthenticatedModelView(Language, db.session))
    admin.add_view(AuthenticatedModelView(Topic, db.session, endpoint="admin_topic"))
    admin.add_view(AuthenticatedModelView(Quiz, db.session, endpoint="admin_quiz"))
    admin.add_view(AuthenticatedModelView(Sentence, db.session))
    admin.add_view(AuthenticatedModelView(Answer, db.session))
    admin.add_view(AuthenticatedModelView(Score, db.session))
    admin.add_view(AuthenticatedModelView(Product, db.session))
    admin.add_view(AuthenticatedModelView(Purchase, db.session))

    return app
