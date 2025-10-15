from app.models import Review, Course
from sqlalchemy import desc, asc

class ReviewRepository:
    def __init__(self, db):
        self.db = db

    def get_reviews_by_course(self, course_id, sort_by='newest', page=1, per_page=10):
        """Получить отзывы для курса с пагинацией и сортировкой"""
        query = self.db.select(Review).filter(Review.course_id == course_id)
        
        # Применяем сортировку
        if sort_by == 'positive':
            query = query.order_by(desc(Review.rating), desc(Review.created_at))
        elif sort_by == 'negative':
            query = query.order_by(asc(Review.rating), desc(Review.created_at))
        else:  # newest (по умолчанию)
            query = query.order_by(desc(Review.created_at))
        
        return self.db.paginate(query, page=page, per_page=per_page)

    def get_recent_reviews_by_course(self, course_id, limit=5):
        """Получить последние отзывы для курса"""
        query = self.db.select(Review).filter(Review.course_id == course_id).order_by(desc(Review.created_at)).limit(limit)
        return self.db.session.execute(query).scalars().all()

    def get_user_review_for_course(self, user_id, course_id):
        """Получить отзыв пользователя для конкретного курса"""
        return self.db.session.execute(
            self.db.select(Review).filter(
                Review.user_id == user_id,
                Review.course_id == course_id
            )
        ).scalar_one_or_none()

    def add_review(self, user_id, course_id, rating, text):
        """Добавить новый отзыв"""
        review = Review(
            user_id=user_id,
            course_id=course_id,
            rating=rating,
            text=text
        )
        
        try:
            self.db.session.add(review)
            self.db.session.commit()
            return review
        except Exception as e:
            self.db.session.rollback()
            raise e

    def update_course_rating(self, course_id):
        """Обновить рейтинг курса на основе отзывов"""
        course = self.db.session.get(Course, course_id)
        if course:
            # Получаем сумму и количество оценок
            result = self.db.session.execute(
                self.db.select(
                    self.db.func.sum(Review.rating).label('rating_sum'),
                    self.db.func.count(Review.id).label('rating_num')
                ).filter(Review.course_id == course_id)
            ).first()
            
            if result:
                course.rating_sum = result.rating_sum or 0
                course.rating_num = result.rating_num or 0
                self.db.session.commit()
