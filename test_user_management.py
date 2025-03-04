import unittest
from user_management import UserManager

class TestUserManager(unittest.TestCase):

    def setUp(self):
        self.user_manager = UserManager()

    def test_register_user(self):
        user_id = self.user_manager.register_user('testuser', 'password123', 'test@example.com')
        self.assertIn('testuser', self.user_manager.users)
        self.assertEqual(self.user_manager.users['testuser']['user_id'], user_id)

    def test_register_user_existing_username(self):
        self.user_manager.register_user('testuser', 'password123', 'test@example.com')
        with self.assertRaises(ValueError):
            self.user_manager.register_user('testuser', 'newpassword', 'new@example.com')

    def test_authenticate_user(self):
        self.user_manager.register_user('testuser', 'password123', 'test@example.com')
        self.assertTrue(self.user_manager.authenticate_user('testuser', 'password123'))
        self.assertFalse(self.user_manager.authenticate_user('testuser', 'wrongpassword'))

    def test_update_profile(self):
        user_id = self.user_manager.register_user('testuser', 'password123', 'test@example.com')
        profile_data = {'bio': 'This is a test bio'}
        self.assertTrue(self.user_manager.update_profile(user_id, profile_data))
        self.assertEqual(self.user_manager.users['testuser']['profile']['bio'], 'This is a test bio')

    def test_create_user(self):
        self.assertTrue(self.user_manager.create_user('test@example.com', 'password123'))
        self.assertIn('test@example.com', self.user_manager.users)

    def test_create_user_existing_email(self):
        self.user_manager.create_user('test@example.com', 'password123')
        self.assertFalse(self.user_manager.create_user('test@example.com', 'newpassword'))

    def test_verify_user(self):
        self.user_manager.create_user('test@example.com', 'password123')
        self.assertTrue(self.user_manager.verify_user('test@example.com', 'password123'))
        self.assertFalse(self.user_manager.verify_user('test@example.com', 'wrongpassword'))

    def test_get_user_profile(self):
        user_id = self.user_manager.register_user('testuser', 'password123', 'test@example.com')
        self.assertIsNone(self.user_manager.get_user_profile(user_id))
        self.user_manager.update_risk_profile(user_id, 'low')
        self.assertEqual(self.user_manager.get_user_profile(user_id), 'low')

    def test_update_risk_profile(self):
        user_id = self.user_manager.register_user('testuser', 'password123', 'test@example.com')
        self.assertTrue(self.user_manager.update_risk_profile(user_id, 'high'))
        self.assertEqual(self.user_manager.users['testuser']['risk_profile'], 'high')

if __name__ == '__main__':
    unittest.main() 
