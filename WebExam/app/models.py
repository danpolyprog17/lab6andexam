from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from .extensions import db, login_manager


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(128), nullable=False)
    middle_name = db.Column(db.String(128))

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    role = db.relationship("Role", backref=db.backref("users", lazy=True))

    recipes = db.relationship("Recipe", back_populates="author", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role and self.role.name == "admin"

    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name or ""]
        return " ".join([p for p in parts if p]).strip()


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description_md = db.Column(db.Text, nullable=False)
    ingredients_md = db.Column(db.Text, nullable=False)
    steps_md = db.Column(db.Text, nullable=False)
    cook_time_min = db.Column(db.Integer, nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author = db.relationship("User", back_populates="recipes")

    images = db.relationship(
        "RecipeImage",
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )
    reviews = db.relationship(
        "Review",
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )

    @validates("cook_time_min", "servings")
    def validate_positive(self, key, value):
        assert value is not None and int(value) >= 0
        return int(value)


class RecipeImage(db.Model):
    __tablename__ = "recipe_images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(127), nullable=False)

    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipe = db.relationship("Recipe", back_populates="images")


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("recipe_id", "user_id", name="uq_review_recipe_user"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_rating_range"),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    text_md = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    recipe = db.relationship("Recipe", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")
