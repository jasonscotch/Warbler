"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Likes

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


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        user1 = User.signup("test1", "test1@email.com", "password", None)
        uid1 = 1111
        user1.id = uid1

        user2 = User.signup("test2", "test2@email.com", "password", None)
        uid2 = 2222
        user2.id = uid2
        
        db.session.add_all([user1, user2])
        db.session.commit()
        
        user1 = User.query.get(uid1)
        user2 = User.query.get(uid2)

        self.user1 = user1
        self.uid1 = uid1

        self.user2 = user2
        self.uid2 = uid2
        
        msg1 = Message(text="Testing 1", user_id=self.uid1)
        msg2 = Message(text="Chillin like a villian", user_id=self.uid2)
        msg3 = Message(id=123, text="let sleeping dogs lie", user_id=self.uid1)

        db.session.add_all([msg1, msg2, msg3])
        db.session.commit()
            
        self.msg1 = msg1
        self.msg2 = msg2
        self.msg3 = msg3
        
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_logged_in_follow_pages(self):
        """Can you see the follower/following pages if logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp1 = c.get(f'/users/{self.uid1}/following')
            resp2 = c.get(f'/users/{self.uid1}/followers')
            resp3 = c.get('/users/2222/following')
            
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp2.status_code, 200)
            self.assertEqual(resp3.status_code, 200)

    def test_logged_out_follow_pages(self):
        """Can you not see the follower/following pages if logged out"""
        resp1 = self.client.get(f'/users/{self.uid1}/following')
        resp2 = self.client.get(f'/users/{self.uid1}/followers')
        resp3 = self.client.get('/users/2222/following')
            
        self.assertEqual(resp1.status_code, 302)
        self.assertEqual(resp2.status_code, 302)
        self.assertEqual(resp3.status_code, 302)
        
    def test_add_like(self):
        msg = Message(id=234, text="Happy Hour", user_id=self.uid2)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1

            resp = c.post("/users/add_like/234", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==234).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.uid1)
  
    def test_remove_like(self):
        msg = Message.query.get(123)
        self.assertIsNotNone(msg)
        self.assertNotEqual(msg.user_id, self.uid2)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid2

            resp = c.post("/users/add_like/123", follow_redirects=True)
            # self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == msg.id).all()
            # The like has been added
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.uid2)

            resp = c.post("/users/add_like/123", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == msg.id).all()
            # The like has been removed
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        m = Message.query.get(123)
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/users/add_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())