import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.kpi_service import get_kpis
from app.services.crud_service import create_campaign, get_campaign_by_id, get_campaigns_paginated, delete_campaign, restore_campaign
from app.services.audit_service import log_action, get_audit_logs
from app.services.auth_service import AuthService, AccountLockedException
from app.models.models import CampaignCreate, UserCreate


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

    @patch('app.services.crud_service.get_connection')
    def test_name_filter_uses_like(self, mock_get_connection):
        """name filter passes LIKE param with % wildcards to the query"""
        mock_conn, mock_cursor = self._setup_mock(mock_get_connection, total=1, rows=[
            self._make_row(1, 'Summer Sale', 500, 50, 5)
        ])

        get_campaigns_paginated(page=1, limit=20, name='Summer')

        all_calls = mock_cursor.execute.call_args_list
        # At least one call should contain %Summer%
        params_used = [str(c) for c in all_calls]
        self.assertTrue(any('%Summer%' in p for p in params_used))

    @patch('app.services.crud_service.get_connection')
    def test_invalid_sort_column_falls_back_to_id(self, mock_get_connection):
        """Unknown sort_by value is silently replaced with 'id' (SQL injection guard)"""
        mock_conn, mock_cursor = self._setup_mock(mock_get_connection, total=0, rows=[])

        # Should not raise; unknown column is rejected
        get_campaigns_paginated(page=1, limit=10, sort_by='malicious; DROP TABLE campaigns--')

        all_calls = [str(c) for c in mock_cursor.execute.call_args_list]
        self.assertTrue(any('ORDER BY id' in c for c in all_calls))

    @patch('app.services.crud_service.get_connection')
    def test_sort_desc_order(self, mock_get_connection):
        """order=desc produces DESC in the SQL query"""
        mock_conn, mock_cursor = self._setup_mock(mock_get_connection, total=0, rows=[])

        get_campaigns_paginated(page=1, limit=10, sort_by='clicks', order='desc')

        all_calls = [str(c) for c in mock_cursor.execute.call_args_list]
        self.assertTrue(any('clicks DESC' in c for c in all_calls))

    @patch('app.services.crud_service.get_connection')
    def test_sort_asc_order_default(self, mock_get_connection):
        """order=asc (default) produces ASC in the SQL query"""
        mock_conn, mock_cursor = self._setup_mock(mock_get_connection, total=0, rows=[])

        get_campaigns_paginated(page=1, limit=10, sort_by='name', order='asc')

        all_calls = [str(c) for c in mock_cursor.execute.call_args_list]
        self.assertTrue(any('name ASC' in c for c in all_calls))


class TestSoftDelete(unittest.TestCase):
    """Test soft delete and restore behavior"""

    @patch('app.services.crud_service.get_connection')
    def test_delete_sets_is_deleted_flag(self, mock_get_connection):
        """delete_campaign updates is_deleted=1, does not DELETE the row"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # campaign found

        result = delete_campaign(1)

        self.assertTrue(result)
        executed = [str(c) for c in mock_cursor.execute.call_args_list]
        self.assertTrue(any('is_deleted = 1' in c for c in executed))
        self.assertFalse(any('DELETE' in c.upper() for c in executed))

    @patch('app.services.crud_service.get_connection')
    def test_delete_returns_false_if_not_found(self, mock_get_connection):
        """delete_campaign returns False when campaign does not exist"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # not found

        result = delete_campaign(999)

        self.assertFalse(result)

    @patch('app.services.crud_service.get_connection')
    def test_restore_sets_is_deleted_to_zero(self, mock_get_connection):
        """restore_campaign updates is_deleted=0"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # deleted campaign found

        result = restore_campaign(1)

        self.assertTrue(result)
        executed = [str(c) for c in mock_cursor.execute.call_args_list]
        self.assertTrue(any('is_deleted = 0' in c for c in executed))

    @patch('app.services.crud_service.get_connection')
    def test_restore_returns_false_if_not_deleted(self, mock_get_connection):
        """restore_campaign returns False when campaign is not in deleted state"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # is_deleted=1 check fails

        result = restore_campaign(42)

        self.assertFalse(result)


