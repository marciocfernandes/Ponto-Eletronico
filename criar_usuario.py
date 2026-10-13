from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario


app = create_app()


with app.app_context():

    email = "teste@teste.com.br"

    usuario_existente = Usuario.query.filter_by(
        email=email
    ).first()

    if usuario_existente:

        print("Usuário já existe.")

    else:

        usuario = Usuario(
            nome="Administrador",
            email=email,
            senha=generate_password_hash("123456"),
            perfil="ADMIN",
            ativo=True
        )

        db.session.add(usuario)

        db.session.commit()

        print("Usuário criado com sucesso!")