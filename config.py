
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]

    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    TESTING = True

    SQLALCHEMY_DATABASE_URI = os.environ["TEST_DATABASE_URL"]

    WTF_CSRF_ENABLED = True
