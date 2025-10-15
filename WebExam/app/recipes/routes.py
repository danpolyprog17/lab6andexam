import os
from typing import List
from flask import render_template, request, redirect, url_for, flash, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Recipe, RecipeImage, Review
from ..util import sanitize_markdown_text, render_markdown_to_html
from . import bp


@bp.app_template_filter("markdown")
def markdown_filter(text: str) -> str:
    return render_markdown_to_html(text)


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Recipe.query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=current_app.config["RECIPES_PER_PAGE"], error_out=False
    )
    recipes = pagination.items

    # Preload aggregates: avg rating and count reviews
    recipe_ids = [r.id for r in recipes]
    reviews_by_recipe = {
        rid: {"count": 0, "sum": 0} for rid in recipe_ids
    }
    if recipe_ids:
        rows = (
            db.session.query(Review.recipe_id, db.func.count(Review.id), db.func.coalesce(db.func.sum(Review.rating), 0))
            .filter(Review.recipe_id.in_(recipe_ids))
            .group_by(Review.recipe_id)
            .all()
        )
        for rid, cnt, total in rows:
            reviews_by_recipe[rid] = {"count": int(cnt), "sum": int(total)}

    return render_template("recipes/index.html", pagination=pagination, recipes=recipes, reviews_agg=reviews_by_recipe)


@bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


def _can_modify(recipe: Recipe) -> bool:
    return current_user.is_authenticated and (current_user.is_admin or recipe.author_id == current_user.id)


@bp.route("/recipes/<int:recipe_id>")
def view(recipe_id: int):
    recipe = Recipe.query.get_or_404(recipe_id)

    # Compute average rating and count
    stats = (
        db.session.query(db.func.count(Review.id), db.func.coalesce(db.func.avg(Review.rating), 0.0))
        .filter(Review.recipe_id == recipe.id)
        .first()
    )
    reviews_count = int(stats[0]) if stats else 0
    avg_rating = float(stats[1]) if stats else 0.0

    existing_user_review = None
    if current_user.is_authenticated:
        existing_user_review = Review.query.filter_by(recipe_id=recipe.id, user_id=current_user.id).first()

    return render_template(
        "recipes/view.html",
        recipe=recipe,
        can_modify=_can_modify(recipe),
        reviews_count=reviews_count,
        avg_rating=avg_rating,
        existing_user_review=existing_user_review,
    )


@bp.route("/recipes/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description_md = sanitize_markdown_text(request.form.get("description_md", ""))
            ingredients_md = sanitize_markdown_text(request.form.get("ingredients_md", ""))
            steps_md = sanitize_markdown_text(request.form.get("steps_md", ""))
            cook_time_min = int(request.form.get("cook_time_min", 0))
            servings = int(request.form.get("servings", 0))

            recipe = Recipe(
                title=title,
                description_md=description_md,
                ingredients_md=ingredients_md,
                steps_md=steps_md,
                cook_time_min=cook_time_min,
                servings=servings,
                author_id=current_user.id,
            )
            db.session.add(recipe)
            db.session.flush()  # Get recipe.id before committing

            # Handle multiple images
            files = request.files.getlist("images")
            for f in files:
                if not f or not f.filename:
                    continue
                filename = secure_filename(f.filename)
                stored_name = f"{recipe.id}_{filename}"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
                f.save(save_path)
                db.session.add(
                    RecipeImage(filename=stored_name, mime_type=f.mimetype, recipe_id=recipe.id)
                )

            db.session.commit()
            return redirect(url_for("recipes.view", recipe_id=recipe.id))
        except Exception:
            db.session.rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
    return render_template("recipes/form.html", mode="create", recipe=None)


@bp.route("/recipes/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
def edit(recipe_id: int):
    recipe = Recipe.query.get_or_404(recipe_id)
    if not _can_modify(recipe):
        flash("У вас недостаточно прав для выполнения данного действия", "warning")
        return redirect(url_for("recipes.index"))
    if request.method == "POST":
        try:
            recipe.title = request.form.get("title", "").strip()
            recipe.description_md = sanitize_markdown_text(request.form.get("description_md", ""))
            recipe.ingredients_md = sanitize_markdown_text(request.form.get("ingredients_md", ""))
            recipe.steps_md = sanitize_markdown_text(request.form.get("steps_md", ""))
            recipe.cook_time_min = int(request.form.get("cook_time_min", 0))
            recipe.servings = int(request.form.get("servings", 0))
            db.session.commit()
            return redirect(url_for("recipes.view", recipe_id=recipe.id))
        except Exception:
            db.session.rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
    return render_template("recipes/form.html", mode="edit", recipe=recipe)


@bp.route("/recipes/<int:recipe_id>/delete", methods=["POST"]) 
@login_required
def delete(recipe_id: int):
    recipe = Recipe.query.get_or_404(recipe_id)
    if not _can_modify(recipe):
        flash("У вас недостаточно прав для выполнения данного действия", "warning")
        return redirect(url_for("recipes.index"))

    try:
        # Collect image files to delete after commit
        image_paths: List[str] = [
            os.path.join(current_app.config["UPLOAD_FOLDER"], img.filename) for img in recipe.images
        ]
        db.session.delete(recipe)
        db.session.commit()
        # Remove files from filesystem
        for p in image_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        flash("Рецепт успешно удалён", "success")
    except Exception:
        db.session.rollback()
        flash("Ошибка удаления рецепта", "danger")
    return redirect(url_for("recipes.index"))
