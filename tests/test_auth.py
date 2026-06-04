import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.auth_service import AuthService, UserService
from app.models.models import UserCreate, UserLogin


class TestAuthService(unittest.TestCase):
    """Test authentication service functionality"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)
        
        # Hash should not be plaintext
        self.assertNotEqual(password, hashed)
        # Hash should be verifiable
        self.assertTrue(AuthService.verify_password(password, hashed))
    
    def test_verify_password_success(self):
        """Test successful password verification"""
        password = "SecurePassword123"
        hashed = AuthService.hash_password(password)
        
        result = AuthService.verify_password(password, hashed)
        self.assertTrue(result)
    
    def test_verify_password_failure(self):
        """Test failed password verification with wrong password"""
        password = "SecurePassword123"
        wrong_password = "WrongPassword"
        hashed = AuthService.hash_password(password)
        
        result = AuthService.verify_password(wrong_password, hashed)
        self.assertFalse(result)
    
    def test_create_access_token(self):
        """Test access token creation"""
        user_id = 1
        username = "testuser"
        
        token = AuthService.create_access_token(user_id, username)
        
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = 1
        username = "testuser"
        
        token = AuthService.create_refresh_token(user_id, username)
        
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
    
    def test_verify_access_token(self):
        """Test token verification"""
        user_id = 1
        username = "testuser"
        
        # Create token
        token = AuthService.create_access_token(user_id, username)
        
        # Verify token
        payload = AuthService.verify_token(token)
        
        self.assertIsNotNone(payload)
        self.assertEqual(payload.user_id, user_id)
        self.assertEqual(payload.username, username)
        self.assertEqual(payload.type, "access")
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        
        with self.assertRaises(Exception) as context:
            AuthService.verify_token(invalid_token)
        
        self.assertIn("Invalid token", str(context.exception))
    
    def test_verify_expired_token(self):
        """Test verification of expired token"""
        from datetime import timedelta
        user_id = 1
        username = "testuser"
        
        # Create token with immediate expiry
        token = AuthService.create_access_token(
            user_id, username,
            expires_delta=timedelta(seconds=-1)
        )
        
        with self.assertRaises(Exception) as context:
            AuthService.verify_token(token)
        
        self.assertIn("expired", str(context.exception).lower())


class TestUserService(unittest.TestCase):
    """Test user management service"""
    
    @patch('app.services.auth_service.get_connection')
    def test_get_user_by_id(self, mock_get_connection):
        """Test fetching user by ID"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock user data
        mock_user = MagicMock()
        mock_user.keys.return_value = ['id', 'username', 'email']
        mock_user.__getitem__ = lambda self, key: {
            'id': 1, 'username': 'testuser', 'email': 'test@example.com',
            'is_active': True
        }[key]
        mock_cursor.fetchone.return_value = mock_user
        
        result = UserService.get_user_by_id(1)
        
        self.assertIsNotNone(result)
        mock_conn.close.assert_called_once()
    
    @patch('app.services.auth_service.get_connection')
    def test_get_user_by_username(self, mock_get_connection):
        """Test fetching user by username"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock user data
        mock_user = MagicMock()
        mock_user.keys.return_value = ['id', 'username', 'email']
        mock_user.__getitem__ = lambda self, key: {
            'id': 1, 'username': 'testuser', 'email': 'test@example.com'
        }[key]
        mock_cursor.fetchone.return_value = mock_user
        
        result = UserService.get_user_by_username('testuser')
        
        self.assertIsNotNone(result)
        mock_conn.close.assert_called_once()
    
    @patch('app.services.auth_service.UserService.get_user_by_username')
    def test_authenticate_user_success(self, mock_get_user):
        """Test successful user authentication"""
        password = "TestPassword123"
        hashed = AuthService.hash_password(password)
        
        mock_get_user.return_value = {
            'id': 1,
            'username': 'testuser',
            'hashed_password': hashed,
            'is_active': True
        }
        
        success, user = UserService.authenticate_user('testuser', password)
        
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser')
    
    @patch('app.services.auth_service.UserService.get_user_by_username')
    def test_authenticate_user_wrong_password(self, mock_get_user):
        """Test authentication with wrong password"""
        password = "TestPassword123"
        hashed = AuthService.hash_password(password)
        
        mock_get_user.return_value = {
            'id': 1,
            'username': 'testuser',
            'hashed_password': hashed,
            'is_active': True
        }
        
        success, user = UserService.authenticate_user('testuser', 'WrongPassword')
        
        self.assertFalse(success)
        self.assertIsNone(user)
    
    @patch('app.services.auth_service.UserService.get_user_by_username')
    def test_authenticate_user_not_found(self, mock_get_user):
        """Test authentication with non-existent user"""
        mock_get_user.return_value = None
        
        success, user = UserService.authenticate_user('nonexistent', 'password')
        
        self.assertFalse(success)
        self.assertIsNone(user)


class TestAuthModels(unittest.TestCase):
    """Test authentication models"""
    
    def test_user_create_validation(self):
        """Test UserCreate model validation"""
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123",
            "full_name": "Test User"
        }
        
        user = UserCreate(**valid_data)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
    
    def test_user_create_short_password(self):
        """Test UserCreate rejects short password"""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",  # Less than 8 characters
            "full_name": "Test User"
        }
        
        with self.assertRaises(Exception):
            UserCreate(**invalid_data)
    
    def test_user_login_model(self):
        """Test UserLogin model"""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        login = UserLogin(**login_data)
        self.assertEqual(login.username, "testuser")
        self.assertEqual(login.password, "password123")


if __name__ == '__main__':
    unittest.main()
