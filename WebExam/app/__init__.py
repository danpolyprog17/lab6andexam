import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .models import Role, User
import click


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"

    # Blueprints
    from .auth import bp as auth_bp
    from .recipes import bp as recipes_bp
    from .reviews import bp as reviews_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(reviews_bp)

    # Simple CLI to create default roles
    @app.cli.command("init-roles")
    def init_roles():
        with app.app_context():
            for name, description in (
                ("admin", "Администратор"),
                ("user", "Пользователь"),
            ):
                if not Role.query.filter_by(name=name).first():
                    db.session.add(Role(name=name, description=description))
            db.session.commit()
            print("Roles ensured: admin, user")

    @app.cli.command("create-user")
    @click.argument("username")
    @click.argument("password")
    @click.option("--last-name", required=True)
    @click.option("--first-name", required=True)
    @click.option("--middle-name", default="")
    @click.option("--role", type=click.Choice(["admin", "user"]), default="user")
    def create_user(username, password, last_name, first_name, middle_name, role):
        with app.app_context():
            if User.query.filter_by(username=username).first():
                print("User already exists")
                return
            role_obj = Role.query.filter_by(name=role).first()
            if not role_obj:
                print("Role not found; run 'flask init-roles' first")
                return
            user = User(
                username=username,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                role=role_obj,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"User '{username}' created with role '{role}'")

    return app
