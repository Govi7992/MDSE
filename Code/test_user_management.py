import unittest
from datetime import datetime
from user_management import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.user_manager = UserManager()
        
        # Sample test data
        self.test_username = "testuser"
        self.test_password = "Test@123"
        self.test_email = "test@example.com"
        self.test_profile_data = {
            "name": "Test User",
            "age": 30,
            "risk_tolerance": "moderate"
        }

    def test_register_user(self):
        """Test user registration"""
        user_id = self.user_manager.register_user(
            self.test_username,
            self.test_password,
            self.test_email
        )
        
        self.assertIsNotNone(user_id)
        self.assertIn(self.test_username, self.user_manager.users)
        
        user = self.user_manager.users[self.test_username]
        self.assertEqual(user['email'], self.test_email)
        self.assertNotEqual(user['password'], self.test_password)  # Password should be hashed
        self.assertIsInstance(user['created_at'], datetime)

    def test_register_duplicate_username(self):
        """Test registration with duplicate username"""
        # Register first user
        self.user_manager.register_user(
            self.test_username,
            self.test_password,
            self.test_email
        )
        
        # Try to register duplicate username
        with self.assertRaises(ValueError):
            self.user_manager.register_user(
                self.test_username,
                "different_password",
                "different@example.com"
            )

    def test_authenticate_user(self):
        """Test user authentication"""
        # Register user
        self.user_manager.register_user(
            self.test_username,
            self.test_password,
            self.test_email
        )
        
        # Test correct password
        self.assertTrue(
            self.user_manager.authenticate_user(
                self.test_username,
                self.test_password
            )
        )
        
        # Test incorrect password
        self.assertFalse(
            self.user_manager.authenticate_user(
                self.test_username,
                "wrong_password"
            )
        )

    def test_authenticate_nonexistent_user(self):
        """Test authentication with non-existent user"""
        self.assertFalse(
            self.user_manager.authenticate_user(
                "nonexistent_user",
                self.test_password
            )
        )

    def test_update_profile(self):
        """Test profile update"""
        # Register user
        user_id = self.user_manager.register_user(
            self.test_username,
            self.test_password,
            self.test_email
        )
        
        # Update profile
        success = self.user_manager.update_profile(
            user_id,
            self.test_profile_data
        )
        
        self.assertTrue(success)
        user = self.user_manager.users[self.test_username]
        self.assertEqual(user['profile'], self.test_profile_data)

    def test_update_nonexistent_profile(self):
        """Test updating profile for non-existent user"""
        success = self.user_manager.update_profile(
            "nonexistent_id",
            self.test_profile_data
        )
        self.assertFalse(success)

    def test_create_user(self):
        """Test user creation with email"""
        success = self.user_manager.create_user(
            self.test_email,
            self.test_password
        )
        
        self.assertTrue(success)
        self.assertIn(self.test_email, self.user_manager.users)
        self.assertEqual(
            self.user_manager.users[self.test_email]['password'],
            self.test_password
        )

    def test_create_duplicate_user(self):
        """Test creation of duplicate user"""
        # Create first user
        self.user_manager.create_user(
            self.test_email,
            self.test_password
        )
        
        # Try to create duplicate user
        success = self.user_manager.create_user(
            self.test_email,
            "different_password"
        )
        
        self.assertFalse(success)

    def test_verify_user(self):
        """Test user verification"""
        # Create user
        self.user_manager.create_user(
            self.test_email,
            self.test_password
        )
        
        # Test correct credentials
        self.assertTrue(
            self.user_manager.verify_user(
                self.test_email,
                self.test_password
            )
        )
        
        # Test incorrect password
        self.assertFalse(
            self.user_manager.verify_user(
                self.test_email,
                "wrong_password"
            )
        )

    def test_get_user_profile(self):
        """Test getting user profile"""
        # Create user and set risk profile
        self.user_manager.create_user(
            self.test_email,
            self.test_password
        )
        self.user_manager.update_risk_profile(
            self.test_email,
            "aggressive"
        )
        
        profile = self.user_manager.get_user_profile(self.test_email)
        self.assertEqual(profile, "aggressive")

    def test_get_nonexistent_user_profile(self):
        """Test getting profile of non-existent user"""
        profile = self.user_manager.get_user_profile("nonexistent@example.com")
        self.assertIsNone(profile)

    def test_update_risk_profile(self):
        """Test updating risk profile"""
        # Create user
        self.user_manager.create_user(
            self.test_email,
            self.test_password
        )
        
        # Update risk profile
        success = self.user_manager.update_risk_profile(
            self.test_email,
            "conservative"
        )
        
        self.assertTrue(success)
        self.assertEqual(
            self.user_manager.users[self.test_email]['risk_profile'],
            "conservative"
        )

    def test_update_nonexistent_user_risk_profile(self):
        """Test updating risk profile for non-existent user"""
        success = self.user_manager.update_risk_profile(
            "nonexistent@example.com",
            "moderate"
        )
        self.assertFalse(success)

    def test_password_hashing(self):
        """Test password hashing"""
        # Register user
        user_id = self.user_manager.register_user(
            self.test_username,
            self.test_password,
            self.test_email
        )
        
        user = self.user_manager.users[self.test_username]
        
        # Verify password is hashed
        self.assertNotEqual(user['password'], self.test_password)
        self.assertTrue(len(user['salt']) > 0)
        
        # Verify hashing is consistent
        hashed = self.user_manager._hash_password(
            self.test_password,
            user['salt']
        )
        self.assertEqual(hashed, user['password'])

if __name__ == '__main__':
    unittest.main() 