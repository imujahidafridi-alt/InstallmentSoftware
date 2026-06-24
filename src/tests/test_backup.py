import os
import zipfile
import json
import pytest
from unittest.mock import MagicMock, patch
from src.services.backup_service import BackupService

@pytest.fixture
def mock_db():
    with patch('src.services.backup_service.get_db') as mock_get_db:
        mock_client = MagicMock()
        mock_get_db.return_value = mock_client
        
        # Setup mock responses for all tables
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[
            {"id": "1", "name": "Test Entry", "created_at": "2026-06-24"}
        ])
        
        mock_client.table.return_value = mock_query
        yield mock_client

def test_backup_zip_creation(mock_db):
    """Verifies that the backup service queries Supabase tables and packages them into a valid ZIP archive."""
    zip_path, zip_filename = BackupService.create_database_backup()
    
    try:
        assert os.path.exists(zip_path)
        assert zip_filename.startswith("AMC_Backup_")
        assert zip_filename.endswith(".zip")
        
        # Verify ZIP contains all expected json sheets
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            names = zip_file.namelist()
            expected_tables = ["suppliers.json", "customers.json", "devices.json", "sales.json", "installments.json", "payments.json", "audit_logs.json"]
            for table in expected_tables:
                assert table in names
                
            # Verify contents of one of the files
            with zip_file.open("customers.json") as f:
                data = json.loads(f.read().decode('utf-8'))
                assert len(data) == 1
                assert data[0]["id"] == "1"
                assert data[0]["name"] == "Test Entry"
                
    finally:
        # Clean up
        if os.path.exists(zip_path):
            os.remove(zip_path)

def test_is_google_configured():
    """Checks that the config checker correctly returns configuration status based on file presence."""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        assert BackupService.is_google_configured() is True
        
        mock_exists.return_value = False
        assert BackupService.is_google_configured() is False

def test_disconnect_google():
    """Verifies that disconnecting Google successfully deletes the token file from disk."""
    with patch('os.path.exists') as mock_exists, patch('os.remove') as mock_remove:
        mock_exists.return_value = True
        BackupService.disconnect_google()
        mock_remove.assert_called_once()
