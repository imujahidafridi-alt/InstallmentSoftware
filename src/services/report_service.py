import os
import csv
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd
from src.config import ConfigManager

# ReportLab imports for professional PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ReportService:
    @staticmethod
    def generate_ledger_pdf(
        customer: Dict[str, Any],
        device: Dict[str, Any],
        sale: Dict[str, Any],
        installments: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
        output_path: str,
        shop_details: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generates a premium corporate individual customer ledger PDF.
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=letter, 
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        # Define premium typography styles
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=15
        )
        
        section_style = ParagraphStyle(
            name='SectionStyle',
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor('#2E4057'),
            spaceBefore=10,
            spaceAfter=5
        )
        
        label_style = ParagraphStyle(
            name='LabelStyle',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.HexColor('#555555')
        )
        
        value_style = ParagraphStyle(
            name='ValueStyle',
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#222222')
        )
        
        table_hdr_style = ParagraphStyle(
            name='TableHdrStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.white
        )
        
        table_row_style = ParagraphStyle(
            name='TableRowStyle',
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#333333')
        )

        table_hdr_center_style = ParagraphStyle(
            name='TableHdrCenterStyle',
            parent=table_hdr_style,
            alignment=1
        )
        
        table_hdr_right_style = ParagraphStyle(
            name='TableHdrRightStyle',
            parent=table_hdr_style,
            alignment=2
        )
        
        table_row_center_style = ParagraphStyle(
            name='TableRowCenterStyle',
            parent=table_row_style,
            alignment=1
        )
        
        table_row_right_style = ParagraphStyle(
            name='TableRowRightStyle',
            parent=table_row_style,
            alignment=2
        )
        
        status_paid_style = ParagraphStyle(
            name='StatusPaidStyle',
            parent=table_row_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#16A34A'),
            backColor=colors.HexColor('#DCFCE7'),
            borderColor=colors.HexColor('#BBF7D0'),
            borderWidth=0.5,
            borderRadius=3,
            borderPadding=3,
            alignment=1
        )
        
        status_partial_style = ParagraphStyle(
            name='StatusPartialStyle',
            parent=table_row_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#D97706'),
            backColor=colors.HexColor('#FEF3C7'),
            borderColor=colors.HexColor('#FDE68A'),
            borderWidth=0.5,
            borderRadius=3,
            borderPadding=3,
            alignment=1
        )
        
        status_pending_style = ParagraphStyle(
            name='StatusPendingStyle',
            parent=table_row_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#DC2626'),
            backColor=colors.HexColor('#FEE2E2'),
            borderColor=colors.HexColor('#FCA5A5'),
            borderWidth=0.5,
            borderRadius=3,
            borderPadding=3,
            alignment=1
        )

        elements = []

        # Shop Header
        if not shop_details:
            try:
                from src.config import ConfigManager
                config = ConfigManager.load_config()
                shop_details = {
                    "name": config.get("shop_name", "Device Installment Store"),
                    "contact": config.get("shop_contact", "Ph: 0300-1234567"),
                    "address": config.get("shop_address", "Main Market, Commercial Area")
                }
            except Exception:
                shop_details = {}

        shop_name = (shop_details or {}).get("name", "Device Installment Store")
        shop_contact = (shop_details or {}).get("contact", "Ph: 0300-1234567")
        shop_address = (shop_details or {}).get("address", "Main Market, Commercial Area")
        
        # Load and scale shop logo if it exists
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "views", "assets", "logo.png"
        )
        logo_img = None
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=55, height=55)
            except Exception:
                pass
                
        # Shop Details Header Layout
        shop_name_para = Paragraph(f"<b>{shop_name}</b>", ParagraphStyle('ShopName', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#1E293B'), leading=22))
        
        # Format contact number to look cleaner
        contact_text = shop_contact
        if contact_text and not any(contact_text.lower().startswith(prefix) for prefix in ["ph:", "tel:", "contact:", "phone:"]):
            contact_text = f"Ph: {contact_text}"
            
        shop_address_para = Paragraph(shop_address, ParagraphStyle('ShopAddr', fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor('#475569'), leading=13))
        shop_contact_para = Paragraph(contact_text, ParagraphStyle('ShopContact', fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor('#475569'), leading=13))
        
        if logo_img:
            brand_table = Table([[logo_img, [shop_name_para, Spacer(1, 4), shop_address_para, Spacer(1, 3), shop_contact_para]]], colWidths=[65, 285])
            brand_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (1, 0), (1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            header_left = brand_table
        else:
            header_left = [shop_name_para, Spacer(1, 4), shop_address_para, Spacer(1, 3), shop_contact_para]
            
        # Report Title and Info
        report_title_style = ParagraphStyle(
            name='ReportTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.HexColor('#2563EB'), # Accent Blue
            alignment=2 # Right aligned
        )
        report_meta_style = ParagraphStyle(
            name='ReportMeta',
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#64748B'),
            alignment=2 # Right aligned
        )
        
        header_right = [
            Paragraph("LEDGER REPORT", report_title_style),
            Spacer(1, 4),
            Paragraph(f"Date: <b>{date.today().strftime('%d-%b-%Y')}</b>", report_meta_style),
            Spacer(1, 2),
            Paragraph(f"Sale ID: <b>{sale.get('id', '')[:8].upper()}</b>", report_meta_style)
        ]
        
        header_table = Table([[header_left, header_right]], colWidths=[350, 190])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        # Horizontal divider line
        divider = Table([[""]], colWidths=[540], rowHeights=[2])
        divider.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2563EB')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(divider)
        elements.append(Spacer(1, 12))

        # Customer & Device Details Grid Layout
        imei_1 = device.get("imei_1")
        if imei_1 and imei_1.startswith("00"):
            display_imei_1 = "N/A"
        else:
            display_imei_1 = imei_1
        cust_imeis = ", ".join(filter(None, [display_imei_1, device.get("imei_2"), device.get("imei_3"), device.get("imei_4")]))
        
        card_header_style = ParagraphStyle(
            name='CardHeader',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=4
        )
        
        info_data = [
            [
                Paragraph("Customer Details", card_header_style), 
                Paragraph("Device Details", card_header_style)
            ],
            [
                Paragraph("Name:", label_style), Paragraph(str(customer.get("name", "")), value_style),
                Paragraph("Device Name:", label_style), Paragraph(str(device.get("name", "")), value_style)
            ],
            [
                Paragraph("Father Name:", label_style), Paragraph(str(customer.get("father_name", "")), value_style),
                Paragraph("Brand / Model:", label_style), Paragraph(f"{device.get('brand','')} / {device.get('model','')}", value_style)
            ],
            [
                Paragraph("Mobile:", label_style), Paragraph(str(customer.get("mobile", "")), value_style),
                Paragraph("RAM / ROM:", label_style), Paragraph(f"{device.get('ram','')}/{device.get('rom','')}", value_style)
            ],
            [
                Paragraph("", label_style), Paragraph("", value_style),
                Paragraph("IMEIs:", label_style), Paragraph(cust_imeis, value_style)
            ]
        ]
        
        info_table = Table(info_data, colWidths=[80, 180, 80, 180])
        info_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        card_table = Table([[info_table]], colWidths=[540])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(card_table)
        elements.append(Spacer(1, 12))

        # Financial Summary
        selling_price = float(sale.get("selling_price", 0))
        down_payment = float(sale.get("down_payment", 0))
        remaining_balance = selling_price - down_payment
        
        fin_label_style = ParagraphStyle(
            name='FinLabelStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#64748B'),
            alignment=1
        )
        
        fin_val_neutral = ParagraphStyle(
            name='FinValNeutral',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#1E293B'),
            alignment=1
        )
        
        fin_val_green = ParagraphStyle(
            name='FinValGreen',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#16A34A'), # Green-600
            alignment=1
        )
        
        fin_val_blue = ParagraphStyle(
            name='FinValBlue',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#2563EB'), # Blue-600
            alignment=1
        )
        
        fin_data = [
            [
                Paragraph("SELLING PRICE", fin_label_style), 
                Paragraph("DOWN PAYMENT", fin_label_style), 
                Paragraph("FINANCE AMOUNT", fin_label_style)
            ],
            [
                Paragraph(ConfigManager.format_currency(selling_price), fin_val_neutral),
                Paragraph(ConfigManager.format_currency(down_payment), fin_val_green),
                Paragraph(ConfigManager.format_currency(remaining_balance), fin_val_blue)
            ]
        ]
        fin_table = Table(fin_data, colWidths=[180, 180, 180])
        fin_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('LINEVERTICAL', (1, 0), (2, -1), 1, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ]))
        elements.append(Paragraph("Financial Summary", section_style))
        elements.append(Spacer(1, 4))
        elements.append(fin_table)
        elements.append(Spacer(1, 12))

        # Installments Schedule Table
        inst_headers = [
            Paragraph("No.", table_hdr_center_style),
            Paragraph("Due Date", table_hdr_style),
            Paragraph("Installment", table_hdr_right_style),
            Paragraph("Paid Date", table_hdr_style),
            Paragraph("Amount Paid", table_hdr_right_style),
            Paragraph("Status", table_hdr_center_style),
            Paragraph("Outstanding", table_hdr_right_style)
        ]
        
        inst_rows = [inst_headers]
        running_outstanding = remaining_balance
        
        # Build map of payments per installment
        payment_map = {}
        for pay in payments:
            inst_id = pay["installment_id"]
            if inst_id not in payment_map:
                payment_map[inst_id] = []
            payment_map[inst_id].append(pay)
            
        for index, inst in enumerate(installments, 1):
            inst_id = inst["id"]
            due_dt = datetime.strptime(inst["due_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            inst_amount = float(inst["amount"])
            
            inst_payments = payment_map.get(inst_id, [])
            total_paid_for_inst = sum(float(p["amount_received"]) for p in inst_payments)
            
            # Format dates of payments
            if inst_payments:
                dates = [datetime.strptime(p["payment_date"], "%Y-%m-%d").strftime("%d-%b-%Y") for p in inst_payments]
                paid_dt_str = ", ".join(dates)
            else:
                paid_dt_str = "-"
                
            running_outstanding -= total_paid_for_inst
            # Prevent floating point negative anomalies
            if abs(running_outstanding) < 0.01:
                running_outstanding = 0.0
                
            status_text = inst["status"]
            # Color code status with beautiful badges
            if status_text == 'Paid':
                status_paragraph = Paragraph(status_text, status_paid_style)
            elif status_text == 'Partial':
                status_paragraph = Paragraph(status_text, status_partial_style)
            else:
                status_paragraph = Paragraph(status_text, status_pending_style)
            
            row = [
                Paragraph(str(index), table_row_center_style),
                Paragraph(due_dt, table_row_style),
                Paragraph(ConfigManager.format_currency(inst_amount), table_row_right_style),
                Paragraph(paid_dt_str, table_row_style),
                Paragraph(ConfigManager.format_currency(total_paid_for_inst), table_row_right_style),
                status_paragraph,
                Paragraph(ConfigManager.format_currency(running_outstanding), table_row_right_style)
            ]
            inst_rows.append(row)
            
        inst_table = Table(inst_rows, colWidths=[30, 75, 85, 90, 85, 85, 90])
        inst_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#1E293B')),
        ]))
        elements.append(Paragraph("Repayment Schedule Ledger", section_style))
        elements.append(Spacer(1, 4))
        elements.append(inst_table)
        elements.append(Spacer(1, 15))

        # Ledger Footer
        footer_style = ParagraphStyle(
            name='FooterStyle',
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=1 # Center
        )
        elements.append(Paragraph("Developed by Mujahid Afridi | Software Developer | Contact: +92 313 930041 | © 2026 All Rights Reserved", footer_style))

        # Build document
        doc.build(elements)
        return output_path

    @staticmethod
    def generate_monthly_collection_pdf(
        month: int,
        year: int,
        data: List[Dict[str, Any]],
        summary: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generates a monthly collection summary PDF report.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        
        elements = []
        
        # Load and scale shop logo if it exists
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "views", "assets", "logo.png"
        )
        logo_img = None
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=55, height=55)
            except Exception:
                pass
                
        # Shop Details
        shop_details = None
        try:
            from src.config import ConfigManager
            config = ConfigManager.load_config()
            shop_details = {
                "name": config.get("shop_name", "Device Installment Store"),
                "contact": config.get("shop_contact", "Ph: 0300-1234567"),
                "address": config.get("shop_address", "Main Market, Commercial Area")
            }
        except Exception:
            shop_details = {}
            
        shop_name = (shop_details or {}).get("name", "Device Installment Store")
        shop_contact = (shop_details or {}).get("contact", "Ph: 0300-1234567")
        shop_address = (shop_details or {}).get("address", "Main Market, Commercial Area")
        
        shop_name_para = Paragraph(f"<b>{shop_name}</b>", ParagraphStyle('ShopNameMC', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#1E293B'), leading=22))
        
        # Format contact number to look cleaner
        contact_text = shop_contact
        if contact_text and not any(contact_text.lower().startswith(prefix) for prefix in ["ph:", "tel:", "contact:", "phone:"]):
            contact_text = f"Ph: {contact_text}"
            
        shop_address_para = Paragraph(shop_address, ParagraphStyle('ShopAddrMC', fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor('#475569'), leading=13))
        shop_contact_para = Paragraph(contact_text, ParagraphStyle('ShopContactMC', fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor('#475569'), leading=13))
        
        if logo_img:
            brand_table = Table([[logo_img, [shop_name_para, Spacer(1, 4), shop_address_para, Spacer(1, 3), shop_contact_para]]], colWidths=[65, 285])
            brand_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (1, 0), (1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            header_left = brand_table
        else:
            header_left = [shop_name_para, Spacer(1, 4), shop_address_para, Spacer(1, 3), shop_contact_para]
            
        # Report Title and Info
        report_title_style = ParagraphStyle(
            name='MCReportTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.HexColor('#2563EB'), # Accent Blue
            alignment=2 # Right aligned
        )
        report_meta_style = ParagraphStyle(
            name='MCReportMeta',
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#64748B'),
            alignment=2 # Right aligned
        )
        
        month_name = datetime(year, month, 1).strftime("%B %Y")
        
        header_right = [
            Paragraph("COLLECTIONS REPORT", report_title_style),
            Spacer(1, 4),
            Paragraph(f"Period: <b>{month_name}</b>", report_meta_style),
            Spacer(1, 2),
            Paragraph(f"Generated: <b>{datetime.now().strftime('%d-%b-%Y')}</b>", report_meta_style)
        ]
        
        header_table = Table([[header_left, header_right]], colWidths=[350, 190])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        # Horizontal divider line
        divider = Table([[""]], colWidths=[540], rowHeights=[2])
        divider.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2563EB')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(divider)
        elements.append(Spacer(1, 12))

        # Summary Metrics Row
        fin_label_style = ParagraphStyle(
            name='MCFinLabelStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.HexColor('#64748B'),
            alignment=1
        )
        
        fin_val_green = ParagraphStyle(
            name='MCFinValGreen',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#16A34A'), # Green-600
            alignment=1
        )
        
        fin_val_blue = ParagraphStyle(
            name='MCFinValBlue',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#2563EB'), # Blue-600
            alignment=1
        )
        
        fin_val_neutral = ParagraphStyle(
            name='MCFinValNeutral',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#1E293B'),
            alignment=1
        )
        
        sum_data = [
            [
                Paragraph("TOTAL COLLECTIONS", fin_label_style), 
                Paragraph("TOTAL OUTSTANDING", fin_label_style), 
                Paragraph("ESTIMATED PROFIT", fin_label_style)
            ],
            [
                Paragraph(ConfigManager.format_currency(summary.get('total_collection', 0)), fin_val_green),
                Paragraph(ConfigManager.format_currency(summary.get('total_outstanding', 0)), fin_val_neutral),
                Paragraph(ConfigManager.format_currency(summary.get('total_profit', 0)), fin_val_blue)
            ]
        ]
        sum_table = Table(sum_data, colWidths=[180, 180, 180])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('LINEVERTICAL', (1, 0), (2, -1), 1, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ]))
        elements.append(Paragraph("Financial Summary", ParagraphStyle('MCSectionStyle', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2E4057'), spaceBefore=10, spaceAfter=5)))
        elements.append(Spacer(1, 4))
        elements.append(sum_table)
        elements.append(Spacer(1, 12))

        # Collection Table
        hdr_style = ParagraphStyle('MCHdrStyle', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white)
        hdr_center_style = ParagraphStyle('MCHdrCenterStyle', parent=hdr_style, alignment=1)
        hdr_right_style = ParagraphStyle('MCHdrRightStyle', parent=hdr_style, alignment=2)
        
        row_style = ParagraphStyle('MCRowStyle', fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#333333'))
        row_center_style = ParagraphStyle('MCRowCenterStyle', parent=row_style, alignment=1)
        row_right_style = ParagraphStyle('MCRowRightStyle', parent=row_style, alignment=2)

        table_rows = [[
            Paragraph("No.", hdr_center_style),
            Paragraph("Customer Name", hdr_style),
            Paragraph("Device Sold", hdr_style),
            Paragraph("Payment Date", hdr_style),
            Paragraph("Amount Received", hdr_right_style),
            Paragraph("Notes", hdr_style)
        ]]

        for idx, row in enumerate(data, 1):
            pay_dt = datetime.strptime(row["payment_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            table_rows.append([
                Paragraph(str(idx), row_center_style),
                Paragraph(row.get("customer_name", ""), row_style),
                Paragraph(row.get("device_name", ""), row_style),
                Paragraph(pay_dt, row_style),
                Paragraph(ConfigManager.format_currency(row.get('amount_received', 0)), row_right_style),
                Paragraph(row.get("notes", "") or "-", row_style)
            ])

        col_table = Table(table_rows, colWidths=[30, 125, 125, 70, 90, 100])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#1E293B')),
        ]))
        
        elements.append(Paragraph("Received Payments Log", ParagraphStyle('MCSubStyle', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2E4057'), spaceBefore=10, spaceAfter=5)))
        elements.append(Spacer(1, 4))
        elements.append(col_table)
        elements.append(Spacer(1, 15))
        
        # Ledger Footer
        footer_style = ParagraphStyle(
            name='MCFooterStyle',
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=1 # Center
        )
        elements.append(Paragraph("Developed by Mujahid Afridi | Software Developer | Contact: +92 313 930041 | © 2026 All Rights Reserved", footer_style))
        
        doc.build(elements)
        return output_path

    @staticmethod
    def generate_monthly_collection_excel(
        month: int,
        year: int,
        data: List[Dict[str, Any]],
        summary: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Exports the monthly collection log into an Excel file.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Format list to Pandas DataFrame
        rows = []
        for idx, item in enumerate(data, 1):
            rows.append({
                "S.No": idx,
                "Customer Name": item.get("customer_name", ""),
                "Device Name": item.get("device_name", ""),
                "Payment Date": item.get("payment_date", ""),
                "Amount Received": float(item.get("amount_received", 0)),
                "Notes": item.get("notes", "") or ""
            })
            
        df = pd.DataFrame(rows)
        
        # Write using ExcelWriter
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Collections Log", index=False)
            
            # Create a summary sheet as well
            sum_df = pd.DataFrame([
                {"Metric": "Total Collection This Month", "Value": summary.get("total_collection", 0)},
                {"Metric": "Total Outstanding Balance", "Value": summary.get("total_outstanding", 0)},
                {"Metric": "Estimated Margin Profit", "Value": summary.get("total_profit", 0)},
                {"Metric": "Report Month", "Value": f"{month}/{year}"},
                {"Metric": "Export Timestamp", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ])
            sum_df.to_excel(writer, sheet_name="Financial Summary", index=False)
            
        return output_path

    @staticmethod
    def generate_monthly_collection_csv(
        month: int,
        year: int,
        data: List[Dict[str, Any]],
        summary: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Exports the monthly collection log into a CSV file.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write metadata header
            month_name = datetime(year, month, 1).strftime("%B %Y")
            writer.writerow(["Monthly Collection Report", month_name])
            writer.writerow(["Generated On", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            
            # Write summary
            writer.writerow(["Summary KPI Name", "Amount"])
            writer.writerow(["Total Collection This Month", summary.get("total_collection", 0)])
            writer.writerow(["Total Outstanding Balance", summary.get("total_outstanding", 0)])
            writer.writerow(["Total Profit Margin", summary.get("total_profit", 0)])
            writer.writerow([])
            
            # Write data rows
            writer.writerow(["S.No", "Customer Name", "Device Name", "Payment Date", "Amount Received", "Notes"])
            for idx, item in enumerate(data, 1):
                writer.writerow([
                    idx,
                    item.get("customer_name", ""),
                    item.get("device_name", ""),
                    item.get("payment_date", ""),
                    item.get("amount_received", 0),
                    item.get("notes", "") or ""
                ])
                
        return output_path
