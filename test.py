import os
from unittest import TestCase
from sqlalchemy import exc
from app import app

from models import db, connect_db, User

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///foodies_test'
app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True


app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    """Test user views"""

    def setUp(self):
        """Add sample user"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        user1 = User.signup(
            username="testuser",
            password="testpassword",
            email="test@test.com",
            image_url=None,
        )

        db.session.add(user1)
        db.session.commit()
    
    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_signup(self):
        """Test if user sign up"""

        with self.client as c:
            response = c.post("/signup",
                              data={"username": "testuser2",
                                    "password": "password",
                                    "email": "test2@test.com",
                                    "image_url": ""},
                              follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("testuser2", html)

    def test_signup_existing_user(self):
        """Test if user can sign up with existing username"""

        with self.client as c:
            response = c.post("/signup",
                              data={"username": "testuser",
                                    "password": "password",
                                    "email": "test2@test.com",
                                    "image_url": ""},
                              follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Username already taken", html)

    def test_login(self):
        """Test user log in"""

        with self.client as c:
            response = c.post("/login",
                              data={"username": "testuser",
                                    "password": "testpassword"},
                              follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Hello, testuser!", html)

    def test_login_invalid_credentials(self):
        """Test if user can't log in with invalid credentials"""

        with self.client as c:
            response = c.post("/login",
                              data={"username": "testuser",
                                    "password": "wrongpassword"},
                              follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Invalid credentials.", html)
