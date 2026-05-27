import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.kpi_service import get_kpis
from app.services.crud_service import create_campaign, get_campaign_by_id
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


if __name__ == '__main__':
    unittest.main()
