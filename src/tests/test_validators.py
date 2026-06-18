import pytest
from unittest.mock import MagicMock
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