class TestAuditService(unittest.TestCase):
    """Test audit log service"""

    @patch('app.services.audit_service.get_connection')
    def test_log_action_inserts_row(self, mock_get_connection):
        """log_action writes an INSERT into audit_logs"""
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn

        log_action(user_id=1, username="admin", action="create", campaign_id=5)

        mock_conn.execute.assert_called_once()
        call_args = str(mock_conn.execute.call_args)
        self.assertIn("INSERT", call_args)
        self.assertIn("audit_logs", call_args)

    @patch('app.services.audit_service.get_connection')
    def test_log_action_silent_on_db_error(self, mock_get_connection):
        """log_action does not raise even if the DB write fails"""
        mock_get_connection.side_effect = Exception("DB unavailable")

        try:
            log_action(user_id=1, username="admin", action="delete", campaign_id=3)
        except Exception:
            self.fail("log_action raised an exception on DB error")

    @patch('app.services.audit_service.get_connection')
    def test_get_audit_logs_returns_paginated(self, mock_get_connection):
        """get_audit_logs returns correct pagination metadata"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (3,)
        mock_cursor.fetchall.return_value = [
            {'id': 3, 'user_id': 1, 'username': 'admin', 'action': 'delete', 'campaign_id': 2, 'timestamp': '2026-06-30'},
            {'id': 2, 'user_id': 1, 'username': 'admin', 'action': 'update', 'campaign_id': 1, 'timestamp': '2026-06-29'},
        ]

        result = get_audit_logs(page=1, limit=50)

        self.assertEqual(result['total'], 3)
        self.assertEqual(result['page'], 1)
        self.assertEqual(len(result['logs']), 2)
        self.assertFalse(result['has_prev'])


class TestPasswordStrength(unittest.TestCase):
    """Test password strength validation on UserCreate"""

    def _make_user(self, password):
        return UserCreate(
            username="testuser",
            email="test@example.com",
            password=password
        )

    def test_strong_password_accepted(self):
        """A password meeting all rules is accepted"""
        user = self._make_user("Secure1@pass")
        self.assertEqual(user.password, "Secure1@pass")

    def test_missing_uppercase_rejected(self):
        """Password without uppercase raises ValueError"""
        with self.assertRaises(Exception):
            self._make_user("secure1@pass")

    def test_missing_digit_rejected(self):
        """Password without digit raises ValueError"""
        with self.assertRaises(Exception):
            self._make_user("Secure@pass")

    def test_missing_special_char_rejected(self):
        """Password without special character raises ValueError"""
        with self.assertRaises(Exception):
            self._make_user("Secure1pass")

    def test_too_short_rejected(self):
        """Password shorter than 8 chars raises ValueError"""
        with self.assertRaises(Exception):
            self._make_user("S1@x")

    def test_all_rules_met_various_specials(self):
        """Different special characters are accepted"""
        for special in ['@', '$', '!', '%', '*', '?', '&', '#']:
            user = self._make_user(f"Password1{special}")
            self.assertIsNotNone(user)


class TestAccountLockout(unittest.TestCase):
    """Test account lockout logic in AuthService"""

    @patch('app.services.auth_service.UserService.get_user_by_username')
    @patch('app.services.auth_service.AuthService._reset_failed_attempts')
    def test_locked_account_raises_exception(self, mock_reset, mock_get_user):
        """Login raises AccountLockedException when locked_until is in the future"""
        from datetime import datetime, timedelta
        future = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'is_active': True,
            'hashed_password': 'hash', 'locked_until': future,
            'failed_attempts': 5
        }

        with self.assertRaises(AccountLockedException):
            AuthService.authenticate_user("user", "wrongpass")

    @patch('app.services.auth_service.UserService.get_user_by_username')
    @patch('app.services.auth_service.AuthService._reset_failed_attempts')
    @patch('app.services.auth_service.AuthService.verify_password', return_value=True)
    def test_expired_lock_resets_and_allows_login(self, mock_verify, mock_reset, mock_get_user):
        """Expired lock is cleared and login succeeds with correct password"""
        from datetime import datetime, timedelta
        past = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'is_active': True,
            'hashed_password': 'hash', 'locked_until': past,
            'failed_attempts': 5
        }

        success, user = AuthService.authenticate_user("user", "Correct1@pass")

        self.assertTrue(success)
        mock_reset.assert_called()

    @patch('app.services.auth_service.UserService.get_user_by_username')
    @patch('app.services.auth_service.AuthService._increment_failed_attempts')
    @patch('app.services.auth_service.AuthService.verify_password', return_value=False)
    def test_wrong_password_increments_counter(self, mock_verify, mock_increment, mock_get_user):
        """Failed login increments the failed attempts counter"""
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'is_active': True,
            'hashed_password': 'hash', 'locked_until': None,
            'failed_attempts': 2
        }

        success, user = AuthService.authenticate_user("user", "wrongpass")

        self.assertFalse(success)
        mock_increment.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
