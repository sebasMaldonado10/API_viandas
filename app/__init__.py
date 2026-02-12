from flask import Flask
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

# xtensiones de Flask
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    # Crear la aplicacion Flask
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    #importar modelos para que SQLAlchemy los reconozca
    from . import models
    
    from .routes import register_routes
    register_routes(app)
    
    return app