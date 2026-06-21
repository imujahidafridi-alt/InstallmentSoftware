import pytest
from PyQt6.QtCore import Qt
from src.views.due_overdue_view import DueOverdueView
from src.config import ConfigManager

def test_due_overdue_view_init(qtbot):
    # Test instantiation of DueOverdueView
    view = DueOverdueView()
    qtbot.addWidget(view)

    # Verify widget components exist
    assert view.tab_widget is not None
    assert view.tab_widget.count() == 2
    assert view.tab_widget.tabText(0) == "Overdue Installments"
    assert view.tab_widget.tabText(1) == "Upcoming Due Schedules"

    assert view.table_overdue is not None
    assert view.table_due is not None

    # Verify horizontal header alignment configuration (left-aligned)
    align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    assert view.table_overdue.horizontalHeader().defaultAlignment() == align_left
    assert view.table_due.horizontalHeader().defaultAlignment() == align_left


def test_due_overdue_view_population(qtbot):
    view = DueOverdueView()
    qtbot.addWidget(view)

    # Mock tracking data
    mock_tracking = {
        "due_today": [
            {
                "customer_name": "Test Customer",
                "device_name": "Test Device",
                "due_date": "2026-06-18",
                "outstanding_amount": 5000.0,
                "sale_id": "test-sale-1"
            }
        ],
        "due_next_7_days": [
            {
                "customer_name": "Next 7 Days Customer",
                "device_name": "Next 7 Days Device",
                "due_date": "2026-06-25",
                "outstanding_amount": 3000.0,
                "sale_id": "test-sale-3"
            }
        ],
        "overdue_1_30": [
            {
                "customer_name": "Overdue Customer",
                "device_name": "Overdue Device",
                "due_date": "2026-05-18",
                "days_overdue": 30,
                "outstanding_amount": 7500.0,
                "sale_id": "test-sale-2"
            }
        ]
    }

    # Populate tables
    view.tracking_data = mock_tracking
    view.update_due_table()
    view.update_overdue_table()

    # Assert default filter ("Due Today") rows are added correctly
    assert view.table_due.rowCount() == 1
    assert view.table_due.item(0, 0).text() == "1"
    assert view.table_due.item(0, 1).text() == "Test Customer"
    assert view.table_due.item(0, 4).text() == ConfigManager.format_currency(5000.0)

    # Switch filter to "Next 7 Days"
    view.cmb_due_filter.setCurrentText("Next 7 Days")
    # Assert "Next 7 Days" rows are updated correctly
    assert view.table_due.rowCount() == 1
    assert view.table_due.item(0, 0).text() == "1"
    assert view.table_due.item(0, 1).text() == "Next 7 Days Customer"
    assert view.table_due.item(0, 4).text() == ConfigManager.format_currency(3000.0)

    assert view.table_overdue.rowCount() == 1
    assert view.table_overdue.item(0, 0).text() == "1"
    assert view.table_overdue.item(0, 1).text() == "Overdue Customer"
    assert view.table_overdue.item(0, 4).text() == "30 days"
    assert view.table_overdue.item(0, 5).text() == ConfigManager.format_currency(7500.0)
