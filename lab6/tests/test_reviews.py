import pytest
from flask import Flask
from app import create_app
from app.models import db, User, Course, Category, Review
from app.repositories import ReviewRepository

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    with app.app_context():
        user = User(first_name='Test', last_name='User', login='testuser')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def category(app):
    with app.app_context():
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        return category

@pytest.fixture
def course(app, user, category):
    with app.app_context():
        course = Course(
            name='Test Course',
            short_desc='Short description',
            full_desc='Full description',
            author_id=user.id,
            category_id=category.id
        )
        db.session.add(course)
        db.session.commit()
        return course

class TestReviewModel:
    def test_review_creation(self, app, user, course):
        with app.app_context():
            review = Review(
                rating=5,
                text='Great course!',
                user_id=user.id,
                course_id=course.id
            )
            db.session.add(review)
            db.session.commit()
            
            assert review.id is not None
            assert review.rating == 5
            assert review.text == 'Great course!'
            assert review.user_id == user.id
            assert review.course_id == course.id

class TestReviewRepository:
    def test_add_review(self, app, user, course):
        with app.app_context():
            review_repo = ReviewRepository(db)
            review = review_repo.add_review(
                user_id=user.id,
                course_id=course.id,
                rating=5,
                text='Great course!'
            )
            
            assert review.id is not None
            assert review.rating == 5
            assert review.text == 'Great course!'

class TestReviewRoutes:
    def test_create_review(self, client, user, course):
        # Login
        client.post('/auth/login', data={
            'login': 'testuser',
            'password': 'password'
        })
        
        # Create review
        response = client.post(f'/courses/{course.id}/reviews/create', data={
            'rating': '5',
            'text': 'Great course!'
        })
        
        assert response.status_code == 302  # Redirect
