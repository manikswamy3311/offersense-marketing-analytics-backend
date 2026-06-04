from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthenticationCredentials
import logging
from app.services.auth_service import AuthService, UserService

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthenticationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user from JWT token.
    Validates the token and returns user information.
    """
    try:
        token = credentials.credentials
        
        # Verify token
        payload = AuthService.verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token type
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = UserService.get_user_by_id(payload.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """
    Dependency to ensure current user is active.
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_optional_user(credentials: HTTPAuthenticationCredentials = None):
    """
    Optional authentication - user is authenticated if token is provided,
    but request is allowed even without authentication.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
