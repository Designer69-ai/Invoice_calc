from flask import Flask, render_template, request, jsonify, send_file
import os
import main

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_invoice():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Input Extraction and Validation
        try:
            total_amount_str = data.get("total_amount")
            if total_amount_str is None or str(total_amount_str).strip() == "":
                return jsonify({"error": "Total amount is required"}), 400
            total_amount = float(total_amount_str)
            if total_amount < 0:
                return jsonify({"error": "Total amount cannot be negative"}), 400
        except ValueError:
            return jsonify({"error": "Total amount must be a valid number"}), 400
            
        try:
            leaves_taken_str = data.get("leaves_taken")
            if leaves_taken_str is None or str(leaves_taken_str).strip() == "":
                return jsonify({"error": "Leaves taken is required"}), 400
            leaves_taken = float(leaves_taken_str)
            if leaves_taken < 0:
                return jsonify({"error": "Leaves taken cannot be negative"}), 400
        except ValueError:
            return jsonify({"error": "Leaves taken must be a valid number"}), 400
            
        try:
            month_str = data.get("month")
            if month_str is None or str(month_str).strip() == "":
                return jsonify({"error": "Month is required"}), 400
            month = int(month_str)
            if month < 1 or month > 12:
                return jsonify({"error": "Month must be between 1 and 12"}), 400
        except ValueError:
            return jsonify({"error": "Month must be a valid integer between 1 and 12"}), 400
            
        # Run invoice calculation
        result = main.calculate(total_amount, leaves_taken, month)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def generate_reportlab_pdf(pdf_path, invoice_date_str, invoice_num, description, final_amount, leaves_taken):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.black,
        alignment=1, # Centered title
        spaceAfter=20
    )
    
    label_style = ParagraphStyle(
        'InvoiceLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
    )
    
    value_style = ParagraphStyle(
        'InvoiceValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
    )

    bold_val_style = ParagraphStyle(
        'InvoiceBoldValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
    )
    
    story.append(Paragraph("SERVICE INVOICE", title_style))
    story.append(Spacer(1, 15))
    
    # Metadata Table
    meta_data = [
        [
            Paragraph("Invoice Date:", label_style), 
            Paragraph(invoice_date_str, value_style),
            Paragraph("Invoice Number:", label_style),
            Paragraph(invoice_num, bold_val_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[90, 110, 110, 194])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Bill To Table
    address_text = "<b>Jetmobile Pte Ltd</b><br/>168 Jalan Bukit Merah<br/>#4-08A Connection One Tower 3<br/>Singapore 150168"
    bill_data = [
        [
            Paragraph("TO", label_style),
            Paragraph(address_text, value_style)
        ]
    ]
    bill_table = Table(bill_data, colWidths=[90, 414])
    bill_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 20))
    
    # Line Items Table
    items_header_style = ParagraphStyle(
        'ItemsHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
    )
    
    items_header_right_style = ParagraphStyle(
        'ItemsHeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=2
    )
    
    items_value_right_style = ParagraphStyle(
        'ItemsValueRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        alignment=2
    )

    items_bold_right_style = ParagraphStyle(
        'ItemsBoldRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=2
    )

    # Escape ampersands to prevent ReportLab parser XML error
    esc_desc = description.replace("&", "&amp;")

    items_data = [
        [
            Paragraph("Description", items_header_style), 
            Paragraph("USD Amount", items_header_right_style)
        ],
        [
            Paragraph(esc_desc, value_style), 
            Paragraph(f"USD {final_amount:,.2f}", items_value_right_style)
        ],
        [
            Paragraph("Off day (if any):", value_style), 
            Paragraph(f"{leaves_taken}", items_value_right_style)
        ],
        [
            Paragraph("Total", items_header_style), 
            Paragraph(f"USD {final_amount:,.2f}", items_bold_right_style)
        ]
    ]
    
    items_table = Table(items_data, colWidths=[350, 154])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,2), 0.5, colors.black),
        ('GRID', (0,3), (1,3), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 40))
    
    # Signature block
    sig_elements = []
    if os.path.exists("Signature.png"):
        sig_elements.append(Image("Signature.png", width=90, height=43))
    else:
        sig_elements.append(Paragraph("", value_style))
        
    sig_data = [
        [Paragraph("Signature:", label_style), sig_elements[0]],
        [Paragraph("Name:", label_style), Paragraph("Jaideep Singh Rajawat", value_style)]
    ]
    
    sig_table = Table(sig_data, colWidths=[90, 414])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sig_table)
    
    doc.build(story)

