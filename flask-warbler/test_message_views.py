"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

        self.testuser_id = self.testuser.id

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def add_message(self):
        u1 = User.query.get(self.testuser_id)
        msg = Message(text="TEST TEXT FOR TESTING")
        u1.messages.append(msg)
        db.session.commit()
        return msg.id

    def test_messages_add(self):
        """ Testing logged in User can post message """
        u1 = User.query.get(self.testuser_id)
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = client.post(f"/messages/new",
                               data={"text": "test text"},
                               follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertIn(f"{u1.username}", html)
            self.assertIn("test text", html)
            self.assertEqual(resp.status_code, 200)

    def test_messages_destroy(self):
        """ Testing logged-in user deleting own messages"""
        msg_id = self.add_message()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = client.post(f"/messages/{msg_id}/delete")

            user1 = User.query.get(self.testuser_id)
            msg = Message.query.get(msg_id)

            self.assertEqual(len(user1.messages), 0)
            self.assertEqual(msg, None)
            self.assertEqual(resp.status_code, 302)
