// Checkout Flow Management
const API_BASE = '/api';
let checkoutSessionId = null;
let selectedPlan = null;

// Collected data during checkout
let checkoutData = {
    email: null,
    phone: null,
    address: null,
    birthdate: null,
    birthtime: null,
    birthcity: null,
    zodiac_sign: null
};

// Get current language
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'fi';
}

// Get translation
function t(key) {
    const lang = getCurrentLanguage();
    const translations = window.checkoutTranslations || {};
    const langTranslations = translations[lang] || translations['fi'] || {};
    return langTranslations[key] || key;
}

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
        checkoutData.email = progress.email;
    }
    if (progress.phone) {
        document.getElementById('phone').value = progress.phone;
        checkoutData.phone = progress.phone;
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
    if (progress.step_birthdate_completed) {
        markStepComplete('birthdate');
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

// Update progress indicator (5 steps - capacity removed)
function updateProgressIndicator(currentStep) {
    const steps = ['email', 'phone', 'address', 'birthdate', 'payment'];
    const currentIndex = steps.indexOf(currentStep);
    
    steps.forEach((step, index) => {
        const progressStep = document.getElementById(`progress-${step}`);
        if (!progressStep) return;
        
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
        
        checkoutData.email = email;
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
        
        checkoutData.phone = phone;
        markStepComplete('phone');
        showStep('address');
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Address form submission - now goes to birthdate step
document.getElementById('addressForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorElement = document.getElementById('addressError');
    errorElement.style.display = 'none';
    
    const addressData = {
        session_id: checkoutSessionId,
        address_line1: document.getElementById('address1').value,
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
        
        checkoutData.address = addressData;
        markStepComplete('address');
        
        // Go to birthdate step (NEW!)
        showStep('birthdate');
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Birthdate form submission (NEW!)
document.getElementById('birthdateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorElement = document.getElementById('birthdateError');
    errorElement.style.display = 'none';
    
    const birthdate = document.getElementById('birthdate').value;
    const birthdateConfirm = document.getElementById('birthdateConfirm').value;
    const birthcity = document.getElementById('birthcity').value;
    
    // Validation: Check that dates match
    if (birthdate !== birthdateConfirm) {
        errorElement.textContent = t('birthdate.error.mismatch');
        errorElement.style.display = 'block';
        return;
    }
    
    // Validation: Required fields
    if (!birthdate || !birthcity) {
        errorElement.textContent = t('birthdate.error.required');
        errorElement.style.display = 'block';
        return;
    }
    
    // Calculate zodiac sign
    const zodiacSign = calculateZodiac(birthdate);
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/checkout/step/birthdate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: checkoutSessionId,
                birth_date: birthdate,
                birth_time: null,  // Can be added later in profile
                birth_city: birthcity,
                zodiac_sign: zodiacSign
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save birth date');
        }
        
        const progress = await response.json();
        
        // Store data
        checkoutData.birthdate = birthdate;
        checkoutData.birthcity = birthcity;
        checkoutData.zodiac_sign = zodiacSign;
        
        markStepComplete('birthdate');
        
        // Update summary
        document.getElementById('summary-plan').textContent = progress.selected_plan ? progress.selected_plan.toUpperCase() : selectedPlan.toUpperCase();
        document.getElementById('summary-email').textContent = (checkoutData.email || progress.email || '').toLowerCase();
        document.getElementById('summary-zodiac').textContent = zodiacSign ? (ZODIAC_DATA[zodiacSign]?.symbol + ' ' + zodiacSign.charAt(0).toUpperCase() + zodiacSign.slice(1)) : '-';
        document.getElementById('summary-birthdate').textContent = formatDate(birthdate);
        
        // Go directly to payment (capacity check removed)
        showStep('payment');
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        showLoading(false);
    }
});

// Format date for display
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fi-FI', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// Proceed to payment (FREE MODE - no actual payment)
document.getElementById('proceedToPayment').addEventListener('click', async () => {
    showLoading(true);
    
    try {
        console.log('Creating order with session:', checkoutSessionId);
        
        const response = await fetch(`${API_BASE}/checkout/create-payment?session_id=${checkoutSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Show actual error from backend
            const errorMsg = data.detail || 'Unknown error';
            console.error('Backend error:', errorMsg);
            alert(`Error: ${errorMsg}`);
            return;
        }
        
        console.log('Order completed:', data);
        
        // Clear checkout session from localStorage
        localStorage.removeItem('checkoutSessionId');
        
        // Redirect to success page
        window.location.href = data.checkout_url;
    } catch (error) {
        console.error('Error creating order:', error);
        alert('Network error. Please check your connection and try again.');
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
