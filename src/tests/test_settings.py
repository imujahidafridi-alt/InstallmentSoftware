import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QThread
from src.views.settings_view import DatabaseResetWorker

@patch("src.db.supabase_client.get_db")
@patch("src.services.cache_service.CacheService.clear")
@patch("src.services.audit_log_service.AuditLogService.log_action")
def test_database_reset_worker(mock_log, mock_clear_cache, mock_get_db):
    """Verifies that DatabaseResetWorker deletes all tables in the correct order, clears cache, and logs the action."""
    # 1. Setup mock database client
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Track the order of table deletions
    deleted_tables = []
    
    def mock_table(name):
        deleted_tables.append(name)
        mock_query = MagicMock()
        mock_query.delete.return_value = mock_query
        mock_query.neq.return_value = mock_query
        mock_query.execute.return_value = MagicMock()
        return mock_query

    mock_db.table.side_effect = mock_table

    # 2. Instantiate worker and run it synchronously
    worker = DatabaseResetWorker()
    
    # Connect signals to verify they are emitted
    success_emitted = False
    failed_emitted = False
    
    def on_success():
        nonlocal success_emitted
        success_emitted = True
        
    def on_failed(err):
        nonlocal failed_emitted
        failed_emitted = err

    worker.reset_success.connect(on_success)
    worker.reset_failed.connect(on_failed)

    # We mock time.sleep so the test runs instantly
    with patch("time.sleep") as mock_sleep:
        worker.run()

    # 3. Assertions
    assert failed_emitted is False
    assert success_emitted is True
    
    # Verify tables deleted in correct order
    expected_order = [
        "payments",
        "installments",
        "sales",
        "devices",
        "customers",
        "suppliers",
        "audit_logs"
    ]
    assert deleted_tables == expected_order
    
    # Verify cache cleared and action logged
    mock_clear_cache.assert_called_once()
    mock_log.assert_called_once_with("Database wiped and reset completely")
