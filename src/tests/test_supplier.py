import pytest
from unittest.mock import MagicMock, patch
from src.viewmodels.supplier_viewmodel import SupplierViewModel
from src.viewmodels.device_viewmodel import DeviceViewModel

def test_supplier_data_validation():
    vm = SupplierViewModel()
    
    # 1. Valid Supplier
    is_valid, errors = vm.validate_supplier_data(
        name="Khalid Electronics",
        mobile="03001234567"
    )
    assert is_valid is True
    assert len(errors) == 0
    
    # 2. Blank Name
    is_valid, errors = vm.validate_supplier_data(
        name="   ",
        mobile="03001234567"
    )
    assert is_valid is False
    assert any("Name is required" in err for err in errors)
    
    # 3. Invalid Mobile Format (too short)
    is_valid, errors = vm.validate_supplier_data(
        name="Khalid Electronics",
        mobile="0300123"
    )
    assert is_valid is False
    assert any("Mobile Number must be in format" in err for err in errors)
    
    # 4. Invalid Mobile Prefix (not starting with 03)
    is_valid, errors = vm.validate_supplier_data(
        name="Khalid Electronics",
        mobile="04001234567"
    )
    assert is_valid is False
    assert any("Mobile Number must be in format" in err for err in errors)

@patch("src.services.cache_service.CacheService.clear")
@patch("src.services.audit_log_service.AuditLogService.log_action")
def test_supplier_crud(mock_log, mock_clear_cache):
    vm = SupplierViewModel()
    vm.repo = MagicMock()
    
    # 1. Register Supplier Success
    vm.repo.create.side_effect = lambda data: {**data, "id": "supp-123"}
    res = vm.register_supplier(
        name="Al-Noor Traders",
        contact_person="Bashir Ahmad",
        mobile="03217654321",
        address="Hall Road, Lahore",
        remarks="N/A"
    )
    
    assert res["id"] == "supp-123"
    assert res["name"] == "Al-Noor Traders"
    vm.repo.create.assert_called_once()
    mock_clear_cache.assert_called_once()
    mock_log.assert_called_once()
    
    # Reset mocks for update
    vm.repo.reset_mock()
    mock_clear_cache.reset_mock()
    mock_log.reset_mock()
    
    # 2. Update Supplier Success
    vm.repo.update.side_effect = lambda supp_id, data: {**data, "id": supp_id}
    res_upd = vm.update_supplier(
        supplier_id="supp-123",
        name="Al-Noor Traders Updated",
        contact_person="Bashir Ahmad",
        mobile="03217654321",
        address="Hall Road, Lahore",
        remarks="Active Remarks"
    )
    
    assert res_upd["id"] == "supp-123"
    assert res_upd["name"] == "Al-Noor Traders Updated"
    vm.repo.update.assert_called_once_with("supp-123", {
        "name": "Al-Noor Traders Updated",
        "contact_person": "Bashir Ahmad",
        "mobile": "03217654321",
        "address": "Hall Road, Lahore",
        "remarks": "Active Remarks"
    })
    mock_clear_cache.assert_called_once()
    mock_log.assert_called_once()
    
    # Reset mocks for delete
    vm.repo.reset_mock()
    mock_clear_cache.reset_mock()
    mock_log.reset_mock()
    
    # 3. Delete Supplier Success
    vm.repo.get_by_id.return_value = {"id": "supp-123", "name": "Al-Noor Traders"}
    vm.delete_supplier("supp-123")
    
    vm.repo.delete.assert_called_once_with("supp-123")
    mock_clear_cache.assert_called_once()
    mock_log.assert_called_once()

def test_device_with_supplier():
    vm = DeviceViewModel()
    vm.repo = MagicMock()
    vm.repo.check_imei_exists.return_value = False
    vm.repo.create.side_effect = lambda data: {**data, "id": "dev-456"}
    
    with patch("src.services.cache_service.CacheService.clear") as mock_clear:
        res = vm.register_device(
            name="Galaxy S24",
            brand="Samsung",
            model="SM-G998",
            ram="12 GB",
            rom="256 GB",
            sim_type=1,
            imeis=["351234567890123", "", "", ""],
            supplier_id="supp-123"
        )
        
        assert res["id"] == "dev-456"
        assert res["supplier_id"] == "supp-123"
        vm.repo.create.assert_called_once_with({
            "name": "Galaxy S24",
            "brand": "Samsung",
            "model": "SM-G998",
            "ram": "12 GB",
            "rom": "256 GB",
            "sim_type": 1,
            "imei_1": "351234567890123",
            "imei_2": None,
            "imei_3": None,
            "imei_4": None,
            "supplier_id": "supp-123"
        })
