import os
import json
import pytest
from unittest.mock import MagicMock
from src.services.cache_service import CacheService, CACHE_FILE

def test_cache_set_and_get():
    # Clear cache before starting
    CacheService.clear()
    
    CacheService.set("test_key", "test_value")
    assert CacheService.get("test_key") == "test_value"
    
    # Save complex types
    complex_data = {"a": [1, 2, 3], "b": {"c": True}}
    CacheService.set("complex", complex_data)
    assert CacheService.get("complex") == complex_data
    
    # Check fallback value
    assert CacheService.get("nonexistent_key", "default") == "default"
    
    # Clean up
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

def test_cache_clear():
    CacheService.set("k1", 1)
    CacheService.set("k2", 2)
    CacheService.clear()
    
    assert CacheService.get("k1") is None
    assert CacheService.get("k2") is None
    
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

def test_check_and_update_state():
    CacheService.clear()
    
    # Mock supabase client and query execution
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_order = MagicMock()
    mock_limit = MagicMock()
    
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.order.return_value = mock_order
    mock_order.limit.return_value = mock_limit
    
    # Mock response
    mock_response = MagicMock()
    mock_response.count = 5
    mock_response.data = [{"created_at": "2026-06-17T12:00:00Z"}]
    mock_limit.execute.return_value = mock_response
    
    # First check: cache is empty, should return True (changes detected)
    changed = CacheService.check_and_update_state("customers", mock_client)
    assert changed is True
    
    # Second check: with same database response, should return False (no changes)
    changed = CacheService.check_and_update_state("customers", mock_client)
    assert changed is False
    
    # Mock database update (count changes)
    mock_response_updated = MagicMock()
    mock_response_updated.count = 6
    mock_response_updated.data = [{"created_at": "2026-06-17T13:00:00Z"}]
    mock_limit.execute.return_value = mock_response_updated
    
    # Third check: should return True (changes detected)
    changed = CacheService.check_and_update_state("customers", mock_client)
    assert changed is True
    
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
