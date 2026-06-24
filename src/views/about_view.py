import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QDialog, QTextBrowser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Title
        lbl_title = QLabel("About System")
        lbl_title.setObjectName("lbl_title")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E293B;")
        main_layout.addWidget(lbl_title)

        # Centered Container Card
        center_card = QFrame()
        center_card.setObjectName("about_center_card")
        center_card.setStyleSheet("QFrame#about_center_card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }")
        
        card_layout = QVBoxLayout(center_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Header (Logo & Title)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # Logo
        lbl_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_logo.setPixmap(scaled_pixmap)
        else:
            lbl_logo.setText("AMC")
            lbl_logo.setStyleSheet(
                "font-size: 28px; font-weight: bold; color: #FFFFFF; "
                "background-color: #3B82F6; border-radius: 50px; "
                "min-width: 100px; max-width: 100px; min-height: 100px; max-height: 100px; "
                "qproperty-alignment: AlignCenter;"
            )
        header_layout.addWidget(lbl_logo)

        # Branding Details
        brand_info_layout = QVBoxLayout()
        brand_info_layout.setSpacing(4)
        
        lbl_app_name = QLabel("EasyQist")
        lbl_app_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #0F172A;")
        
        lbl_sub = QLabel("Device Installment Management System")
        lbl_sub.setStyleSheet("font-size: 14px; font-weight: 500; color: #475569;")
        
        lbl_agency = QLabel("A product of Afridi Labz")
        lbl_agency.setStyleSheet("font-size: 13px; font-weight: bold; color: #2563EB;")
        
        lbl_version = QLabel("Enterprise Edition — Version 1.2.0-stable (Release 2026)")
        lbl_version.setStyleSheet("font-size: 12px; color: #64748B;")

        brand_info_layout.addWidget(lbl_app_name)
        brand_info_layout.addWidget(lbl_sub)
        brand_info_layout.addWidget(lbl_agency)
        brand_info_layout.addWidget(lbl_version)
        brand_info_layout.addStretch()


        header_layout.addLayout(brand_info_layout)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)

        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        card_layout.addWidget(line)

        # 2. Main Content Grid (Two Columns: Specs & Legal / Developer Info)
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(24)

        # Left Column: Enterprise Specifications & Security
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        lbl_spec_title = QLabel("System Specifications")
        lbl_spec_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-bottom: 4px;")
        left_col.addWidget(lbl_spec_title)

        spec_box = QFrame()
        spec_box.setObjectName("about_spec_box")
        spec_box.setStyleSheet("QFrame#about_spec_box { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }")
        spec_layout = QVBoxLayout(spec_box)
        spec_layout.setContentsMargins(12, 12, 12, 12)
        spec_layout.setSpacing(6)

        specs = [
            ("Core Framework", "Python 3.11 / PyQt6"),
            ("Database Engine", "Supabase Cloud Database (PostgreSQL)"),
            ("ORM Mapper", "Drizzle Kit Schema Sync"),
            ("Security Model", "SSL-TLS Transits & Row-Level Security (RLS)"),
            ("Performance Caching", "Local Cache Synchronization Engine"),
            ("Environment Status", "Fully Production Operational")
        ]

        for title, desc in specs:
            row = QHBoxLayout()
            lbl_key = QLabel(f"{title}:")
            lbl_key.setStyleSheet("font-weight: 600; color: #475569; min-width: 140px;")
            lbl_val = QLabel(desc)
            lbl_val.setStyleSheet("color: #0F172A;")
            row.addWidget(lbl_key)
            row.addWidget(lbl_val)
            row.addStretch()
            spec_layout.addLayout(row)

        left_col.addWidget(spec_box)
        left_col.addStretch()
        grid_layout.addLayout(left_col, 1)

        # Right Column: Developer Info & Copyright Claims
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        lbl_legal_title = QLabel("Developer & Legal Info")
        lbl_legal_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-bottom: 4px;")
        right_col.addWidget(lbl_legal_title)

        legal_box = QFrame()
        legal_box.setObjectName("about_legal_box")
        legal_box.setStyleSheet("QFrame#about_legal_box { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }")
        legal_layout = QVBoxLayout(legal_box)
        legal_layout.setContentsMargins(12, 12, 12, 12)
        legal_layout.setSpacing(8)

        # Developer Info
        lbl_agency_header = QLabel("Development Agency:")
        lbl_agency_header.setStyleSheet("font-weight: bold; color: #475569;")
        lbl_agency_name = QLabel("Afridi Labz")
        lbl_agency_name.setStyleSheet("color: #2563EB; font-weight: bold;")

        lbl_dev_header = QLabel("Lead Developer:")
        lbl_dev_header.setStyleSheet("font-weight: bold; color: #475569;")
        lbl_dev_name = QLabel("Mujahid Afridi")
        lbl_dev_name.setStyleSheet("color: #0F172A; font-weight: 500;")


        lbl_support = QLabel("Technical Support Email:")
        lbl_support.setStyleSheet("font-weight: bold; color: #475569;")
        lbl_support_contact = QLabel("imujahidafridi@gmail.com")
        lbl_support_contact.setStyleSheet("color: #3B82F6; text-decoration: underline;")

        lbl_phone_tag = QLabel("Contact Phone:")
        lbl_phone_tag.setStyleSheet("font-weight: bold; color: #475569;")
        lbl_phone_val = QLabel("0313-9330041")
        lbl_phone_val.setStyleSheet("color: #0F172A; font-weight: 500;")

        # Copyright details
        lbl_copyright = QLabel("Copyright & Proprietary License:")
        lbl_copyright.setStyleSheet("font-weight: bold; color: #475569;")
        lbl_copyright_text = QLabel(
            "© 2026 Afridi Labz. All Rights Reserved.\n"
            "This software product is protected under international copyright "
            "and intellectual property laws. Unauthorized duplication, reverse engineering, "
            "or redistribution of this application or any part thereof is strictly prohibited "
            "and subject to severe legal penalties."
        )
        lbl_copyright_text.setStyleSheet("color: #64748B; font-size: 11px;")
        lbl_copyright_text.setWordWrap(True)

        legal_layout.addWidget(lbl_agency_header)
        legal_layout.addWidget(lbl_agency_name)
        legal_layout.addWidget(lbl_dev_header)
        legal_layout.addWidget(lbl_dev_name)

        legal_layout.addWidget(lbl_support)
        legal_layout.addWidget(lbl_support_contact)
        legal_layout.addWidget(lbl_phone_tag)
        legal_layout.addWidget(lbl_phone_val)
        legal_layout.addWidget(lbl_copyright)
        legal_layout.addWidget(lbl_copyright_text)

        right_col.addWidget(legal_box)
        right_col.addStretch()
        grid_layout.addLayout(right_col, 1)

        card_layout.addLayout(grid_layout)

        # Footer Actions
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        btn_docs = QPushButton("System Documentation")
        btn_docs.setObjectName("btn_secondary")
        btn_docs.setStyleSheet(
            "background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; "
            "font-weight: 600; padding: 8px 16px; border-radius: 6px;"
        )
        btn_docs.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_license = QPushButton("View End-User License Agreement (EULA)")
        btn_license.setObjectName("btn_secondary")
        btn_license.setStyleSheet(
            "background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; "
            "font-weight: 600; padding: 8px 16px; border-radius: 6px;"
        )
        btn_license.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_docs.clicked.connect(self.show_docs)
        btn_license.clicked.connect(self.show_eula)

        footer_layout.addWidget(btn_docs)
        footer_layout.addWidget(btn_license)
        footer_layout.addStretch()
        
        card_layout.addLayout(footer_layout)

        main_layout.addWidget(center_card)
        main_layout.addStretch()

    def show_eula(self):
        eula_html = """
        <h2>End-User License Agreement (EULA)</h2>
        <p><strong>Effective Date: June 24, 2026</strong></p>
        <p>Please read this End-User License Agreement ("Agreement") carefully before installing or using the <strong>EasyQist - Device Installment Management System</strong> ("Software").</p>
        <p>By installing, copying, or using the Software, you agree to be bound by the terms and conditions of this Agreement. This Software is licensed, not sold, to you by <strong>Afridi Labz</strong> ("Licensor") for use strictly in accordance with the terms of this license.</p>

        <h3>1. License Grant</h3>
        <p>Licensor grants you a revocable, non-exclusive, non-transferable, limited license to download, install, and use the Software solely for your internal business operations, strictly in accordance with the terms of this Agreement.</p>

        <h3>2. Restrictions on Use</h3>
        <p>You agree not to, and you will not permit others to:</p>
        <ul>
            <li>License, sell, rent, lease, assign, distribute, host, outsource, disclose, or otherwise commercially exploit the Software.</li>
            <li>Modify, make derivative works of, disassemble, decrypt, reverse compile, or reverse engineer any part of the Software.</li>
            <li>Remove, alter, or obscure any proprietary notice (including copyright or trademark notices) of Licensor or its affiliates.</li>
        </ul>

        <h3>3. Intellectual Property</h3>
        <p>The Software, including without limitation all copyrights, patents, trademarks, trade secrets, and other intellectual property rights, is and shall remain the sole and exclusive property of <strong>Afridi Labz</strong>. Any feedback, suggestions, or ideas provided by you shall become the sole property of Licensor.</p>

        <h3>4. Third-Party Services</h3>
        <p>The Software utilizes third-party database and synchronization services, including <strong>Supabase (PostgreSQL)</strong>. You acknowledge that availability, speed, and security of data transits are subject to the operational uptime and policies of these third-party providers. Licensor shall not be liable for service disruptions caused by external vendors.</p>

        <h3>5. Limitation of Liability</h3>
        <p>In no event shall <strong>Afridi Labz</strong> or its developers be liable for any special, incidental, indirect, or consequential damages whatsoever (including, but not limited to, damages for loss of profits, loss of data or other information, business interruption, or personal injury) arising out of or in any way related to the use of or inability to use the Software.</p>

        <h3>6. Termination</h3>
        <p>This Agreement shall remain in effect until terminated by you or Licensor. Licensor may, in its sole discretion, at any time and for any or no reason, suspend or terminate this Agreement with or without prior notice.</p>

        <h3>7. Governing Law</h3>
        <p>This Agreement shall be governed by and construed in accordance with the laws of Pakistan, without regard to its conflict of law principles.</p>

        <hr/>
        <p style="color: #64748B; font-size: 11px; text-align: center;">Developed by <strong>Afridi Labz</strong>. For licensing queries, email: <a href="mailto:imujahidafridi@gmail.com">imujahidafridi@gmail.com</a></p>
        """
        dialog = ScrollableTextDialog("End-User License Agreement (EULA)", eula_html, self)
        dialog.exec()

    def show_docs(self):
        docs_html = """
        <h2>System Documentation & Operations Manual</h2>
        <p>Welcome to the <strong>EasyQist - Device Installment Management System</strong>. This documentation serves as a quick-start guide to navigate and operate the application efficiently.</p>

        <h3>1. Executive Dashboard</h3>
        <p>The <strong>Dashboard</strong> acts as your operational control center, providing high-level insights:</p>
        <ul>
            <li><strong>Key Performance Indicators (KPIs)</strong>: Tracks total active customers, outstanding balance, monthly collections, and overdue accounts.</li>
            <li><strong>Installment Completion Rate</strong>: A dynamic pie chart showing the percentage of completed (Paid) vs outstanding (Pending) installments across the entire database.</li>
            <li><strong>Monthly Collection Trend</strong>: A line chart visualizing your revenue streams and collection efficiency month-over-month.</li>
        </ul>

        <h3>2. Inventory & Supplier Management</h3>
        <p>Before recording sales, manage your devices and suppliers under the <strong>Inventory</strong> and <strong>Suppliers</strong> panels:</p>
        <ul>
            <li><strong>Suppliers Directory</strong>: Manage contact details for wholesalers. Every mobile device registered can be linked to a supplier for traceability.</li>
            <li><strong>IMEI Supplier Lookup</strong>: Instantly search or scan a 15-digit IMEI to retrieve the supplier's contact details, purchase date, and device specifications (ideal for dealing with defective units).</li>
            <li><strong>Device Registration</strong>: Add new units with brand, model, specifications, SIM configurations (up to 4 SIMs), and associated IMEI numbers.</li>
        </ul>

        <h3>3. Sales & Installments Setup</h3>
        <p>To register a new installment plan:</p>
        <ol>
            <li>Navigate to <strong>New Sale</strong>.</li>
            <li>Select the customer and the device from the dropdown menus.</li>
            <li>Enter the cost price, selling price, down payment, and installment duration (e.g., 6 or 12 months).</li>
            <li>The system will automatically compute the remaining balance, the monthly installment amount, and generate the complete schedule.</li>
        </ol>

        <h3>4. Customer Ledgers & PDF Reports</h3>
        <p>Under the <strong>Customer Ledgers</strong> tab, you can search customers by Name, Father's Name, Phone, or Address:</p>
        <ul>
            <li><strong>Collect Installment Payment</strong>: Log monthly payments. The system updates the installment status to "Paid", registers the transaction, and updates the ledger in real-time.</li>
            <li><strong>Reschedule Remaining Balance</strong>: Re-calculate installment structures for customers requesting term modifications.</li>
            <li><strong>Export Ledger (PDF)</strong>: Save a professional PDF statement of the customer's account, including purchase details, selling date, and full payment history.</li>
            <li><strong>Preview & Print Ledger</strong>: View the ledger PDF directly in-app using the high-DPI print previewer and print to any physical or virtual printer.</li>
        </ul>

        <h3>5. Reminders & Alerts</h3>
        <p>The <strong>Reminders</strong> panel helps you track and collect pending balances:</p>
        <ul>
            <li>Filter records by <strong>Overdue</strong>, <strong>Due Today</strong>, <strong>Due This Week</strong>, or <strong>Next 7 Days</strong>.</li>
            <li>Double-clicking any record in the reminders table redirects you instantly to that customer's detailed ledger.</li>
        </ul>

        <h3>6. Cloud Synchronization & Security</h3>
        <ul>
            <li>The app uses a <strong>local cache synchronization engine</strong> to load data instantly, and queries Supabase in the background to update its state.</li>
            <li>Security is enforced at the database layer using <strong>Row-Level Security (RLS) policies</strong>, ensuring data integrity and safety.</li>
        </ul>
        """
        dialog = ScrollableTextDialog("System Documentation & Operations Manual", docs_html, self)
        dialog.exec()


class ScrollableTextDialog(QDialog):
    def __init__(self, title, html_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(680, 550)
        self.setMinimumSize(500, 400)
        
        # Apply clean design system styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QTextBrowser {
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                background-color: #F8FAFC;
                padding: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #334155;
            }
            QPushButton#btn_close {
                background-color: #1E293B;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#btn_close:hover {
                background-color: #0F172A;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        # Title Label
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        layout.addWidget(lbl_title)
        
        # Text Browser for rich text
        self.browser = QTextBrowser()
        self.browser.setHtml(html_content)
        self.browser.setOpenExternalLinks(True)  # Allow clicking links to open default browser
        layout.addWidget(self.browser)
        
        # Bottom Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setObjectName("btn_close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

