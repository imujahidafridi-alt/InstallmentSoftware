import pytest
from PyQt6.QtWidgets import QWidget
from src.views.components.q_notification import QNotification

def test_q_notification(qtbot):
    # Setup parent widget
    parent = QWidget()
    qtbot.addWidget(parent)
    parent.resize(800, 600)
    
    # Create notification with type success
    notif_success = QNotification(parent, "Operation completed successfully", type="success", duration=0)
    
    # Verify properties
    assert notif_success.message == "Operation completed successfully"
    assert notif_success.type == "success"
    assert notif_success.lbl_msg.text() == "Operation completed successfully"
    assert notif_success.lbl_icon.text() == "🟢"
    
    # Create notification with type error
    notif_error = QNotification(parent, "An unexpected error occurred", type="error", duration=0)
    
    # Verify properties
    assert notif_error.message == "An unexpected error occurred"
    assert notif_error.type == "error"
    assert notif_error.lbl_msg.text() == "An unexpected error occurred"
    assert notif_error.lbl_icon.text() == "🔴"
    
    # Stacking test
    assert len(QNotification.ACTIVE_NOTIFICATIONS) == 2
    assert QNotification.ACTIVE_NOTIFICATIONS[0] == notif_success
    assert QNotification.ACTIVE_NOTIFICATIONS[1] == notif_error
    
    # Cleanup active stack
    QNotification.ACTIVE_NOTIFICATIONS.clear()
