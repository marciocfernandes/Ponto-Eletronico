
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    # Registrar blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.admin import admin
    from app.routes.api import api

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(api)

    # Importar modelos
    from app.models import Usuario, RegistroPonto

    # Carregar usuário autenticado
    @login_manager.user_loader
    def load_user(user_id):
        try:
            usuario = db.session.get(Usuario, int(user_id))
        except (ValueError, TypeError):
            return None

        if usuario is None or not usuario.ativo:
            return None

        return usuario

    # Inicializar banco de dados
    with app.app_context():
        db.create_all()

    # Retornar a aplicação Flask
    return app
