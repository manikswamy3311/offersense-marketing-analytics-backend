from app.database.db import get_connection
import logging
import math

logger = logging.getLogger(__name__)


def log_action(user_id: int, username: str, action: str, campaign_id: int = None):
    """Write one audit log entry. Silently swallows errors so it never breaks a request."""
    conn = None
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_logs (user_id, username, action, campaign_id) VALUES (?, ?, ?, ?)",
            (user_id, username, action, campaign_id),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Audit log write failed: {e}")
    finally:
        if conn:
            conn.close()


def get_audit_logs(page: int = 1, limit: int = 50):
    """Return paginated audit log entries, newest first."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total = cursor.fetchone()[0]

        offset = (page - 1) * limit
        cursor.execute(
            "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = [dict(r) for r in cursor.fetchall()]

        pages = math.ceil(total / limit) if total > 0 else 1

        return {
            "logs": rows,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        }
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise Exception(f"Failed to fetch audit logs: {e}")
    finally:
        if conn:
            conn.close()
