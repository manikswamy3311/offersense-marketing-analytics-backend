import logging
from app.database.db import get_connection

logger = logging.getLogger(__name__)


def get_summary_stats() -> dict:
    """Statistical summary across all campaigns."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_campaigns,
                SUM(impressions)  as total_impressions,
                SUM(clicks)       as total_clicks,
                SUM(conversions)  as total_conversions,
                ROUND(AVG(impressions), 2) as avg_impressions,
                ROUND(AVG(clicks), 2)      as avg_clicks,
                ROUND(AVG(conversions), 2) as avg_conversions,
                MAX(impressions) as max_impressions,
                MIN(impressions) as min_impressions,
                MAX(clicks)      as max_clicks,
                MIN(clicks)      as min_clicks,
                MAX(conversions) as max_conversions,
                MIN(conversions) as min_conversions
            FROM campaigns
        """)
        row = cursor.fetchone()
        if not row or row["total_campaigns"] == 0:
            return {"error": "No campaign data found"}

        total_clicks = row["total_clicks"] or 0
        total_impressions = row["total_impressions"] or 0
        total_conversions = row["total_conversions"] or 0

        overall_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions else 0.0
        overall_conv_rate = round((total_conversions / total_clicks * 100), 2) if total_clicks else 0.0

        return {
            "total_campaigns": row["total_campaigns"],
            "totals": {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "conversions": total_conversions,
            },
            "averages": {
                "impressions": row["avg_impressions"],
                "clicks": row["avg_clicks"],
                "conversions": row["avg_conversions"],
            },
            "ranges": {
                "impressions": {"min": row["min_impressions"], "max": row["max_impressions"]},
                "clicks": {"min": row["min_clicks"], "max": row["max_clicks"]},
                "conversions": {"min": row["min_conversions"], "max": row["max_conversions"]},
            },
            "overall_kpis": {
                "ctr": overall_ctr,
                "conversion_rate": overall_conv_rate,
            }
        }
    except Exception as e:
        logger.error(f"Error in get_summary_stats: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


def get_benchmark() -> list:
    """Compare each campaign against the portfolio average."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, impressions, clicks, conversions FROM campaigns")
        rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return []

        # Compute per-campaign metrics
        for r in rows:
            r["ctr"] = round((r["clicks"] / r["impressions"] * 100), 2) if r["impressions"] else 0.0
            r["conversion_rate"] = round((r["conversions"] / r["clicks"] * 100), 2) if r["clicks"] else 0.0

        avg_ctr = round(sum(r["ctr"] for r in rows) / len(rows), 2)
        avg_conv = round(sum(r["conversion_rate"] for r in rows) / len(rows), 2)

        for r in rows:
            r["vs_avg_ctr"] = round(r["ctr"] - avg_ctr, 2)
            r["vs_avg_conversion_rate"] = round(r["conversion_rate"] - avg_conv, 2)
            r["ctr_status"] = "above_avg" if r["vs_avg_ctr"] >= 0 else "below_avg"
            r["conversion_status"] = "above_avg" if r["vs_avg_conversion_rate"] >= 0 else "below_avg"

        return {
            "benchmarks": {
                "avg_ctr": avg_ctr,
                "avg_conversion_rate": avg_conv,
            },
            "campaigns": rows,
        }
    except Exception as e:
        logger.error(f"Error in get_benchmark: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


def get_performance_scores() -> list:
    """
    Composite performance score per campaign (0-100).
    Score = 0.5 * normalised_ctr + 0.5 * normalised_conversion_rate
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, impressions, clicks, conversions FROM campaigns")
        rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return []

        for r in rows:
            r["ctr"] = (r["clicks"] / r["impressions"] * 100) if r["impressions"] else 0.0
            r["conversion_rate"] = (r["conversions"] / r["clicks"] * 100) if r["clicks"] else 0.0

        max_ctr = max(r["ctr"] for r in rows) or 1
        max_conv = max(r["conversion_rate"] for r in rows) or 1

        for r in rows:
            norm_ctr = r["ctr"] / max_ctr
            norm_conv = r["conversion_rate"] / max_conv
            r["performance_score"] = round((0.5 * norm_ctr + 0.5 * norm_conv) * 100, 1)
            r["ctr"] = round(r["ctr"], 2)
            r["conversion_rate"] = round(r["conversion_rate"], 2)

        return sorted(rows, key=lambda x: x["performance_score"], reverse=True)
    except Exception as e:
        logger.error(f"Error in get_performance_scores: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


def get_top_performers(metric: str = "conversion_rate", limit: int = 3) -> list:
    """Return top N campaigns by a given metric."""
    allowed = {"ctr", "conversion_rate", "impressions", "clicks", "conversions"}
    if metric not in allowed:
        raise ValueError(f"Invalid metric '{metric}'. Choose from: {', '.join(allowed)}")

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, impressions, clicks, conversions FROM campaigns")
        rows = [dict(r) for r in cursor.fetchall()]

        for r in rows:
            r["ctr"] = round((r["clicks"] / r["impressions"] * 100), 2) if r["impressions"] else 0.0
            r["conversion_rate"] = round((r["conversions"] / r["clicks"] * 100), 2) if r["clicks"] else 0.0

        return sorted(rows, key=lambda x: x[metric], reverse=True)[:limit]
    except Exception as e:
        logger.error(f"Error in get_top_performers: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()
