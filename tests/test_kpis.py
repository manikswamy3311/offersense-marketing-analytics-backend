import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.kpi_service import get_kpis
from app.services.crud_service import create_campaign, get_campaign_by_id, get_campaigns_paginated
from app.models.models import CampaignCreate


class TestKPIService(unittest.TestCase):
    """Test KPI calculations"""
    
    @patch('app.services.kpi_service.get_connection')
    def test_get_kpis_success(self, mock_get_connection):
        """Test successful KPI calculation"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query result: impressions=5000, clicks=500, conversions=50
        mock_cursor.fetchone.return_value = (5000, 500, 50)
        
        # Call the function
        result = get_kpis()
        
        # Assertions
        self.assertEqual(result['impressions'], 5000)
        self.assertEqual(result['clicks'], 500)
        self.assertEqual(result['conversions'], 50)
        self.assertEqual(result['ctr'], 10.0)  # (500/5000)*100 = 10%
        self.assertEqual(result['conversion_rate'], 10.0)  # (50/500)*100 = 10%
        
        # Verify connection was closed
        mock_conn.close.assert_called_once()
    
    @patch('app.services.kpi_service.get_connection')
    def test_get_kpis_zero_impressions(self, mock_get_connection):
        """Test KPI calculation with zero impressions"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Zero impressions
        mock_cursor.fetchone.return_value = (0, 0, 0)
        
        result = get_kpis()
        
        self.assertEqual(result['ctr'], 0.0)
        self.assertEqual(result['conversion_rate'], 0.0)
    
    @patch('app.services.kpi_service.get_connection')
    def test_get_kpis_none_values(self, mock_get_connection):
        """Test KPI calculation with None values from empty table"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # None values (empty table)
        mock_cursor.fetchone.return_value = (None, None, None)
        
        result = get_kpis()
        
        self.assertEqual(result['impressions'], 0)
        self.assertEqual(result['clicks'], 0)
        self.assertEqual(result['conversions'], 0)
        self.assertEqual(result['ctr'], 0.0)
        self.assertEqual(result['conversion_rate'], 0.0)


class TestCRUDService(unittest.TestCase):
    """Test CRUD operations"""
    
    @patch('app.services.crud_service.get_connection')
    def test_create_campaign_success(self, mock_get_connection):
        """Test successful campaign creation"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock lastrowid
        mock_cursor.lastrowid = 1
        
        # Mock fetchone to return campaign data
        mock_row = MagicMock()
        mock_row.keys.return_value = ['id', 'name', 'impressions', 'clicks', 'conversions']
        mock_row.__getitem__ = lambda self, key: {
            'id': 1, 'name': 'Test Campaign', 
            'impressions': 1000, 'clicks': 100, 'conversions': 10
        }[key]
        mock_cursor.fetchone.return_value = mock_row
        
        # Create campaign data
        campaign_data = CampaignCreate(
            name="Test Campaign",
            impressions=1000,
            clicks=100,
            conversions=10
        )
        
        # Call function
        result = create_campaign(campaign_data)
        
        # Assertions
        self.assertIsNotNone(result)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('app.services.crud_service.get_connection')
    def test_get_campaign_by_id_not_found(self, mock_get_connection):
        """Test getting a campaign that doesn't exist"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock no result found
        mock_cursor.fetchone.return_value = None
        
        # Call function
        result = get_campaign_by_id(999)
        
        # Should return None for non-existent campaign
        self.assertIsNone(result)
        mock_conn.close.assert_called_once()


class TestCalculations(unittest.TestCase):
    """Test calculation logic"""
    
    def test_ctr_calculation(self):
        """Test CTR calculation formula"""
        impressions = 1000
        clicks = 100
        ctr = round((clicks / impressions) * 100, 2)
        self.assertEqual(ctr, 10.0)
    
    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation formula"""
        clicks = 100
        conversions = 15
        conversion_rate = round((conversions / clicks) * 100, 2)
        self.assertEqual(conversion_rate, 15.0)
    
    def test_division_by_zero_handling(self):
        """Test that division by zero is handled"""
        impressions = 0
        clicks = 0
        ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.00
        self.assertEqual(ctr, 0.0)


