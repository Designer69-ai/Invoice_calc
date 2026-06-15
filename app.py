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
        
        try:
            import win32com.client
            import pythoncom
        except ImportError:
            return jsonify({"error": "PDF generation requires a Microsoft Excel Windows environment and is not supported in Linux/Vercel hosting."}), 500
        
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
        
        # Load and fill spreadsheet
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
        
        # Save temp file
        unique_id = str(uuid.uuid4())
        temp_xlsx = f"temp_invoice_{unique_id}.xlsx"
        temp_pdf = f"temp_invoice_{unique_id}.pdf"
        wb.save(temp_xlsx)
        
        # Convert to PDF using Excel COM
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
            
        # Stream file to response
        if os.path.exists(temp_pdf):
            with open(temp_pdf, "rb") as f:
                pdf_data = io.BytesIO(f.read())
            pdf_data.seek(0)
            
            # Clean up temp files
            try: os.remove(temp_xlsx)
            except: pass
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

