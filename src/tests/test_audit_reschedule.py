import pytest
from unittest.mock import MagicMock, patch
from src.services.audit_log_service import AuditLogService
from src.viewmodels.customer_viewmodel import CustomerViewModel
from src.viewmodels.installment_viewmodel import InstallmentViewModel

def test_audit_log_service_ip_fetching():
    # Test fallback to local IP when network request fails
    with patch("urllib.request.urlopen", side_effect=Exception("Timeout")):
        ip = AuditLogService.get_public_ip()
        assert ip != ""
        # Check it is a valid string/IP representation
        assert len(ip) > 0

def test_customer_viewmodel_update():
    vm = CustomerViewModel()
    vm.repo = MagicMock()
    vm.repo.update.return_value = {
        "id": "cust-1",
        "name": "Ali Raza",
        "father_name": "Muhammad Raza",
        "mobile": "03001234567"
    }

    # Verify update runs and calls logging internally
    with patch("src.services.audit_log_service.AuditLogService.log_action") as mock_log:
        result = vm.update_customer(
            customer_id="cust-1",
            name="Ali Raza",
            father_name="Muhammad Raza",
            mobile="03001234567",
            address="Lahore",
            remarks="VIP Customer"
        )
        assert result["name"] == "Ali Raza"
        vm.repo.update.assert_called_once()
        mock_log.assert_called_once()

def test_installment_rescheduling_validation():
    vm = InstallmentViewModel()
    vm.inst_repo = MagicMock()
    vm.sale_repo = MagicMock()

    # Verify invalid months count throws ValueError
    with pytest.raises(ValueError, match="Reschedule duration must be at least 1 month"):
        vm.reschedule_installments("sale-1", "2026-07-01", 0)

    # Verify successful reschedule triggers repo and logging
    vm.inst_repo.reschedule_schedule.return_value = True
    vm.sale_repo.get_by_id.return_value = {
        "id": "sale-1",
        "customers": {"name": "Test Cust"},
        "devices": {"brand": "Samsung", "model": "S24"}
    }

    with patch("src.services.audit_log_service.AuditLogService.log_action") as mock_log:
        success = vm.reschedule_installments("sale-1", "2026-07-01", 6)
        assert success is True
        vm.inst_repo.reschedule_schedule.assert_called_once_with("sale-1", "2026-07-01", 6)
        mock_log.assert_called_once()

def test_customer_reminders_exclusion():
    from datetime import date
    today_str = date.today().strftime("%Y-%m-%d")
    
    vm = InstallmentViewModel()
    vm.inst_repo = MagicMock()
    vm.pay_repo = MagicMock()
    
    # Mock database call return list
    vm.inst_repo.db.table.return_value.select.return_value.neq.return_value.order.return_value.execute.return_value.data = [
        {
            "id": "inst-1",
            "sale_id": "sale-1",
            "due_date": today_str,
            "amount": "5000",
            "status": "Pending",
            "sales": {
                "customers": {
                    "name": "Enabled Cust",
                    "mobile": "03001234567",
                    "reminders_enabled": True
                },
                "devices": {
                    "name": "Device 1"
                }
            }
        },
        {
            "id": "inst-2",
            "sale_id": "sale-2",
            "due_date": today_str,
            "amount": "6000",
            "status": "Pending",
            "sales": {
                "customers": {
                    "name": "Disabled Cust",
                    "mobile": "03007654321",
                    "reminders_enabled": False
                },
                "devices": {
                    "name": "Device 2"
                }
            }
        }
    ]
    
    # Mock payments retrieval
    vm.pay_repo.db.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
    
    lists = vm.get_due_tracking_lists()
    
    # Check that ONLY the customer with reminders_enabled=True is returned
    due_today_names = [item["customer_name"] for item in lists["due_today"]]
    assert "Enabled Cust" in due_today_names
    assert "Disabled Cust" not in due_today_names