class TestPaginationService(unittest.TestCase):
    """Test paginated campaign retrieval"""

    def _make_row(self, id, name, impressions, clicks, conversions):
        return {'id': id, 'name': name, 'impressions': impressions,
                'clicks': clicks, 'conversions': conversions}

    def _setup_mock(self, mock_get_connection, total, rows):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (total,)
        mock_cursor.fetchall.return_value = rows
        return mock_conn, mock_cursor

    @patch('app.services.crud_service.get_connection')
    def test_first_page_has_next(self, mock_get_connection):
        """First page of multiple: has_next=True, has_prev=False"""
        rows = [
            self._make_row(1, 'Alpha', 1000, 100, 10),
            self._make_row(2, 'Beta',  2000, 200, 20),
        ]
        self._setup_mock(mock_get_connection, total=3, rows=rows)

        result = get_campaigns_paginated(page=1, limit=2)

        self.assertEqual(result['total'], 3)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['limit'], 2)
        self.assertEqual(result['pages'], 2)
        self.assertTrue(result['has_next'])
        self.assertFalse(result['has_prev'])
        self.assertEqual(len(result['campaigns']), 2)

    @patch('app.services.crud_service.get_connection')
    def test_last_page_has_prev(self, mock_get_connection):
        """Last page: has_next=False, has_prev=True"""
        rows = [self._make_row(3, 'Gamma', 500, 50, 5)]
        self._setup_mock(mock_get_connection, total=3, rows=rows)

        result = get_campaigns_paginated(page=2, limit=2)

        self.assertFalse(result['has_next'])
        self.assertTrue(result['has_prev'])
        self.assertEqual(result['pages'], 2)
        self.assertEqual(len(result['campaigns']), 1)

    @patch('app.services.crud_service.get_connection')
    def test_single_page_no_nav(self, mock_get_connection):
        """All results fit on one page: no next or prev"""
        rows = [self._make_row(1, 'Solo', 1000, 100, 10)]
        self._setup_mock(mock_get_connection, total=1, rows=rows)

        result = get_campaigns_paginated(page=1, limit=20)

        self.assertFalse(result['has_next'])
        self.assertFalse(result['has_prev'])
        self.assertEqual(result['pages'], 1)

    @patch('app.services.crud_service.get_connection')
    def test_empty_table(self, mock_get_connection):
        """Empty table returns zero total, one page, empty list"""
        self._setup_mock(mock_get_connection, total=0, rows=[])

        result = get_campaigns_paginated(page=1, limit=20)

        self.assertEqual(result['total'], 0)
        self.assertEqual(result['pages'], 1)
        self.assertFalse(result['has_next'])
        self.assertFalse(result['has_prev'])
        self.assertEqual(result['campaigns'], [])

    @patch('app.services.crud_service.get_connection')
    def test_ctr_and_conversion_rate_computed(self, mock_get_connection):
        """CTR and conversion_rate are calculated on the paginated rows"""
        rows = [self._make_row(1, 'Campaign X', 1000, 100, 25)]
        self._setup_mock(mock_get_connection, total=1, rows=rows)

        result = get_campaigns_paginated(page=1, limit=20)
        campaign = result['campaigns'][0]

        self.assertEqual(campaign['ctr'], 10.0)           # (100/1000)*100
        self.assertEqual(campaign['conversion_rate'], 25.0)  # (25/100)*100

    @patch('app.services.crud_service.get_connection')
    def test_correct_offset_passed_to_db(self, mock_get_connection):
        """LIMIT and OFFSET are derived correctly from page/limit params"""
        mock_conn, mock_cursor = self._setup_mock(mock_get_connection, total=50, rows=[])

        get_campaigns_paginated(page=3, limit=10)

        # Page 3, limit 10 → OFFSET = (3-1)*10 = 20
        call_args = mock_cursor.execute.call_args_list
        paginated_call = call_args[-1]
        self.assertIn(10, paginated_call[0][1])   # limit
        self.assertIn(20, paginated_call[0][1])   # offset

    @patch('app.services.crud_service.get_connection')
    def test_connection_closed_on_success(self, mock_get_connection):
        """DB connection is always closed after a successful call"""
        mock_conn, _ = self._setup_mock(mock_get_connection, total=0, rows=[])

        get_campaigns_paginated(page=1, limit=10)

        mock_conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
