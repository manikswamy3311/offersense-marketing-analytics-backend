import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.analytics_service import (
    get_summary_stats, get_benchmark, get_performance_scores, get_top_performers
)


def _make_row(name, impressions, clicks, conversions):
    """Helper: create a mock sqlite3.Row-like dict."""
    row = MagicMock()
    data = {
        "id": 1, "name": name,
        "impressions": impressions, "clicks": clicks, "conversions": conversions,
        "total_campaigns": 3,
        "total_impressions": impressions, "total_clicks": clicks,
        "total_conversions": conversions,
        "avg_impressions": impressions, "avg_clicks": clicks,
        "avg_conversions": conversions,
        "max_impressions": impressions, "min_impressions": impressions,
        "max_clicks": clicks, "min_clicks": clicks,
        "max_conversions": conversions, "min_conversions": conversions,
    }
    row.__getitem__ = lambda self, k: data[k]
    row.keys = lambda: list(data.keys())
    return row


SAMPLE_ROWS = [
    {"id": 1, "name": "Campaign A", "impressions": 1000, "clicks": 100, "conversions": 15},
    {"id": 2, "name": "Campaign B", "impressions": 2000, "clicks": 150, "conversions": 12},
    {"id": 3, "name": "Campaign C", "impressions": 500,  "clicks": 80,  "conversions": 5},
]


class TestSummaryStats(unittest.TestCase):

    @patch('app.services.analytics_service.get_connection')
    def test_summary_returns_expected_keys(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        summary_row = _make_row("", 5000, 500, 50)
        summary_row.__getitem__ = lambda self, k: {
            "total_campaigns": 3,
            "total_impressions": 5000, "total_clicks": 500, "total_conversions": 50,
            "avg_impressions": 1666.67, "avg_clicks": 166.67, "avg_conversions": 16.67,
            "max_impressions": 2000, "min_impressions": 500,
            "max_clicks": 200, "min_clicks": 80,
            "max_conversions": 25, "min_conversions": 5,
        }[k]
        mock_cursor.fetchone.return_value = summary_row

        result = get_summary_stats()

        self.assertIn("total_campaigns", result)
        self.assertIn("totals", result)
        self.assertIn("averages", result)
        self.assertIn("ranges", result)
        self.assertIn("overall_kpis", result)
        self.assertEqual(result["total_campaigns"], 3)
        mock_conn.close.assert_called_once()

    @patch('app.services.analytics_service.get_connection')
    def test_summary_no_data(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        empty_row = MagicMock()
        empty_row.__getitem__ = lambda self, k: 0 if k != "total_campaigns" else 0
        mock_cursor.fetchone.return_value = empty_row

        result = get_summary_stats()
        self.assertIn("error", result)


class TestBenchmark(unittest.TestCase):

    @patch('app.services.analytics_service.get_connection')
    def test_benchmark_above_below_avg(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_rows = []
        for r in SAMPLE_ROWS:
            m = MagicMock()
            m.__getitem__ = lambda self, k, _r=r: _r[k]
            m.keys = lambda _r=r: list(_r.keys())
            mock_rows.append(m)
        mock_cursor.fetchall.return_value = mock_rows

        result = get_benchmark()

        self.assertIn("benchmarks", result)
        self.assertIn("campaigns", result)
        self.assertIn("avg_ctr", result["benchmarks"])
        self.assertIn("avg_conversion_rate", result["benchmarks"])
        for c in result["campaigns"]:
            self.assertIn("vs_avg_ctr", c)
            self.assertIn("ctr_status", c)

    @patch('app.services.analytics_service.get_connection')
    def test_benchmark_empty(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        result = get_benchmark()
        self.assertEqual(result, [])


class TestPerformanceScores(unittest.TestCase):

    @patch('app.services.analytics_service.get_connection')
    def test_scores_between_0_and_100(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_rows = []
        for r in SAMPLE_ROWS:
            m = MagicMock()
            m.__getitem__ = lambda self, k, _r=r: _r[k]
            m.keys = lambda _r=r: list(_r.keys())
            mock_rows.append(m)
        mock_cursor.fetchall.return_value = mock_rows

        result = get_performance_scores()

        self.assertEqual(len(result), 3)
        for c in result:
            self.assertIn("performance_score", c)
            self.assertGreaterEqual(c["performance_score"], 0)
            self.assertLessEqual(c["performance_score"], 100)

    @patch('app.services.analytics_service.get_connection')
    def test_scores_sorted_descending(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_rows = []
        for r in SAMPLE_ROWS:
            m = MagicMock()
            m.__getitem__ = lambda self, k, _r=r: _r[k]
            m.keys = lambda _r=r: list(_r.keys())
            mock_rows.append(m)
        mock_cursor.fetchall.return_value = mock_rows

        result = get_performance_scores()
        scores = [c["performance_score"] for c in result]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestTopPerformers(unittest.TestCase):

    @patch('app.services.analytics_service.get_connection')
    def test_top_by_conversion_rate(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_rows = []
        for r in SAMPLE_ROWS:
            m = MagicMock()
            m.__getitem__ = lambda self, k, _r=r: _r[k]
            m.keys = lambda _r=r: list(_r.keys())
            mock_rows.append(m)
        mock_cursor.fetchall.return_value = mock_rows

        result = get_top_performers(metric="conversion_rate", limit=2)

        self.assertEqual(len(result), 2)
        # First result should have highest conversion rate
        self.assertGreaterEqual(
            result[0]["conversion_rate"], result[1]["conversion_rate"]
        )

    @patch('app.services.analytics_service.get_connection')
    def test_top_limit_respected(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_rows = []
        for r in SAMPLE_ROWS:
            m = MagicMock()
            m.__getitem__ = lambda self, k, _r=r: _r[k]
            m.keys = lambda _r=r: list(_r.keys())
            mock_rows.append(m)
        mock_cursor.fetchall.return_value = mock_rows

        result = get_top_performers(metric="clicks", limit=1)
        self.assertEqual(len(result), 1)

    def test_invalid_metric_raises(self):
        with self.assertRaises(ValueError):
            get_top_performers(metric="invalid_metric")


if __name__ == '__main__':
    unittest.main()
