"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

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

        db.session.commit()

        user1 = User.query.get(uid1)
        user2 = User.query.get(uid2)

        self.user1 = user1
        self.uid1 = uid1

        self.user2 = user2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(user)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(user.messages), 0)
        self.assertEqual(len(user.followers), 0)
         
    def test_followers(self):
        """Tests the following functions"""
        self.user1.following.append(self.user2)
        db.session.commit()

        # Test after following
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertTrue(self.user2.is_followed_by(self.user1))
        
        # Make user1 unfollow user2
        self.user1.following.remove(self.user2)
        db.session.commit()

        # Test after unfollowing
        self.assertFalse(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))
        
    def test_dup_username(self):
        """Tests the signup username function"""
        bad_user = User.signup(
            'test1',
            'test@email.com',
            'testing',
            None
        )
        
        uid = 3333
        bad_user.id = uid
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_dup_email(self):
        """Tests the signup email function"""
        bad_user = User.signup(
            'test',
            'test1@email.com',
            'testing',
            None
        )
        
        uid = 4444
        bad_user.id = uid
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
            
    def test_no_password(self):
        """Tests the lack of password function"""
        with self.assertRaises(ValueError) as context:
            User.signup("test", "test1@email.com", None, None)
            
    def test_authenticate(self):
        """Tests the authenticate method"""
        user = User.authenticate(
            "test1",
            "password"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.uid1)
        
    def test_invalid_username(self):
        """Tests authenticate with a bad username"""
        self.assertFalse(User.authenticate("test3", "password"))
            
    def test_invalid_password(self):
        """Tests authenticate with a bad password"""
        self.assertFalse(User.authenticate("test1", "password1"))