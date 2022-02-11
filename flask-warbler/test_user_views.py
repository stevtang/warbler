# run these tests like:
#
#    python -m unittest test_user_views.py


from app import app

from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows
from flask import g, session

from flask_bcrypt import Bcrypt

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler_test"

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
CURR_USER_KEY = "curr_user"


class UserViewFunctionTestCase(TestCase):

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

        self.user1_id = user1.id
        self.user2_id = user2.id

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_show_following(self):
        """ Testing login function."""
        # u1 = User.query.get(self.user1_id)
        # u2 = User.query.get(self.user2_id)
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = client.get(f"/users/{self.user2_id}/following")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("TEST FOLLOWING DO NOT DELETE", html)

    def test_invalid_show_following(self):
        """ Testing access from user not logged in"""
        
        with self.client as client:
            resp = client.get(f"/users/{self.user2_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_show_followers(self):
        """ Testing login function."""
        # u1 = User.query.get(self.user1_id)
        # u2 = User.query.get(self.user2_id)
        
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = client.get(f"/users/{self.user2_id}/followers")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("TEST FOLLOWERS COMMENT DO NOT DELETE", html)

    def test_invalid_show_followers(self):
        """ Testing access from user not logged in"""
        
        with self.client as client:
            resp = client.get(f"/users/{self.user2_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_messages_add(self):
        """ Testing logged in User can post message """
        u1 = User.query.get(self.user1_id)
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            resp = client.post(
                    f"/messages/new",
                    data={
                        "text": "test text"
                    }, follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn(f"{u1.username}", html)
            self.assertIn("test text", html)
            self.assertEqual(resp.status_code, 200)
