// Checkout Flow Management
const API_BASE = '/api';
let checkoutSessionId = null;
let selectedPlan = null;

// Get plan from URL or localStorage
function getSelectedPlan() {
    const urlParams = new URLSearchParams(window.location.search);
    const planFromUrl = urlParams.get('plan');
    
    if (planFromUrl) {
        localStorage.setItem('selectedPlan', planFromUrl);
        return planFromUrl;
    }
    
    return localStorage.getItem('selectedPlan') || 'cosmic';
}

// Initialize checkout
async function initializeCheckout() {
    selectedPlan = getSelectedPlan();
    
    // Check if we have an existing session
    const existingSessionId = localStorage.getItem('checkoutSessionId');
    
    if (existingSessionId) {
        // Try to resume existing session
        try {
            const response = await fetch(`${API_BASE}/checkout/progress/${existingSessionId}`);
            if (response.ok) {
                const progress = await response.json();
                checkoutSessionId = existingSessionId;
                resumeFromProgress(progress);
                return;
            }
        } catch (error) {
            console.log('Could not resume session, starting new one');
        }
    }
    
    // Start new checkout session
    try {
        const response = await fetch(`${API_BASE}/checkout/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan: selectedPlan })
        });
        
        if (!response.ok) {
            throw new Error('Failed to start checkout');
        }
        
        const data = await response.json();
        checkoutSessionId = data.session_id;
        localStorage.setItem('checkoutSessionId', checkoutSessionId);
        
        showStep('email');
    } catch (error) {
        console.error('Error initializing checkout:', error);
        alert('Failed to start checkout. Please try again.');
        window.location.href = '/';
    }
}

// Resume from saved progress
function resumeFromProgress(progress) {
    // Pre-fill forms
    if (progress.email) {
        document.getElementById('email').value = progress.email;
    }
    if (progress.phone) {
        document.getElementById('phone').value = progress.phone;
    }
    
    // Show current step
    showStep(progress.current_step);
    
    // Update progress indicator
    if (progress.step_email_completed) {
        markStepComplete('email');
    }
    if (progress.step_phone_completed) {
        markStepComplete('phone');
    }
    if (progress.step_address_completed) {
        markStepComplete('address');
    }
}

// Show specific step
function showStep(stepName) {
    // Hide all steps
    document.querySelectorAll('.checkout-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Show requested step
    const stepElement = document.getElementById(`step-${stepName}`);
    if (stepElement) {
        stepElement.classList.add('active');
    }
    
    // Update progress indicator
    updateProgressIndicator(stepName);
}

// Update progress indicator
function updateProgressIndicator(currentStep) {
    const steps = ['email', 'phone', 'address', 'payment'];
    const currentIndex = steps.indexOf(currentStep);
    
    steps.forEach((step, index) => {
        const progressStep = document.getElementById(`progress-${step}`);
        if (index < currentIndex) {
            progressStep.classList.add('completed');
            progressStep.classList.remove('active');
        } else if (index === currentIndex) {
            progressStep.classList.add('active');
            progressStep.classList.remove('completed');
        } else {
            progressStep.classList.remove('active', 'completed');
        }
    });
}

// Mark step as complete
function markStepComplete(stepName) {
    const progressStep = document.getElementById(`progress-${stepName}`);
    if (progressStep) {
        progressStep.classList.add('completed');
    }
}

// Go to previous step
function goToPreviousStep(stepName) {
    showStep(stepName);
}

// Email form submission
document.getElementById('emailForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const errorElement = document.getElementById('emailError');
    errorElement.style.display = 'none';
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/checkout/step/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: checkoutSessionId,
                email: email
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save email');
        }
        
        markStepComplete('email');
        showStep('phone');
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Phone form submission
document.getElementById('phoneForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const phone = document.getElementById('phone').value;
    const errorElement = document.getElementById('phoneError');
    errorElement.style.display = 'none';
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/checkout/step/phone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: checkoutSessionId,
                phone: phone
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save phone');
        }
        
        markStepComplete('phone');
        showStep('address');
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Address form submission
document.getElementById('addressForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorElement = document.getElementById('addressError');
    errorElement.style.display = 'none';
    
    const addressData = {
        session_id: checkoutSessionId,
        address_line1: document.getElementById('address1').value,
        address_line2: document.getElementById('address2').value || null,
        city: document.getElementById('city').value,
        postal_code: document.getElementById('postal').value,
        country: document.getElementById('country').value
    };
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/checkout/step/address`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(addressData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save address');
        }
        
        const progress = await response.json();
        
        markStepComplete('address');
        
        // Update summary
        document.getElementById('summary-plan').textContent = progress.selected_plan.toUpperCase();
        document.getElementById('summary-email').textContent = progress.email;
        
        showStep('payment');
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Proceed to payment
document.getElementById('proceedToPayment').addEventListener('click', async () => {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/checkout/create-payment?session_id=${checkoutSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error('Failed to create payment session');
        }
        
        const data = await response.json();
        
        // Clear checkout session from localStorage
        localStorage.removeItem('checkoutSessionId');
        
        // Redirect to Stripe
        window.location.href = data.checkout_url;
    } catch (error) {
        console.error('Error creating payment:', error);
        alert('Failed to proceed to payment. Please try again.');
    } finally {
        showLoading(false);
    }
});

// Loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Initialize on page load
initializeCheckout();

