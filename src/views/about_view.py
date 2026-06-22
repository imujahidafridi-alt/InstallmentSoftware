import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
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
        
        lbl_app_name = QLabel("Asif Mobile Center")
        lbl_app_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #0F172A;")
        
        lbl_sub = QLabel("Device Installment Management System")
        lbl_sub.setStyleSheet("font-size: 14px; font-weight: 500; color: #475569;")
        
        lbl_version = QLabel("Enterprise Edition — Version 1.2.0-stable (Release 2026)")
        lbl_version.setStyleSheet("font-size: 12px; color: #64748B;")

        brand_info_layout.addWidget(lbl_app_name)
        brand_info_layout.addWidget(lbl_sub)
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
            "© 2026 Asif Mobile Center. All Rights Reserved.\n"
            "This software product is protected under international copyright "
            "and intellectual property laws. Unauthorized duplication, reverse engineering, "
            "or redistribution of this application or any part thereof is strictly prohibited "
            "and subject to severe legal penalties."
        )
        lbl_copyright_text.setStyleSheet("color: #64748B; font-size: 11px;")
        lbl_copyright_text.setWordWrap(True)

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
        
        footer_layout.addWidget(btn_docs)
        footer_layout.addWidget(btn_license)
        footer_layout.addStretch()
        
        card_layout.addLayout(footer_layout)

        main_layout.addWidget(center_card)
        main_layout.addStretch()
