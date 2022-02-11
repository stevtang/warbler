"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
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

        self.user2.is_following(self.user1)
        self.user1.is_followed_by(self.user2)

        self.assertEqual(self.user2.is_following(self.user1), True)
        self.assertEqual(self.user2.is_following(self.user2), False)
        self.assertEqual(self.user1.is_following(self.user2), False)

    def test_is_followed_by(self):
        """Tests the is followed by db.relationship"""

        self.user2.following.append(self.user1)
        db.session.commit()

        self.assertEqual(self.user1.is_followed_by(self.user2), True)
        self.assertEqual(self.user1.is_followed_by(self.user1), False)
        self.assertEqual(self.user2.is_followed_by(self.user1), False)

    # Testing User Sign Up

    def test_signup(self):
        """ Tests if the signup method works with 
        valid inputs and fails eith ANY invalid
        input
        """

        user = User.signup(
            username="test_signup",
            email="test_@gmail.com",
            password=bcrypt.generate_password_hash("password3").decode('utf8'),
            image_url="someimg.org/test_pic",
        )

        db.session.commit()

        total_users = User.query.all()

        # Query all the users
        self.assertEqual(len(total_users), 3)
        self.assertEqual(user.username, "test_signup")
        self.assertEqual(user.email, "test_@gmail.com")
        self.assertEqual(user.image_url, "someimg.org/test_pic")
        self.assertTrue(user.password.startswith("$2b$"))

    def test_signup_fail(self):
        """ Tests the signup method's uniqueness and nonnullable
        fields
        """

        with self.assertRaises(Exception) as context:

            fail_user = User.signup(
                # username not unique
                username="test1_username",
                email="test3_email",
                password="1234567890",
                image_url="someimg.org/test_pic",
            )

        self.assertTrue(Exception in context.exception)

    # Testing Authentication

    def test_valid_authentication(self):
        user1 = User.authenticate(self.user1.username, "password1")
        self.assertIsNotNone(user1)
        self.assertEqual(user1.id, self.user1.id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password1"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user1.username, "badpassword"))
