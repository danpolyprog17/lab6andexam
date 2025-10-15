from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Recipe, Review
from ..util import sanitize_markdown_text
from . import bp


@bp.route("/create/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def create(recipe_id: int):
    recipe = Recipe.query.get_or_404(recipe_id)

    existing = Review.query.filter_by(recipe_id=recipe.id, user_id=current_user.id).first()
    if existing:
        flash("Вы уже оставили отзыв на этот рецепт", "info")
        return redirect(url_for("recipes.view", recipe_id=recipe.id))

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", 5))
            text_md = sanitize_markdown_text(request.form.get("text_md", ""))
            review = Review(recipe_id=recipe.id, user_id=current_user.id, rating=rating, text_md=text_md)
            db.session.add(review)
            db.session.commit()
            return redirect(url_for("recipes.view", recipe_id=recipe.id))
        except Exception:
            db.session.rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
    return render_template("reviews/form.html", recipe=recipe)
