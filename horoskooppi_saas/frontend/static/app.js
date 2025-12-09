// Language translations are loaded in index.html inline script
// API Configuration
const API_BASE = '/api';

// Utility function to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

// Utility function to handle API errors
function handleApiError(error, errorElementId) {
    console.error('API Error:', error);
    const errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        errorElement.textContent = error.message || 'An error occurred. Please try again.';
        errorElement.style.display = 'block';
    }
}

// ============================================================================
// Checkout Button Handlers
// ============================================================================

// Handle all subscribe buttons on index page
function initSubscribeButtons() {
    // Get all subscribe buttons
    const subscribeButtons = document.querySelectorAll('[data-i18n="cta.subscribe"]');
    
    subscribeButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Determine which plan based on button context
            let plan = 'cosmic'; // default
            
            const card = button.closest('.pricing-card, .lifetime-card');
            if (card) {
                const titleElement = card.querySelector('.pricing-title, .lifetime-title');
                if (titleElement) {
                    const title = titleElement.textContent.toLowerCase();
                    if (title.includes('starlight')) plan = 'starlight';
                    else if (title.includes('cosmic')) plan = 'cosmic';
                    else if (title.includes('celestial')) plan = 'celestial';
                    else if (title.includes('eternal') || title.includes('lifetime')) plan = 'lifetime';
                }
            }
            
            // Store plan and redirect to checkout
            localStorage.setItem('selectedPlan', plan);
            window.location.href = `/checkout?plan=${plan}`;
        });
    });
}

// ============================================================================
// Index Page (Landing Page)
// ============================================================================

