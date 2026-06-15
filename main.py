import datetime
import calendar 
import urllib.request
import json

def main():
    print(f"Running invoice calculator")
    
    # Get user input for invoice details
    total_amount, leaves_taken, month = get_user_input()
    
    # Calculate the total amount payable after deductions
    calculate(total_amount, leaves_taken, month)
    
    
def get_user_input():
    # Get the total amount payable 
    total_amount = float(input("Enter the total amount payable (USD): "))
    # Get the leaves taken by the employee
    leaves_taken = float(input("Enter the number of leaves taken by the employee (0.5 - half day, 1 - full day): "))
    # Get the month for the invoice
    month = int(input("Enter the month for the invoice (1-12): "))
    
    return total_amount, leaves_taken, month

def get_total_working_days(month):
    year = datetime.date.today().year
    _, days_in_month = calendar.monthrange(year, month)
    working_days = 0
    for day in range(1, days_in_month + 1):
        weekday = datetime.date(year, month, day).weekday()
        if weekday < 5:
            working_days += 1
    return working_days

def get_usd_to_inr_rate():
    # Free API to fetch live exchange rates relative to USD
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and "rates" in data and "INR" in data["rates"]:
                return data["rates"]["INR"]
            else:
                raise ValueError("INR rate not found in response data")
    except Exception as e:
        # Fallback rate if network request fails
        fallback_rate = 83.50
        print(f"\nWarning: Could not fetch real-time USD/INR rate ({e}). Using fallback rate of {fallback_rate:.2f}")
        return fallback_rate

def calculate(total_amount, leaves_taken, month):
    # Get the total working days in the specified month
    total_working_days = get_total_working_days(month)
    
    # Calculate the deduction based on leaves taken
    deduction_per_day = total_amount / total_working_days
    total_deduction = deduction_per_day * leaves_taken
    
    # Calculate the final amount payable after deductions
    final_amount = total_amount - total_deduction
    
    # Fetch real-time exchange rate and convert
    usd_to_inr_rate = get_usd_to_inr_rate()
    final_amount_inr = final_amount * usd_to_inr_rate
    
    print(f"\n--- Invoice Summary ---")
    print(f"Total amount payable after deductions (USD): ${final_amount:.2f}")
    print(f"Current USD to INR rate: {usd_to_inr_rate:.4f}")
    print(f"Total amount payable after deductions (INR): INR {final_amount_inr:.2f}")
    
    return {
        "total_working_days": total_working_days,
        "deduction_per_day": deduction_per_day,
        "total_deduction": total_deduction,
        "final_amount_usd": final_amount,
        "usd_to_inr_rate": usd_to_inr_rate,
        "final_amount_inr": final_amount_inr
    }

if __name__ == "__main__":
    main()
    


