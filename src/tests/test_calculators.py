import pytest
from src.viewmodels.sale_viewmodel import SaleViewModel

def test_calculate_margin():
    vm = SaleViewModel()
    
    # Standard Case
    margin, pct = vm.calculate_margin(50000.0, 40000.0)
    assert margin == 10000.0
    assert pct == 25.0

    # Margin 0 Case
    margin, pct = vm.calculate_margin(30000.0, 30000.0)
    assert margin == 0.0
    assert pct == 0.0

    # Negative margin (Selling < Cost)
    margin, pct = vm.calculate_margin(35000.0, 40000.0)
    assert margin == -5000.0
    assert pct == -12.5

def test_calculate_monthly_installment():
    vm = SaleViewModel()
    
    # Standard Case: 60,000 price, 10,000 down, 10 months duration = 5,000 monthly
    inst = vm.calculate_monthly_installment(60000.0, 10000.0, 10)
    assert inst == 5000.0

    # Zero remaining balance
    inst = vm.calculate_monthly_installment(15000.0, 15000.0, 12)
    assert inst == 0.0

    # Division by zero safety
    inst = vm.calculate_monthly_installment(50000.0, 10000.0, 0)
    assert inst == 0.0

    # Duration negative duration check
    inst = vm.calculate_monthly_installment(50000.0, 10000.0, -5)
    assert inst == 0.0
