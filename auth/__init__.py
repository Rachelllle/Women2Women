"""Auth package — shared login manager, User model, and user loader.

`login_manager` is created here without an app, then bound in app.py via
`login_manager.init_app(app)`. The routes live in auth/routes.py.
"""
from flask import jsonify
from flask_login import LoginManager, UserMixin
from database.db import db_query

login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, id, email):
        self.id    = id
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    row = db_query("SELECT id, email FROM users WHERE id = %s", (user_id,), one=True)
    return User(row["id"], row["email"]) if row else None


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Login required"}), 401
