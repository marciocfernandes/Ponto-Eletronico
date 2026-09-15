from flask_login import UserMixin

from app import db


class Usuario(UserMixin, db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    perfil = db.Column(
        db.String(20),
        nullable=False,
        default="FUNCIONARIO"
    )

    ativo = db.Column(
        db.Boolean,
        default=True
    )