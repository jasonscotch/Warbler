"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

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
        uid1 = 1111
        self.testuser.id = uid1
        
        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test.com",
                                     password="testuser2",
                                     image_url=None)
        uid2 = 2222
        self.testuser2.id = uid2

        db.session.commit()
        
    def test_add_message(self):

        """Can user add a message?"""

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
    
    def test_delete_message(self):

        """Can user delete a message?"""
        msg = Message(
                    id=123,
                    text='Here is a test message I am posting.',
                    user_id=self.testuser.id
                    )
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/messages/123/delete', follow_redirects=True)
            
            msg1 = Message.query.get(123)
            user = User.query.get(self.testuser.id)
            
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(msg1, user.messages)

    def test_logged_out_add_message(self):
        """Are you prohibited from adding a message without logging in?"""
        resp1 = self.client.post('/messages/new', data={'text': "Testing"}, follow_redirects=True)
        
        self.assertEqual(resp1.status_code, 200)
        
        self.assertIn('Access unauthorized.', resp1.get_data(as_text=True))
    
    def test_logged_out_delete_message(self):
        """Can a logged out user delete a message?"""
        msg = Message(
                    id=123,
                    text='Here is a test message I am posting.',
                    user_id=self.testuser.id
                    )
        db.session.add(msg)
        db.session.commit()

        resp = self.client.post('/messages/123/delete', follow_redirects=True)
          
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Access unauthorized.', resp.get_data(as_text=True))
        
        m = Message.query.get(123)
        self.assertIsNotNone(m)

    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Testing 123"}, follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', resp.get_data(as_text=True))