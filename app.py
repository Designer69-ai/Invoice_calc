from flask import Flask, render_template, request, jsonify
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
