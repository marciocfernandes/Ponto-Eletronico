from functools import wraps
from flask import abort
from flask_login import current_user, login_required


def admin_required(func):
    @wraps(func)
    @login_required
    def decorated_view(*args, **kwargs):
        if current_user.perfil != "ADMIN":
            abort(403)

        return func(*args, **kwargs)

    return decorated_view