@app.route('/generate-pdf', methods=['GET', 'POST'])
def generate_pdf_invoice():
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            total_amount_str = data.get("total_amount")
            leaves_taken_str = data.get("leaves_taken")
            month_str = data.get("month")
        else:  # GET request from browser query params
            total_amount_str = request.args.get("total_amount")
            leaves_taken_str = request.args.get("leaves_taken")
            month_str = request.args.get("month")
            
        if not total_amount_str or not leaves_taken_str or not month_str:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Parse inputs
        try:
            total_amount = float(total_amount_str)
            leaves_taken = float(leaves_taken_str)
            month = int(month_str)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid inputs provided"}), 400

        # Calculate values
        result = main.calculate(total_amount, leaves_taken, month)
        
        import uuid
        import datetime
        import calendar
        import openpyxl
        from openpyxl.styles import Font
        from openpyxl.drawing.image import Image
        import io
        
        # Check COM availability
        use_reportlab = False
        try:
            import win32com.client
            import pythoncom
        except ImportError:
            use_reportlab = True
        
        # Format Date and Invoice Number
        current_year = datetime.date.today().year
        if month == 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_month = month + 1
            next_year = current_year
        invoice_date = datetime.date(next_year, next_month, 1)
        invoice_date_str = invoice_date.strftime("%Y-%m-%d")
        invoice_num_str = f"JSR{invoice_date.strftime('%Y-%m-%d')}"
        month_name = calendar.month_name[month]
        description = f"R&D Service for {month_name} {current_year}"
        
        import tempfile
        unique_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        temp_pdf = os.path.join(temp_dir, f"temp_invoice_{unique_id}.pdf")
        
        if not use_reportlab:
            # Load and fill spreadsheet (only needed for COM conversion or xlsx saving)
            wb = openpyxl.load_workbook("Service Invoice template - Monthly.xlsx")
            sheet = wb["Invoice"]
            
            sheet["C5"] = invoice_date
            sheet["E7"] = invoice_num_str
            sheet["A18"] = description
            sheet["E18"] = result["final_amount_usd"]
            sheet["E19"] = leaves_taken
            sheet["E21"] = result["final_amount_usd"]
            
            # Set name
            sheet["B30"] = "Jaideep Singh Rajawat"
            sheet["B30"].font = Font(name="Arial", size=12, bold=False)
            
            # Add Signature
            if os.path.exists("Signature.png"):
                img = Image("Signature.png")
                img.width = 90
                img.height = 43
                sheet.add_image(img, "B28")
            
            temp_xlsx = os.path.join(temp_dir, f"temp_invoice_{unique_id}.xlsx")
            wb.save(temp_xlsx)
            
            # Convert to PDF using Excel COM
            try:
                pythoncom.CoInitialize()
                excel = win32com.client.Dispatch("Excel.Application")
                excel.Visible = False
                excel.DisplayAlerts = False
                try:
                    abs_xlsx = os.path.abspath(temp_xlsx)
                    abs_pdf = os.path.abspath(temp_pdf)
                    wb_com = excel.Workbooks.Open(abs_xlsx)
                    ws_com = wb_com.Sheets("Invoice")
                    
                    ws_com.PageSetup.Zoom = False
                    ws_com.PageSetup.FitToPagesWide = 1
                    ws_com.PageSetup.FitToPagesTall = 1
                    
                    wb_com.ExportAsFixedFormat(0, abs_pdf)
                    wb_com.Close(SaveChanges=False)
                finally:
                    excel.Quit()
                    pythoncom.CoUninitialize()
                
                # Cleanup temp xlsx
                try: os.remove(temp_xlsx)
                except: pass
                
            except Exception as e:
                # COM failed, clean up and fallback to ReportLab
                try: os.remove(temp_xlsx)
                except: pass
                use_reportlab = True
                
        if use_reportlab:
            # Generate PDF using ReportLab
            generate_reportlab_pdf(temp_pdf, invoice_date_str, invoice_num_str, description, result["final_amount_usd"], leaves_taken)
            
        # Stream file to response
        if os.path.exists(temp_pdf):
            with open(temp_pdf, "rb") as f:
                pdf_data = io.BytesIO(f.read())
            pdf_data.seek(0)
            
            # Clean up temp file
            try: os.remove(temp_pdf)
            except: pass
            
            return send_file(
                pdf_data,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"Service_Invoice_{month_name}_{current_year}.pdf"
            )
        else:
            raise FileNotFoundError("PDF file was not generated successfully")
            
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF invoice: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

