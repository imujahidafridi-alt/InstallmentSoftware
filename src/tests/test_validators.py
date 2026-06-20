import pytest
from unittest.mock import MagicMock, patch
from src.viewmodels.customer_viewmodel import CustomerViewModel
from src.viewmodels.device_viewmodel import DeviceViewModel

def test_customer_data_validation():
    vm = CustomerViewModel()
    # Mock repo to avoid database calls
    vm.repo = MagicMock()
    
    # Valid customer
    is_valid, errors = vm.validate_customer_data(
        name="John Doe",
        father_name="Senior Doe",
        mobile="03001234567"
    )
    assert is_valid is True
    assert len(errors) == 0

    # Invalid Mobile prefix
    is_valid, errors = vm.validate_customer_data(
        name="John Doe",
        father_name="Senior Doe",
        mobile="04001234567" # starts with 04 instead of 03
    )
    assert is_valid is False
    assert any("Mobile Number must be in format" in err for err in errors)

def test_device_imei_validation():
    vm = DeviceViewModel()
    # Mock repo to return no duplicates found in DB
    vm.repo = MagicMock()
    vm.repo.check_imei_exists.return_value = False

    # Valid Dual SIM IMEIs
    is_valid, errors = vm.validate_device_data(
        name="iPhone 15",
        brand="Apple",
        model="A3090",
        ram="8 GB",
        rom="256 GB",
        sim_type=2,
        imeis=["123456789012345", "987654321098765", "", ""]
    )
    assert is_valid is True
    assert len(errors) == 0

    # Short IMEI format (14 digits)
    is_valid, errors = vm.validate_device_data(
        name="iPhone 15",
        brand="Apple",
        model="A3090",
        ram="8 GB",
        rom="256 GB",
        sim_type=2,
        imeis=["12345678901234", "987654321098765", "", ""] # imei 1 is 14 digits
    )
    assert is_valid is False
    assert any("must be exactly 15 digits" in err for err in errors)

    # Non-numeric IMEI check
    is_valid, errors = vm.validate_device_data(
        name="iPhone 15",
        brand="Apple",
        model="A3090",
        ram="8 GB",
        rom="256 GB",
        sim_type=1,
        imeis=["1234567890ABCDE", "", "", ""] # contains alphabets
    )
    assert is_valid is False
    assert any("must be exactly 15 digits" in err for err in errors)

def test_device_optional_fields():
    vm = DeviceViewModel()
    vm.repo = MagicMock()
    vm.repo.check_imei_exists.return_value = False

    # Brand, Model, and IMEIs are optional now
    is_valid, errors = vm.validate_device_data(
        name="iPhone 15",
        brand="",  # empty
        model="",  # empty
        ram="8 GB",
        rom="256 GB",
        sim_type=1,
        imeis=["", "", "", ""]  # all empty
    )
    assert is_valid is True
    assert len(errors) == 0


def test_device_auto_generate_imei():
    vm = DeviceViewModel()
    vm.repo = MagicMock()
    vm.repo.check_imei_exists.return_value = False
    vm.repo.create.side_effect = lambda data: data

    result = vm.register_device(
        name="iPhone 15",
        brand="",
        model="",
        ram="8 GB",
        rom="256 GB",
        sim_type=1,
        imeis=["", "", "", ""]
    )
    
    assert result["imei_1"].startswith("00")
    assert len(result["imei_1"]) == 15


def test_device_update_safe():
    vm = DeviceViewModel()
    vm.repo = MagicMock()
    
    # 1. Test update when device is already sold
    with patch.object(vm, "is_device_sold", return_value=True):
        with pytest.raises(ValueError, match="already sold and cannot be edited"):
            vm.update_device("dev-1", "iPhone 15", "Apple", "Model X", "8 GB", "256 GB", 1, ["", "", "", ""])

    # 2. Test update success when device is unsold
    vm.repo.check_imei_exists.return_value = False
    vm.repo.update.side_effect = lambda dev_id, data: {**data, "id": dev_id}
    
    with patch.object(vm, "is_device_sold", return_value=False):
        with patch("src.services.audit_log_service.AuditLogService.log_action") as mock_log:
            result = vm.update_device("dev-1", "iPhone 15", "Apple", "Model X", "8 GB", "256 GB", 1, ["123456789012345", "", "", ""])
            assert result["id"] == "dev-1"
            assert result["name"] == "iPhone 15"
            assert result["imei_1"] == "123456789012345"
            vm.repo.update.assert_called_once()
            mock_log.assert_called_once()


def test_device_delete_safe():
    vm = DeviceViewModel()
    vm.repo = MagicMock()
    
    # 1. Test delete when device is already sold
    with patch.object(vm, "is_device_sold", return_value=True):
        with pytest.raises(ValueError, match="already sold and cannot be deleted"):
            vm.delete_device("dev-1")

    # 2. Test delete success when device is unsold
    with patch.object(vm, "is_device_sold", return_value=False):
        with patch("src.services.audit_log_service.AuditLogService.log_action") as mock_log:
            success = vm.delete_device("dev-1")
            assert success is True
            vm.repo.delete.assert_called_once_with("dev-1")
            mock_log.assert_called_once()
