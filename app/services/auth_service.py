import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from passlib.context import CryptContext
from app.database.db import get_connection
from app.models.models import TokenPayload

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Change in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# In-memory token blacklist (use Redis in production for multi-instance support)
_token_blacklist: set = set()

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class AccountLockedException(Exception):
    pass


class AuthService:
    """Authentication and authorization service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(user_id: int, username: str, role: str = "viewer", expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "type": "access"
        }
        
        try:
            encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise Exception("Failed to create access token")
    
    @staticmethod
    def create_refresh_token(user_id: int, username: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "type": "refresh"
        }
        
        try:
            encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise Exception("Failed to create refresh token")
    
    @staticmethod
    def blacklist_token(token: str) -> None:
        """Add token to blacklist (invalidate it)"""
        _token_blacklist.add(token)
        logger.info("Token blacklisted")

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if token has been blacklisted"""
        return token in _token_blacklist

    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        if token in _token_blacklist:
            raise Exception("Token has been revoked")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            username = payload.get("username")
            
            if user_id is None or username is None:
                return None
            
            return TokenPayload(
                user_id=user_id,
                username=username,
                role=payload.get("role", "viewer"),
                exp=payload.get("exp"),
                type=payload.get("type", "access")
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            raise Exception("Invalid token")
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            raise Exception("Token verification failed")


class UserService:
    """User management service"""
    
    @staticmethod
    def get_user_by_id(user_id: int):
        """Get user by ID"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, full_name, is_active, role, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            raise Exception(f"Failed to fetch user: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_user_by_username(username: str):
        """Get user by username"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"Error fetching user by username: {str(e)}")
            raise Exception(f"Failed to fetch user: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_user_by_email(email: str):
        """Get user by email"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"Error fetching user by email: {str(e)}")
            raise Exception(f"Failed to fetch user: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def create_user(username: str, email: str, password: str, full_name: Optional[str] = None, role: str = "viewer"):
        """Create new user"""
        conn = None
        try:
            # Check if user exists
            if UserService.get_user_by_username(username):
                raise Exception("Username already exists")
            
            if UserService.get_user_by_email(email):
                raise Exception("Email already exists")
            
            # Hash password and create user
            hashed_password = AuthService.hash_password(password)
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (username, email, full_name, hashed_password, is_active, role)
                   VALUES (?, ?, ?, ?, 1, ?)""",
                (username, email, full_name, hashed_password, role)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            logger.info(f"User created: {username}")
            return UserService.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """Authenticate user by username and password"""
        try:
            user = UserService.get_user_by_username(username)
            
            if not user:
                logger.warning(f"Login attempt with non-existent username: {username}")
                return False, None
            
            if not user.get("is_active"):
                logger.warning(f"Login attempt with inactive user: {username}")
                return False, None

            # Block password login for OAuth-only accounts
            if user.get("hashed_password") == "OAUTH_NO_PASSWORD":
                logger.warning(f"Password login attempt on OAuth-only account: {username}")
                return False, None

            # Check account lockout
            locked_until_str = user.get("locked_until")
            if locked_until_str:
                try:
                    locked_until = datetime.fromisoformat(str(locked_until_str))
                    if locked_until > datetime.utcnow():
                        remaining = max(1, int((locked_until - datetime.utcnow()).total_seconds() / 60) + 1)
                        raise AccountLockedException(
                            f"Account locked due to too many failed attempts. Try again in {remaining} minute(s)."
                        )
                    else:
                        # Lock expired — clear it
                        AuthService._reset_failed_attempts(user["id"])
                except AccountLockedException:
                    raise
                except Exception:
                    pass
            
            # Verify password
            if not AuthService.verify_password(password, user.get("hashed_password")):
                logger.warning(f"Failed login attempt for user: {username}")
                AuthService._increment_failed_attempts(user["id"])
                return False, None
            
            # Success — reset lockout counter
            AuthService._reset_failed_attempts(user["id"])
            logger.info(f"User authenticated: {username}")
            return True, user
        except AccountLockedException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return False, None

    @staticmethod
    def _increment_failed_attempts(user_id: int):
        """Increment failed login counter; lock account if threshold reached."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id = ?",
                (user_id,)
            )
            cursor.execute("SELECT failed_attempts FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            attempts = row[0] if row else 0
            if attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                cursor.execute(
                    "UPDATE users SET locked_until = ? WHERE id = ?",
                    (locked_until.isoformat(), user_id)
                )
                logger.warning(f"Account locked: user_id={user_id} after {attempts} failed attempts")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to increment failed attempts: {e}")
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _reset_failed_attempts(user_id: int):
        """Reset failed login counter and clear lockout."""
        conn = None
        try:
            conn = get_connection()
            conn.execute(
                "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to reset failed attempts: {e}")
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def deactivate_user(user_id: int) -> bool:
        """Deactivate a user account"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            
            logger.info(f"User deactivated: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        conn = None
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            # Verify old password
            if not AuthService.verify_password(old_password, user.get("hashed_password")):
                return False, "Old password is incorrect"
            
            # Hash new password
            hashed_password = AuthService.hash_password(new_password)
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (hashed_password, user_id)
            )
            conn.commit()
            
            logger.info(f"Password changed for user: {user_id}")
            return True, "Password changed successfully"
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            if conn:
                conn.rollback()
            return False, str(e)
        finally:
            if conn:
                conn.close()
