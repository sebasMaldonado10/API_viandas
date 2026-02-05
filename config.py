import os
from datetime import timedelta

class Config:
    # configuracion general

    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost/viandas")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    JSON_AS_ASCII = False
    PROPAGATE_EXCEPTIONS = True



    