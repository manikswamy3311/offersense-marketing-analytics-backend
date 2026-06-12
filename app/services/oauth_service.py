import os
import secrets
import logging
import httpx
from typing import Optional
from app.database.db import get_connection
from app.models.models import OAuthUserInfo
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# ── Configuration (set these in .env / environment variables) ──────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

GITHUB_CLIENT_ID     = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI  = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

# ── In-memory state store (use Redis in production) ─────────────────────────
_oauth_states: set = set()


class OAuthService:

    # ── State helpers ────────────────────────────────────────────────────────

    @staticmethod
    def generate_state() -> str:
        state = secrets.token_urlsafe(32)
        _oauth_states.add(state)
        return state

    @staticmethod
    def validate_state(state: str) -> bool:
        if state in _oauth_states:
            _oauth_states.discard(state)
            return True
        return False

    # ── Google ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_google_auth_url(state: str) -> str:
        params = (
            f"client_id={GOOGLE_CLIENT_ID}"
            f"&redirect_uri={GOOGLE_REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&state={state}"
            f"&access_type=offline"
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

    @staticmethod
    async def exchange_google_code(code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            # Exchange code for tokens
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()

            # Get user info
            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_resp.raise_for_status()
            info = user_resp.json()

        return OAuthUserInfo(
            provider="google",
            oauth_id=info["sub"],
            email=info["email"],
            full_name=info.get("name"),
            username=info.get("email", "").split("@")[0],
        )

    # ── GitHub ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_github_auth_url(state: str) -> str:
        params = (
            f"client_id={GITHUB_CLIENT_ID}"
            f"&redirect_uri={GITHUB_REDIRECT_URI}"
            f"&scope=user:email"
            f"&state={state}"
        )
        return f"https://github.com/login/oauth/authorize?{params}"

    @staticmethod
    async def exchange_github_code(code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": GITHUB_REDIRECT_URI,
                },
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
            access_token = tokens["access_token"]

            # Get user profile
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()
            info = user_resp.json()

            # Get primary verified email if not in profile
            email = info.get("email")
            if not email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                emails_resp.raise_for_status()
                for e in emails_resp.json():
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        if not email:
            raise ValueError("GitHub account has no verified email address")

        return OAuthUserInfo(
            provider="github",
            oauth_id=str(info["id"]),
            email=email,
            full_name=info.get("name"),
            username=info.get("login"),
        )

    # ── User resolution ──────────────────────────────────────────────────────

    @staticmethod
    def get_or_create_oauth_user(info: OAuthUserInfo) -> dict:
        """Find existing OAuth user or create a new one, return user dict."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 1. Try to find by oauth_provider + oauth_id
            cursor.execute(
                "SELECT id, username, email, full_name, is_active, role FROM users "
                "WHERE oauth_provider = ? AND oauth_id = ?",
                (info.provider, info.oauth_id),
            )
            user = cursor.fetchone()
            if user:
                return dict(user)

            # 2. Try to find by email (link account)
            cursor.execute(
                "SELECT id, username, email, full_name, is_active, role FROM users WHERE email = ?",
                (info.email,),
            )
            user = cursor.fetchone()
            if user:
                # Link the OAuth provider to the existing account
                cursor.execute(
                    "UPDATE users SET oauth_provider = ?, oauth_id = ? WHERE id = ?",
                    (info.provider, info.oauth_id, dict(user)["id"]),
                )
                conn.commit()
                return dict(user)

            # 3. Create new OAuth user (no password)
            base_username = (info.username or info.email.split("@")[0]).lower()
            username = base_username
            suffix = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                username = f"{base_username}{suffix}"
                suffix += 1

            cursor.execute(
                """INSERT INTO users
                   (username, email, full_name, hashed_password, is_active, role, oauth_provider, oauth_id)
                   VALUES (?, ?, ?, '', 1, 'viewer', ?, ?)""",
                (username, info.email, info.full_name, info.provider, info.oauth_id),
            )
            conn.commit()
            user_id = cursor.lastrowid

            cursor.execute(
                "SELECT id, username, email, full_name, is_active, role FROM users WHERE id = ?",
                (user_id,),
            )
            return dict(cursor.fetchone())
        except Exception as e:
            logger.error(f"OAuth user resolution error: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_tokens_for_user(user: dict) -> dict:
        """Return access + refresh JWT tokens for an OAuth-authenticated user."""
        access_token = AuthService.create_access_token(
            user_id=user["id"],
            username=user["username"],
            role=user.get("role", "viewer"),
        )
        refresh_token = AuthService.create_refresh_token(
            user_id=user["id"],
            username=user["username"],
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
        }
