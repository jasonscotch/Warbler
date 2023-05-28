"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Likes, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages"""
    
    def setUp(self):
        """Create test client, add sample data"""
        db.drop_all()
        db.create_all()
        
        user1 = User.signup("test1", "test1@email.com", "password", None)
        uid1 = 1111
        user1.id = uid1

        db.session.commit()

        user1 = User.query.get(uid1)

        self.user1 = user1
        self.uid1 = uid1

        self.client = app.test_client()
        
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res    
    
    def test_message_model(self):
        """Does basic message model work"""
        
        message = Message(
            text='Here is a test message I am posting.',
            user_id=1111
        )
        
        db.session.add(message)
        db.session.commit()
        
        self.assertEqual(len(self.user1.messages), 1)
        self.assertEqual(self.user1.messages[0].text, 'Here is a test message I am posting.')
        
    def test_message_likes(self):
        """Tests liking messages"""
        
        user2 = User.signup("test2", "test2@email.com", "password", None)
        uid2 = 2222
        user2.id = uid2

        db.session.commit()

        user2 = User.query.get(uid2)
        
        message = Message(
            text='Here is a test message I am posting.',
            user_id=1111
        )
        
        db.session.add(message)
        db.session.commit()
        
        user2.likes.append(message)
        
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == uid2).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message.id)