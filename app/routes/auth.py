from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash

from app.models.usuario import Usuario


auth = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):

            if not usuario.ativo:
                flash("Usuário desativado.")
                return redirect(url_for("auth.login"))

            login_user(usuario)

            return redirect(url_for("main.home"))

        flash("E-mail ou senha inválidos.")

    return render_template("login.html")


@auth.route("/logout")
def logout():

    logout_user()

    return redirect(url_for("auth.login"))