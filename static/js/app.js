document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("calculator-form");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = document.getElementById("btn-text");
    const btnSpinner = document.getElementById("btn-spinner");
    const errorMessage = document.getElementById("error-message");
    
    const resultSection = document.getElementById("result-section");
    const placeholderContent = document.getElementById("placeholder-content");
    const resultContent = document.getElementById("result-content");
    
    // Result elements
    const resWorkingDays = document.getElementById("res-working-days");
    const resDeductionRate = document.getElementById("res-deduction-rate");
    const resTotalDeduction = document.getElementById("res-total-deduction");
    const resFinalUsd = document.getElementById("res-final-usd");
    const resExchangeRate = document.getElementById("res-exchange-rate");
    const resFinalInr = document.getElementById("res-final-inr");
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Clear previous states
        errorMessage.classList.add("hidden");
        errorMessage.textContent = "";
        
        const totalAmountStr = document.getElementById("total_amount").value;
        const leavesTakenStr = document.getElementById("leaves_taken").value;
        const month = document.getElementById("month").value;
        
        if (totalAmountStr.trim() === "") {
            showError("Total Amount is required.");
            return;
        }
        const totalAmount = parseFloat(totalAmountStr);
        if (isNaN(totalAmount) || totalAmount < 0) {
            showError("Total Amount must be a positive number.");
            return;
        }
        
        if (leavesTakenStr.trim() === "") {
            showError("Leaves Taken is required.");
            return;
        }
        const leavesTaken = parseFloat(leavesTakenStr);
        if (isNaN(leavesTaken) || leavesTaken < 0) {
            showError("Leaves Taken must be 0 or a positive number.");
            return;
        }
        
        if (!month) {
            showError("Please select an invoice month.");
            return;
        }
        
        // Set loading state
        setLoading(true);
        
        try {
            const response = await fetch("/calculate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    total_amount: totalAmount,
                    leaves_taken: leavesTaken,
                    month: month
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || "An error occurred during calculation.");
            }
            
            // Format and display results
            displayResults(data);
            
        } catch (error) {
            showError(error.message);
            // Hide result container and restore placeholder
            resultContent.classList.add("hidden");
            placeholderContent.classList.remove("hidden");
            resultSection.classList.add("placeholder-state");
        } finally {
            setLoading(false);
        }
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove("hidden");
    }
    
    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            btnText.classList.add("hidden");
            btnSpinner.classList.remove("hidden");
        } else {
            submitBtn.disabled = false;
            btnText.classList.remove("hidden");
            btnSpinner.classList.add("hidden");
        }
    }
    
    function displayResults(data) {
        // Remove placeholder layout and show content
        resultSection.classList.remove("placeholder-state");
        placeholderContent.classList.add("hidden");
        resultContent.classList.remove("hidden");
        
        // Populating results
        resWorkingDays.textContent = data.total_working_days;
        resDeductionRate.textContent = `$${data.deduction_per_day.toFixed(2)}`;
        resTotalDeduction.textContent = `$${data.total_deduction.toFixed(2)}`;
        resFinalUsd.textContent = `$${data.final_amount_usd.toFixed(2)}`;
        resExchangeRate.textContent = data.usd_to_inr_rate.toFixed(4);
        
        // Localized INR formatting
        resFinalInr.textContent = `INR ${data.final_amount_inr.toLocaleString('en-IN', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        })}`;
    }
});
