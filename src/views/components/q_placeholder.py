from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

def show_empty_table_message(table: QTableWidget, message: str):
    """
    Spans a single row across all columns of a QTableWidget to show a styled placeholder message
    when no data records are found or available.
    """
    table.setRowCount(0)
    table.insertRow(0)
    table.setSpan(0, 0, 1, table.columnCount())
    
    item = QTableWidgetItem(message)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable, non-editable
    item.setForeground(QColor("#64748B"))  # Slate color for secondary text
    
    table.setItem(0, 0, item)
    table.setRowHeight(0, 60)
