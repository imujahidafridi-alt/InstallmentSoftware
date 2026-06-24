from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class SearchSelectWidget(QWidget):
    """
    A premium, reusable inline search-select combobox component.
    Supports both callback-based configuration and class-based inheritance.
    
    Exposes:
        item_selected (pyqtSignal(str)): Emitted with the selected item's ID, or "" when cleared.
    """
    item_selected = pyqtSignal(str)

    _POPUP_ITEM_HEIGHT = 52   # px per row

    def __init__(self, placeholder="Type to search...", filter_callback=None, format_callback=None, parent=None):
        super().__init__(parent)
        self._items: list = []
        self._selected_id: str = ""
        self._placeholder = placeholder
        
        # Configuration Callbacks (Optional - can also subclass and override methods)
        self.filter_callback = filter_callback
        self.format_callback = format_callback
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container frame
        self.container = QFrame()
        self.container.setFixedHeight(36)
        self.container.setObjectName("search_container")
        self.container.setStyleSheet(
            "QFrame#search_container {"
            "  background: #FFFFFF;"
            "  border: 1px solid #CBD5E1;"
            "  border-radius: 6px;"
            "  padding: 0px;"
            "}"
        )
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(10, 0, 10, 0)
        container_layout.setSpacing(6)

        # Search input
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self._placeholder)
        self.txt_search.setStyleSheet(
            "QLineEdit {"
            "  background: transparent;"
            "  border: none;"
            "  font-size: 13px;"
            "  color: #0F172A;"
            "  padding: 0px;"
            "}"
        )
        self.txt_search.textChanged.connect(self._on_text_changed)
        self.txt_search.focusOutEvent = self._on_focus_out
        self.txt_search.focusInEvent = self._on_focus_in
        container_layout.addWidget(self.txt_search, 1)

        # Action Button (Dropdown arrow by default, clear cross when selected)
        self.btn_action = QPushButton("▼")
        self.btn_action.setFixedWidth(24)
        self.btn_action.setFixedHeight(24)
        self.btn_action.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  color: #64748B;"
            "  font-size: 11px;"
            "  font-weight: bold;"
            "  padding: 0px;"
            "}"
            "QPushButton:hover {"
            "  color: #0F172A;"
            "}"
        )
        self.btn_action.clicked.connect(self._on_action_clicked)
        container_layout.addWidget(self.btn_action)

        layout.addWidget(self.container)

        # Popup list (hidden by default)
        self.list_popup = QListWidget()
        self.list_popup.setVisible(False)
        self.list_popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_popup.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_popup.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_popup.setStyleSheet(
            "QListWidget {"
            "  background: #FFFFFF;"
            "  border: 1px solid #CBD5E1;"
            "  border-radius: 6px;"
            "  outline: none;"
            "}"
            "QListWidget::item {"
            "  padding: 8px 12px;"
            "  border-bottom: 1px solid #F1F5F9;"
            "  color: #0F172A;"
            "  font-size: 12px;"
            "}"
            "QListWidget::item:selected, QListWidget::item:hover {"
            "  background: #EFF6FF;"
            "  color: #1D4ED8;"
            "}"
        )
        self.list_popup.itemClicked.connect(self._on_item_clicked)

        # Debounce timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._filter_popup)

    def _on_focus_in(self, event):
        if not self._selected_id:
            self.container.setStyleSheet(
                "QFrame#search_container {"
                "  background: #FFFFFF;"
                "  border: 1.5px solid #3B82F6;"
                "  border-radius: 6px;"
                "  padding: 0px;"
                "}"
            )
        QLineEdit.focusInEvent(self.txt_search, event)

    def _on_focus_out(self, event):
        QTimer.singleShot(200, self._hide_popup)
        if not self._selected_id:
            self.container.setStyleSheet(
                "QFrame#search_container {"
                "  background: #FFFFFF;"
                "  border: 1px solid #CBD5E1;"
                "  border-radius: 6px;"
                "  padding: 0px;"
                "}"
            )
        QLineEdit.focusOutEvent(self.txt_search, event)

    # ── Public API ─────────────────────────────────────────────────────

    def set_items(self, items: list):
        """Populates the items list used for search filtering."""
        self._items = items

    def selected_id(self) -> str:
        """Returns the ID of the selected item, or empty string."""
        return self._selected_id

    def set_selection(self, item_id: str, display_text: str):
        """Programmatically sets the active selection."""
        self._selected_id = item_id
        
        self.txt_search.blockSignals(True)
        self.txt_search.setText(display_text)
        self.txt_search.setReadOnly(True)
        self.txt_search.blockSignals(False)

        # Apply selected visuals
        self.txt_search.setStyleSheet(
            "QLineEdit {"
            "  background: transparent;"
            "  border: none;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  color: #15803D;"
            "  padding: 0px;"
            "}"
        )
        self.container.setStyleSheet(
            "QFrame#search_container {"
            "  background: #F0FDF4;"
            "  border: 1.5px solid #10B981;"
            "  border-radius: 6px;"
            "  padding: 0px;"
            "}"
        )
        self.btn_action.setText("×")
        self.btn_action.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  color: #EF4444;"
            "  font-size: 16px;"
            "  font-weight: bold;"
            "  padding: 0px;"
            "}"
            "QPushButton:hover {"
            "  color: #B91C1C;"
            "}"
        )
        self._hide_popup()

    def clear_selection(self):
        """Clears the active selection and resets style back to default."""
        self._selected_id = ""
        
        self.txt_search.blockSignals(True)
        self.txt_search.clear()
        self.txt_search.setReadOnly(False)
        self.txt_search.blockSignals(False)
        
        self.txt_search.setStyleSheet(
            "QLineEdit {"
            "  background: transparent;"
            "  border: none;"
            "  font-size: 13px;"
            "  color: #0F172A;"
            "  padding: 0px;"
            "}"
        )
        self.container.setStyleSheet(
            "QFrame#search_container {"
            "  background: #FFFFFF;"
            "  border: 1px solid #CBD5E1;"
            "  border-radius: 6px;"
            "  padding: 0px;"
            "}"
        )
        self.btn_action.setText("▼")
        self.btn_action.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  color: #64748B;"
            "  font-size: 11px;"
            "  font-weight: bold;"
            "  padding: 0px;"
            "}"
            "QPushButton:hover {"
            "  color: #0F172A;"
            "}"
        )
        self._hide_popup()

    # ── Extension Points / Customization ───────────────────────────────

    def filter_items(self, query: str, items: list) -> list:
        """
        Filters items based on search query. 
        Can be overridden in a subclass or configured via filter_callback.
        """
        if self.filter_callback:
            return self.filter_callback(query, items)
        
        # Fallback default filter: match query in any string representation of dictionary values
        if not query:
            return items
        matches = []
        for item in items:
            if isinstance(item, dict):
                content = " ".join(str(v).lower() for v in item.values())
                if query in content:
                    matches.append(item)
            elif query in str(item).lower():
                matches.append(item)
        return matches

    def format_item(self, item) -> tuple:
        """
        Formats an item for listing and identification.
        Should return a tuple of: (display_text, tooltip_text, item_id)
        Can be overridden in a subclass or configured via format_callback.
        """
        if self.format_callback:
            return self.format_callback(item)
        
        # Fallback default formatter
        if isinstance(item, dict):
            name = item.get("name", "Unnamed")
            item_id = item.get("id", "")
            return name, f"ID: {item_id}", item_id
        return str(item), str(item), str(item)

    # ── Internals ──────────────────────────────────────────────────────

    def _on_text_changed(self, text: str):
        if not self.txt_search.isReadOnly():
            self._selected_id = ""
            self._timer.stop()
            self._timer.start(200)

    def _on_action_clicked(self):
        if self._selected_id:
            self.clear_selection()
            self.item_selected.emit("")
        else:
            if self.list_popup.isVisible():
                self._hide_popup()
            else:
                self.txt_search.setFocus()
                self._filter_popup()

    def _filter_popup(self):
        query = self.txt_search.text().strip().lower()
        self.list_popup.clear()

        # Perform filtering (callback or overridden method)
        matches = self.filter_items(query, self._items)

        if not matches:
            self._hide_popup()
            return

        for item_data in matches[:20]:   # Cap at 20 suggestions
            display_text, tooltip_text, item_id = self.format_item(item_data)
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, item_id)
            if tooltip_text:
                item.setToolTip(tooltip_text)
            self.list_popup.addItem(item)

        win = self.window()
        if win:
            if self.list_popup.parent() != win:
                self.list_popup.setParent(win)
            pos = self.container.mapTo(win, self.container.rect().bottomLeft())
            visible_rows = min(len(matches), 5)
            self.list_popup.setGeometry(
                pos.x(),
                pos.y() + 2,
                self.container.width(),
                visible_rows * self._POPUP_ITEM_HEIGHT
            )
            self.list_popup.raise_()
            self.list_popup.show()

    def _on_item_clicked(self, item: QListWidgetItem):
        item_id = item.data(Qt.ItemDataRole.UserRole)
        # Extract name part (before first '  /  ' if present) to display cleanly in input
        display_text = item.text().split("  /  ")[0]
        
        self.set_selection(item_id, display_text)
        self.item_selected.emit(item_id)

    def _hide_popup(self):
        self.list_popup.setVisible(False)
        self.list_popup.clear()
