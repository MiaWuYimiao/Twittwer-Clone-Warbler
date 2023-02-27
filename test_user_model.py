"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

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

app.app_context().push()
db.create_all()


class UserModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.u1 = u1
        self.uid1 = u1.id

        self.u2 = u2
        self.uid2 = u2.id

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

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

    def test_repr(self):
        """Does the repr method work as expected"""

        self.assertEquals(self.u1.__repr__(), f"<User #{self.uid1}: testuser1, test1@test.com>")
        self.assertEquals(self.u2.__repr__(), f"<User #{self.uid2}: testuser2, test2@test.com>")

    ####
    #
    # Following tests
    #
    ####
    def test_user_follows(self):
        """Basic test for user follows"""
        
        following = Follows(user_being_followed_id="2", user_following_id="1")
        db.session.add(following)
        db.session.commit()

        self.assertEquals(len(self.u1.following), 1)
        self.assertEquals(len(self.u1.followers), 0)
        self.assertEquals(len(self.u2.following), 0)
        self.assertEquals(len(self.u2.followers), 1)

        self.assertEquals(self.u1.following[0].id, 2)
        self.assertEquals(self.u2.followers[0].id, 1)
        

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEquals(self.u1.is_following(self.u2), True)
        self.assertFalse(self.u2.is_following(self.u1))


    def test_is_followed_by(self):
        """Does is_following successfully detect when user1 is following user2?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEquals(self.u1.is_followed_by(self.u2), False)
        self.assertTrue(self.u2.is_followed_by(self.u1))
        
    ####
    #
    # Sign in test
    #
    ####
    def test_valid_signup(self):
        """Test user signup"""

        u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", None)
        db.session.commit()

        u_test = User.query.get_or_404(u.id)
        self.assertIsNotNone(u_test)
        self.assertEquals(u_test.username, "testuser")
        self.assertEquals(u_test.email, "test@test.com")
        self.assertEquals(u_test.username, "testuser")
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):

        u = User.signup(None, "test@test.com", "HASHED_PASSWORD", None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):

        u = User.signup("user1", None, "HASHED_PASSWORD", None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None, None)

    
    ####
    #
    # Authenticate test
    #
    ####
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "HASHED_PASSWORD")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "HASHED_PASSWORD"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "password"))