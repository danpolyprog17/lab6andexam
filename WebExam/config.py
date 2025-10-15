import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Force SQLite for local run
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(BASE_DIR, "uploads"),
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Pagination
    RECIPES_PER_PAGE = int(os.environ.get("RECIPES_PER_PAGE", 10))


config = Config()
