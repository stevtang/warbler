"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

from flask_bcrypt import Bcrypt

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# added:
# imported bcrypt 
# set some test user data for two users

bcrypt = Bcrypt()

USER1_DATA = {
    "email": "test1_email",
    "username": "test1_username",
    "password": bcrypt.generate_password_hash("password1").decode('utf8'),
}

USER2_DATA = {
    "email": "test2_email",
    "username": "test2_username",
    "password": bcrypt.generate_password_hash("password2").decode('utf8'),
}

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
        user1 = User(**USER1_DATA)
        user2 = User(**USER2_DATA)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        self.user1 = user1
        self.user2 = user2

    # added teardown
    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        
    def test_is_following(self):
        """Does is_following successfully detect 
        when user1 is following user2?
        """

        follows = Follows(
            user_being_followed_id=self.user1.id, 
            user_following_id=self.user2.id)

        db.session.add(follows)
        db.session.commit()

        users_following = [u.id for u in self.user1.following]

        self.assertIn(self.user2.id, users_following)