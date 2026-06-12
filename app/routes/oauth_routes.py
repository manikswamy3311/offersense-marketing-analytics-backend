from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from app.services.oauth_service import OAuthService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["OAuth"])


# ── Google ────────────────────────────────────────────────────────────────────

@router.get("/google/login")
def google_login():
    """Redirect browser to Google's OAuth consent screen."""
    state = OAuthService.generate_state()
    url = OAuthService.get_google_auth_url(state)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """
    Google redirects here after the user grants permission.
    Returns JWT access + refresh tokens.
    """
    if not OAuthService.validate_state(state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    try:
        user_info = await OAuthService.exchange_google_code(code)
    except Exception as e:
        logger.error(f"Google OAuth token exchange failed: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google authentication failed")

    try:
        user = OAuthService.get_or_create_oauth_user(user_info)
    except Exception as e:
        logger.error(f"OAuth user resolution failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve user")

    logger.info(f"Google OAuth login: {user['username']}")
    return OAuthService.create_tokens_for_user(user)


# ── GitHub ────────────────────────────────────────────────────────────────────

@router.get("/github/login")
def github_login():
    """Redirect browser to GitHub's OAuth consent screen."""
    state = OAuthService.generate_state()
    url = OAuthService.get_github_auth_url(state)
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """
    GitHub redirects here after the user grants permission.
    Returns JWT access + refresh tokens.
    """
    if not OAuthService.validate_state(state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    try:
        user_info = await OAuthService.exchange_github_code(code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"GitHub OAuth token exchange failed: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub authentication failed")

    try:
        user = OAuthService.get_or_create_oauth_user(user_info)
    except Exception as e:
        logger.error(f"OAuth user resolution failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve user")

    logger.info(f"GitHub OAuth login: {user['username']}")
    return OAuthService.create_tokens_for_user(user)
