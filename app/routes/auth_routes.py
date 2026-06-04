from fastapi import APIRouter, HTTPException, status, Depends
from app.models.models import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest
from app.services.auth_service import AuthService, UserService
from app.dependencies import get_current_user, security
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    - **full_name**: Optional full name
    """
    try:
        # Create user
        user = UserService.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        logger.info(f"New user registered: {user_data.username}")
        return user
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Registration error: {error_msg}")
        
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    """
    Login with username and password.
    
    Returns JWT access token and refresh token.
    """
    try:
        # Authenticate user
        success, user = UserService.authenticate_user(credentials.username, credentials.password)
        
        if not success:
            logger.warning(f"Failed login attempt: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create tokens
        access_token = AuthService.create_access_token(
            user_id=user["id"],
            username=user["username"]
        )
        refresh_token = AuthService.create_refresh_token(
            user_id=user["id"],
            username=user["username"]
        )
        
        logger.info(f"User logged in: {user['username']}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes in seconds
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token
        payload = AuthService.verify_token(request.refresh_token)
        
        if payload is None or payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = AuthService.create_access_token(
            user_id=payload.user_id,
            username=payload.username
        )
        
        logger.info(f"Token refreshed for user: {payload.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes in seconds
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    **Requires**: Valid JWT access token in Authorization header
    """
    return current_user


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: This is a client-side operation. Client should discard the token.
    Token will still be valid until expiration on server-side.
    For production, implement token blacklist in Redis.
    """
    logger.info(f"User logged out: {current_user['username']}")
    return {
        "message": "Logged out successfully",
        "username": current_user["username"]
    }


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Change password for current user.
    
    **Requires**: Valid JWT access token
    """
    try:
        success, message = UserService.change_password(
            user_id=current_user["id"],
            old_password=old_password,
            new_password=new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        logger.info(f"Password changed for user: {current_user['username']}")
        return {"message": message}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/deactivate")
def deactivate_account(current_user: dict = Depends(get_current_user)):
    """
    Deactivate current user account.
    
    **Warning**: This action cannot be undone without admin intervention.
    """
    try:
        success = UserService.deactivate_user(current_user["id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate account"
            )
        
        logger.info(f"Account deactivated: {current_user['username']}")
        return {"message": "Account deactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )
