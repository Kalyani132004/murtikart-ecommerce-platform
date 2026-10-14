document.addEventListener('DOMContentLoaded', () => {
    const modelSelect = document.getElementById('modelSelect');
    const quantityInput = document.getElementById('quantity');
    const unitPriceInput = document.getElementById('unitPrice');
    const totalPriceEl = document.getElementById('totalPrice');
    const discountAmountEl = document.getElementById('discountAmount');
    const finalPriceEl = document.getElementById('finalPrice');
    const advanceInput = document.getElementById('advancePaid');
    const balanceText = document.getElementById('balanceText');
    function populateModels() {
        if (!modelSelect) return;
        let stored = localStorage.getItem('murtiKartModels');
        const models = stored ? JSON.parse(stored) : [];
        
        const currentVal = modelSelect.value;
        modelSelect.innerHTML = '<option value="" disabled selected>Choose a model...</option>';
        models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.price.replace(/,/g, ''); 
            opt.text = `${m.name} (₹${m.price}) - Stock: ${m.stock}`;
            if(opt.value === currentVal) opt.selected = true;
            modelSelect.appendChild(opt);
        });
    }

    populateModels();

    function getDiscountDetails(total) {
        if (total >= 200000) return { rate: 0.35, label: "Platinum (35%)", tier: "Platinum" };
        if (total >= 50000) return { rate: 0.25, label: "Gold (25%)", tier: "Gold" };
        if (total >= 10000) return { rate: 0.15, label: "Silver (15%)", tier: "Silver" };
        return { rate: 0.05, label: "Standard (5%)", tier: "Standard" };
    }

    function calculate() {
        const unitPrice = parseFloat(modelSelect.value) || 0;
        const qty = parseInt(quantityInput.value) || 0;
        const advance = parseFloat(advanceInput?.value) || 0;

        unitPriceInput.value = unitPrice.toLocaleString('en-IN');
        
        const total = unitPrice * qty;
        const discountDetails = getDiscountDetails(total);
        const discount = total * discountDetails.rate;
        const final = total - discount;
        const balance = final - advance;

        // Update UI
        const discountPercentInput = document.getElementById('discountPercent');
        if (discountPercentInput) {
            discountPercentInput.value = (discountDetails.rate * 100);
        }

        totalPriceEl.innerText = `₹${total.toLocaleString('en-IN')}`;
        discountAmountEl.innerText = `-₹${discount.toLocaleString('en-IN')} (${discountDetails.tier})`;
        finalPriceEl.innerText = `₹${final.toLocaleString('en-IN')}`;
        
        const discountLabelEl = document.getElementById('discountLabel');
        if (discountLabelEl) {
            discountLabelEl.innerText = `Discount Amount (${discountDetails.label}):`;
        }
        
        if(balanceText) {
            balanceText.innerText = `Pending Balance: ₹${Math.max(0, balance).toLocaleString('en-IN')}`;
        }
    }

    if(modelSelect) {
        modelSelect.addEventListener('change', calculate);
        quantityInput.addEventListener('input', calculate);
        advanceInput?.addEventListener('input', calculate);
    }
});