if (window.location.pathname === '/') {
    // Initialize subscribe buttons
    initSubscribeButtons();
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const showLoginBtns = document.querySelectorAll('#showLogin');
    const showRegisterBtns = document.querySelectorAll('#showRegister, #ctaRegister, #pricingCta');
    const closeBtns = document.querySelectorAll('.close');
    const switchToRegister = document.getElementById('switchToRegister');
    const switchToLogin = document.getElementById('switchToLogin');

    // Show login modal
    showLoginBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            loginModal.style.display = 'flex';
            registerModal.style.display = 'none';
        });
    });

    // Show register modal
    showRegisterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            registerModal.style.display = 'flex';
            loginModal.style.display = 'none';
        });
    });

    // Close modals
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            loginModal.style.display = 'none';
            registerModal.style.display = 'none';
        });
    });

    // Switch between modals
    if (switchToRegister) {
        switchToRegister.addEventListener('click', (e) => {
            e.preventDefault();
            loginModal.style.display = 'none';
            registerModal.style.display = 'flex';
        });
    }

    if (switchToLogin) {
        switchToLogin.addEventListener('click', (e) => {
            e.preventDefault();
            registerModal.style.display = 'none';
            loginModal.style.display = 'flex';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.style.display = 'none';
        }
        if (e.target === registerModal) {
            registerModal.style.display = 'none';
        }
    });

    // Login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const errorElement = document.getElementById('loginError');
            errorElement.style.display = 'none';

            try {
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (!response.ok) {
                    let errorMessage = 'Login failed';
                    // Clone response to allow multiple reads
                    const clonedResponse = response.clone();
                    // Check content type before trying to parse
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        try {
                            const error = await clonedResponse.json();
                            errorMessage = error.detail || errorMessage;
                        } catch (e) {
                            console.error('Error parsing JSON error:', e);
                            errorMessage = `Server error: ${response.status}`;
                        }
                    } else {
                        // Not JSON, try to get text
                        try {
                            const text = await clonedResponse.text();
                            errorMessage = text.substring(0, 200) || `Server error: ${response.status}`;
                        } catch (e) {
                            console.error('Error reading error text:', e);
                            errorMessage = `Server error: ${response.status}`;
                        }
                    }
                    console.error('Login failed:', errorMessage, 'Status:', response.status);
                    throw new Error(errorMessage);
                }

                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                window.location.href = '/dashboard';
            } catch (error) {
                handleApiError(error, 'loginError');
            }
        });
    }

    // Register form submission
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const full_name = document.getElementById('registerName').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const errorElement = document.getElementById('registerError');
            errorElement.style.display = 'none';

            try {
                const response = await fetch(`${API_BASE}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ full_name, email, password })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Registration failed');
                }

                // Auto-login after registration
                const loginResponse = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (loginResponse.ok) {
                    const data = await loginResponse.json();
                    localStorage.setItem('token', data.access_token);
                    window.location.href = '/dashboard';
                }
            } catch (error) {
                handleApiError(error, 'registerError');
            }
        });
    }
}

// ============================================================================
// Dashboard Page
// ============================================================================

if (window.location.pathname === '/dashboard') {
    let currentUser = null;

    // Logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('token');
            window.location.href = '/';
        });
    }

    // Load user information
    async function loadUserInfo() {
        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to load user info');
            }

            currentUser = await response.json();
            const userEmailElement = document.getElementById('userEmail');
            if (userEmailElement) {
                userEmailElement.textContent = currentUser.email;
            }

            return currentUser;
        } catch (error) {
            console.error('Error loading user info:', error);
            localStorage.removeItem('token');
            window.location.href = '/';
        }
    }

    // Load subscription status
    async function loadSubscriptionStatus() {
        const statusContainer = document.getElementById('subscriptionStatus');
        
        try {
            const response = await fetch(`${API_BASE}/subscription/status`, {
                headers: getAuthHeaders()
            });

            if (response.status === 404) {
                // No subscription
                displayNoSubscription(statusContainer);
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to load subscription');
            }

            const subscription = await response.json();
            displaySubscriptionInfo(statusContainer, subscription);
            
            // Show horoscope sections if active subscriber
            if (subscription.status === 'active') {
                document.getElementById('horoscopeGenerator').style.display = 'block';
                document.getElementById('previousHoroscopes').style.display = 'block';
                loadPreviousHoroscopes();
            }
        } catch (error) {
            console.error('Error loading subscription:', error);
            displayNoSubscription(statusContainer);
        }
    }

    function displayNoSubscription(container) {
        container.innerHTML = `
            <div class="subscription-card inactive">
                <h3>No Active Subscription</h3>
                <p>Subscribe now to unlock AI-powered horoscope predictions!</p>
                <button id="subscribeBtn" class="btn btn-primary">Subscribe Now - $9.99/month</button>
            </div>
        `;

        document.getElementById('subscribeBtn').addEventListener('click', createCheckoutSession);
    }

    function displaySubscriptionInfo(container, subscription) {
        const statusClass = subscription.status === 'active' ? 'active' : 'inactive';
        const statusText = subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1);
        
        let periodInfo = '';
        if (subscription.current_period_end) {
            const endDate = new Date(subscription.current_period_end);
            periodInfo = `<p>Renews on: ${endDate.toLocaleDateString()}</p>`;
        }

        container.innerHTML = `
            <div class="subscription-card ${statusClass}">
                <h3>Subscription Status: ${statusText}</h3>
                ${periodInfo}
                ${subscription.status === 'active' ? 
                    '<button id="manageBtn" class="btn btn-ghost">Manage Subscription</button>' : 
                    '<button id="subscribeBtn" class="btn btn-primary">Subscribe Now</button>'}
            </div>
        `;

        const manageBtn = document.getElementById('manageBtn');
        if (manageBtn) {
            manageBtn.addEventListener('click', createPortalSession);
        }

        const subscribeBtn = document.getElementById('subscribeBtn');
        if (subscribeBtn) {
            subscribeBtn.addEventListener('click', createCheckoutSession);
        }
    }

    // Create Stripe checkout session
    async function createCheckoutSession() {
        try {
            const response = await fetch(`${API_BASE}/stripe/create-checkout-session`, {
                method: 'POST',
                headers: getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to create checkout session');
            }

            const data = await response.json();
            window.location.href = data.checkout_url;
        } catch (error) {
            console.error('Error creating checkout session:', error);
            alert('Failed to start checkout. Please try again.');
        }
    }

    // Create Stripe portal session
    async function createPortalSession() {
        try {
            const response = await fetch(`${API_BASE}/stripe/create-portal-session`, {
                method: 'POST',
                headers: getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to create portal session');
            }

            const data = await response.json();
            window.location.href = data.portal_url;
        } catch (error) {
            console.error('Error creating portal session:', error);
            alert('Failed to open subscription management. Please try again.');
        }
    }

    // Generate horoscope
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const zodiacSign = document.getElementById('zodiacSign').value;
            const predictionType = document.getElementById('predictionType').value;
            const errorElement = document.getElementById('generateError');
            errorElement.style.display = 'none';

            if (!zodiacSign) {
                errorElement.textContent = 'Please select your zodiac sign';
                errorElement.style.display = 'block';
                return;
            }

            // Show loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            loadingOverlay.style.display = 'flex';

            try {
                const response = await fetch(`${API_BASE}/horoscopes/generate`, {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        zodiac_sign: zodiacSign,
                        prediction_type: predictionType
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to generate horoscope');
                }

                const horoscope = await response.json();
                displayHoroscope(horoscope);
                loadPreviousHoroscopes(); // Refresh the list
            } catch (error) {
                handleApiError(error, 'generateError');
            } finally {
                loadingOverlay.style.display = 'none';
            }
        });
    }

    // Display horoscope
    function displayHoroscope(horoscope) {
        const container = document.getElementById('horoscopeContent');
        const section = document.getElementById('currentHoroscope');
        
        const date = new Date(horoscope.created_at);
        const formattedDate = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        // Parse raw data if available
        let rawDataHtml = '';
        if (horoscope.raw_data) {
            try {
                const rawData = JSON.parse(horoscope.raw_data);
                if (rawData && rawData.positions) {
                    const planetItems = Object.entries(rawData.positions).map(([planet, data]) => `
                        <div class="planet-item">
                            <span class="planet-name">${planet}</span>
                            <span class="planet-sign">${data.sign}</span>
                            <span class="planet-deg">${data.deg.toFixed(2)}°</span>
                        </div>
                    `).join('');
                    
                    rawDataHtml = `
                        <div class="astrology-data">
                            <h4>Current Planetary Positions</h4>
                            <div class="planet-grid">
                                ${planetItems}
                            </div>
                        </div>
                    `;
                }
            } catch (e) {
                console.error("Error parsing raw data", e);
            }
        }

        container.innerHTML = `
            <div class="horoscope-card">
                <div class="horoscope-header">
                    <h3>${horoscope.zodiac_sign.charAt(0).toUpperCase() + horoscope.zodiac_sign.slice(1)}</h3>
                    <span class="horoscope-type">${horoscope.prediction_type}</span>
                </div>
                <div class="horoscope-date">${formattedDate}</div>
                <div class="horoscope-text">${horoscope.content.replace(/\n/g, '<br>')}</div>
                ${rawDataHtml}
            </div>
        `;

        section.style.display = 'block';
        section.scrollIntoView({ behavior: 'smooth' });
    }

    // Load previous horoscopes
    async function loadPreviousHoroscopes() {
        try {
            const response = await fetch(`${API_BASE}/horoscopes/my?limit=5`, {
                headers: getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to load horoscopes');
            }

            const horoscopes = await response.json();
            const container = document.getElementById('horoscopesList');

            if (horoscopes.length === 0) {
                container.innerHTML = '<p class="no-data">No horoscopes yet. Generate your first one above!</p>';
                return;
            }

            container.innerHTML = horoscopes.map(h => {
                const date = new Date(h.created_at);
                const formattedDate = date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric'
                });

                return `
                    <div class="horoscope-item">
                        <div class="horoscope-item-header">
                            <span class="horoscope-sign">${h.zodiac_sign.charAt(0).toUpperCase() + h.zodiac_sign.slice(1)}</span>
                            <span class="horoscope-badge">${h.prediction_type}</span>
                            <span class="horoscope-date-small">${formattedDate}</span>
                        </div>
                        <div class="horoscope-preview">${h.content.substring(0, 150)}...</div>
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('Error loading previous horoscopes:', error);
        }
    }

    // Initialize dashboard
    loadUserInfo().then(() => {
        loadSubscriptionStatus();
    });
}

