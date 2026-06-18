import os
import csv
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd

# ReportLab imports for professional PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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
            textColor=colors.HexColor('#1A2530'),
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
        
        header_data = [
            [Paragraph(f"<b>{shop_name}</b>", title_style), Paragraph(f"<b>LEDGER REPORT</b>", title_style)],
            [Paragraph(shop_address, value_style), Paragraph(f"Date: {date.today().strftime('%d-%b-%Y')}", value_style)],
            [Paragraph(shop_contact, value_style), Paragraph(f"Sale ID: {sale.get('id', '')[:8]}", value_style)]
        ]
        
        header_table = Table(header_data, colWidths=[350, 190])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        # Horizontal divider line
        divider = Table([[""]], colWidths=[540], rowHeights=[2])
        divider.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1A2530')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(divider)
        elements.append(Spacer(1, 12))

        # Customer & Device Grid Layout
        cust_imeis = ", ".join(filter(None, [device.get("imei_1"), device.get("imei_2"), device.get("imei_3"), device.get("imei_4")]))
        
        info_data = [
            [
                Paragraph("Customer Details", section_style), 
                Paragraph("Device Details", section_style)
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
        
        info_table = Table(info_data, colWidths=[90, 180, 90, 180])
        info_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

        # Financial Summary
        selling_price = float(sale.get("selling_price", 0))
        down_payment = float(sale.get("down_payment", 0))
        remaining_balance = selling_price - down_payment
        
        fin_data = [
            [
                Paragraph("Selling Price", table_hdr_style), 
                Paragraph("Down Payment", table_hdr_style), 
                Paragraph("Finance Amount", table_hdr_style)
            ],
            [
                Paragraph(f"Rs. {selling_price:,.2f}", value_style),
                Paragraph(f"Rs. {down_payment:,.2f}", value_style),
                Paragraph(f"Rs. {remaining_balance:,.2f}", value_style)
            ]
        ]
        fin_table = Table(fin_data, colWidths=[180, 180, 180])
        fin_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4057')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(Paragraph("Financial Summary", section_style))
        elements.append(fin_table)
        elements.append(Spacer(1, 15))

        # Installments Schedule Table
        inst_headers = [
            Paragraph("No.", table_hdr_style),
            Paragraph("Due Date", table_hdr_style),
            Paragraph("Installment", table_hdr_style),
            Paragraph("Paid Date", table_hdr_style),
            Paragraph("Amount Paid", table_hdr_style),
            Paragraph("Status", table_hdr_style),
            Paragraph("Outstanding", table_hdr_style)
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
            # Color code status
            if status_text == 'Paid':
                status_color = '#27AE60'  # Green
            elif status_text == 'Partial':
                status_color = '#F39C12'  # Orange
            else:
                status_color = '#E74C3C'  # Red
                
            status_paragraph = Paragraph(f"<font color='{status_color}'><b>{status_text}</b></font>", table_row_style)
            
            row = [
                Paragraph(str(index), table_row_style),
                Paragraph(due_dt, table_row_style),
                Paragraph(f"Rs. {inst_amount:,.2f}", table_row_style),
                Paragraph(paid_dt_str, table_row_style),
                Paragraph(f"Rs. {total_paid_for_inst:,.2f}", table_row_style),
                status_paragraph,
                Paragraph(f"Rs. {running_outstanding:,.2f}", table_row_style)
            ]
            inst_rows.append(row)
            
        inst_table = Table(inst_rows, colWidths=[35, 75, 85, 95, 85, 75, 90])
        inst_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A2530')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(Paragraph("Repayment Schedule Ledger", section_style))
        elements.append(inst_table)
        elements.append(Spacer(1, 20))

        # Ledger Footer
        footer_style = ParagraphStyle(
            name='FooterStyle',
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=1 # Center
        )
        elements.append(Paragraph("This is a computer-generated document. No signature required.", footer_style))

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
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor('#1A2530'), spaceAfter=15)
        text_style = ParagraphStyle('TextStyle', fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#333333'))
        hdr_style = ParagraphStyle('HdrStyle', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)
        row_style = ParagraphStyle('RowStyle', fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#333333'))

        elements = []
        
        # Header
        month_name = datetime(year, month, 1).strftime("%B %Y")
        elements.append(Paragraph(f"<b>Monthly Collection Report - {month_name}</b>", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}", text_style))
        elements.append(Spacer(1, 10))

        # Summary Metrics Row
        sum_data = [
            ["Total Collections This Month", "Total Outstanding Balance", "Estimated Profit Margin"],
            [f"Rs. {summary.get('total_collection', 0):,.2f}", f"Rs. {summary.get('total_outstanding', 0):,.2f}", f"Rs. {summary.get('total_profit', 0):,.2f}"]
        ]
        sum_table = Table(sum_data, colWidths=[180, 180, 180])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4057')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 15))

        # Collection Table
        table_rows = [[
            Paragraph("No.", hdr_style),
            Paragraph("Customer Name", hdr_style),
            Paragraph("Device Sold", hdr_style),
            Paragraph("Payment Date", hdr_style),
            Paragraph("Amount Received", hdr_style),
            Paragraph("Notes", hdr_style)
        ]]

        for idx, row in enumerate(data, 1):
            pay_dt = datetime.strptime(row["payment_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            table_rows.append([
                Paragraph(str(idx), row_style),
                Paragraph(row.get("customer_name", ""), row_style),
                Paragraph(row.get("device_name", ""), row_style),
                Paragraph(pay_dt, row_style),
                Paragraph(f"Rs. {float(row.get('amount_received', 0)):,.2f}", row_style),
                Paragraph(row.get("notes", "") or "-", row_style)
            ])

        col_table = Table(table_rows, colWidths=[30, 120, 120, 70, 90, 110])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A2530')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(Paragraph("Received Payments Log", ParagraphStyle('Sub', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2E4057'), spaceAfter=5)))
        elements.append(col_table)
        
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
