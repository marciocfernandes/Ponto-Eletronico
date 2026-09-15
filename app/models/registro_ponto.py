from datetime import datetime

from app import db


class RegistroPonto(db.Model):

    __tablename__ = "registros_ponto"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    data_hora = db.Column(
        db.DateTime,
        default=datetime.now,
        nullable=False
    )

    tipo = db.Column(
        db.String(30),
        nullable=False
    )

    usuario = db.relationship(
        "Usuario",
        backref="registros"
    )