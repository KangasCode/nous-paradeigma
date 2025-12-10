# 🌟 Horoskooppi SaaS - AI-Powered Horoscope Subscription Service

A complete subscription-based web service that provides AI-powered horoscope predictions using Google Gemini API, with Stripe payment integration, JWT authentication, and a beautiful modern UI.

## 🚀 Features

- **User Authentication**: Secure registration and login with JWT tokens
- **Subscription Management**: Stripe integration for recurring billing
- **AI-Powered Horoscopes**: Generate personalized horoscopes using Google Gemini API
- **Multiple Prediction Types**: Daily, weekly, and monthly horoscopes
- **Role-Based Access**: Subscriber-only endpoints with automatic validation
- **Webhook Integration**: Automatic subscription status updates via Stripe webhooks
- **Modern UI**: Beautiful, responsive design with smooth animations
- **Production-Ready**: Modular code structure, error handling, and security best practices

## 📁 Project Structure

```
horoskooppi_saas/
├── backend/
│   ├── main.py              # FastAPI application and routes
│   ├── models.py            # SQLAlchemy database models
│   ├── database.py          # Database configuration
│   ├── auth.py              # JWT authentication and authorization
│   ├── gemini_client.py     # Google Gemini API client
│   ├── stripe_webhooks.py   # Stripe webhook handlers
│   ├── schemas.py           # Pydantic schemas for validation
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── static/
│   │   ├── app.js          # Frontend JavaScript
│   │   └── styles.css      # CSS styles
│   └── templates/
│       ├── index.html      # Landing page
│       ├── dashboard.html  # User dashboard
│       ├── success.html    # Payment success page
│       └── cancel.html     # Payment cancel page
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.12 (required for flatlib compatibility)
- pip (Python package manager)
- Google Gemini API key
- Stripe account with API keys

**Note:** Python 3.13 is not currently supported due to flatlib dependency compatibility issues.

### 1. Clone the Repository

```bash
cd horoskooppi_saas
```

### 2. Set Up Python Environment

**Important:** This project requires Python 3.12. If you have multiple Python versions:

**On macOS (using Homebrew):**
```bash
# Install Python 3.12 if not already installed
brew install python@3.12

# Navigate to backend directory
cd backend

# Create virtual environment with Python 3.12
python3.12 -m venv venv
```

**On Linux:**
```bash
# Install Python 3.12 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv

# Navigate to backend directory
cd backend

# Create virtual environment with Python 3.12
python3.12 -m venv venv
```

**Activate virtual environment:**
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Verify Python version:**
```bash
python --version  # Should show Python 3.12.x
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp ../.env.example ../.env

# Edit the .env file with your actual credentials
nano ../.env  # or use your preferred editor
```

**Required Environment Variables:**

- `SECRET_KEY`: Generate a secure random string (minimum 32 characters)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

- `STRIPE_SECRET_KEY`: Get from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)

- `STRIPE_PRICE_ID`: Create a subscription product in Stripe and copy the price ID

- `STRIPE_WEBHOOK_SECRET`: Set up a webhook endpoint in Stripe and copy the signing secret

### 4. Set Up Stripe

1. **Create a Product:**
   - Go to [Stripe Dashboard → Products](https://dashboard.stripe.com/products)
   - Create a new product (e.g., "Premium Horoscope Subscription")
   - Add a recurring price (e.g., $9.99/month)
   - Copy the Price ID (starts with `price_...`)

2. **Set Up Webhook:**
   - Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
   - Click "Add endpoint"
   - Set endpoint URL: `http://localhost:8000/api/stripe/webhook` (or your production URL)
   - Select events to listen to:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
   - Copy the Webhook signing secret (starts with `whsec_...`)

### 5. Initialize Database

The database will be automatically initialized when you first run the application. By default, it uses SQLite for local development.

### 6. Run the Application

```bash
# Make sure you're in the backend directory with venv activated
cd backend
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at: `http://localhost:8000`

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (requires auth)

### Stripe/Subscription
- `POST /api/stripe/create-checkout-session` - Create Stripe checkout session
- `POST /api/stripe/create-portal-session` - Create customer portal session
- `POST /api/stripe/webhook` - Handle Stripe webhooks
- `GET /api/subscription/status` - Get subscription status

### Horoscopes (Subscriber Only)
- `POST /api/horoscopes/generate` - Generate new horoscope
- `GET /api/horoscopes/my` - Get user's horoscopes
- `GET /api/horoscopes/{id}` - Get specific horoscope

### Pages
- `GET /` - Landing page
- `GET /dashboard` - User dashboard
- `GET /success` - Payment success page
- `GET /cancel` - Payment cancel page

## 🧪 Testing the Application

### 1. Test User Registration and Login
1. Go to `http://localhost:8000`
2. Click "Get Started" or "Register"
3. Fill in your details and create an account
4. You'll be automatically logged in and redirected to the dashboard

### 2. Test Subscription Flow
1. On the dashboard, click "Subscribe Now"
2. You'll be redirected to Stripe Checkout
3. Use Stripe test card: `4242 4242 4242 4242`
4. Use any future expiry date, any CVC, and any ZIP code
5. Complete the payment
6. You'll be redirected back to the success page

### 3. Test Horoscope Generation
1. After subscribing, go to the dashboard
2. Select your zodiac sign
3. Choose prediction type (daily/weekly/monthly)
4. Click "Generate Horoscope"
5. Wait for the AI to generate your personalized horoscope

### 4. Test Webhook Locally (Optional)

To test webhooks locally, you can use Stripe CLI:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe  # macOS
# or download from https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/stripe/webhook

# Trigger test events
stripe trigger checkout.session.completed
```

## 🚀 Deployment

### Prerequisites for Production

1. **Database**: Switch from SQLite to PostgreSQL
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/horoskooppi
   ```

2. **Secret Key**: Generate a strong secret key
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Update BASE_URL and SITE_URL**: Set to your production domain
   ```env
   BASE_URL=https://nousparadeigma.com
   SITE_URL=https://nousparadeigma.com
   ```

4. **Update Stripe Webhook**: Point to your production webhook endpoint

### Deploy to Popular Platforms

#### Deploy to Railway.app

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and initialize:
   ```bash
   railway login
   railway init
   ```

3. Add environment variables in Railway dashboard

4. Deploy:
   ```bash
   railway up
   ```

#### Deploy to Heroku

1. Create `Procfile`:
   ```
   web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set GEMINI_API_KEY=your-gemini-key
   # ... set other environment variables
   git push heroku main
   ```

#### Deploy to DigitalOcean/AWS/GCP

1. Set up a server with Python 3.9+
2. Install dependencies
3. Set up environment variables
4. Use a process manager like systemd or supervisor
5. Set up Nginx as reverse proxy
6. Configure SSL with Let's Encrypt

Example systemd service file:

```ini
[Unit]
Description=Horoskooppi FastAPI
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/horoskooppi/backend
Environment="PATH=/var/www/horoskooppi/backend/venv/bin"
EnvironmentFile=/var/www/horoskooppi/.env
ExecStart=/var/www/horoskooppi/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use strong SECRET_KEY** - Minimum 32 characters, random
3. **Use HTTPS in production** - Protect JWT tokens in transit
4. **Verify Stripe webhooks** - Always validate webhook signatures
5. **Rate limiting** - Consider adding rate limiting middleware
6. **Input validation** - All inputs are validated using Pydantic schemas
7. **SQL injection protection** - Using SQLAlchemy ORM prevents SQL injection
8. **Password hashing** - Passwords are hashed using bcrypt

## 📝 Database Schema

### Users Table
- id (Primary Key)
- email (Unique)
- hashed_password
- full_name
- is_active
- is_subscriber
- created_at

### Subscriptions Table
- id (Primary Key)
- user_id (Foreign Key → Users)
- stripe_customer_id (Unique)
- stripe_subscription_id (Unique)
- status (active/inactive/canceled/past_due)
- current_period_start
- current_period_end
- created_at
- updated_at

### Horoscopes Table
- id (Primary Key)
- user_id (Foreign Key → Users)
- zodiac_sign
- prediction_type (daily/weekly/monthly)
- content (Text)
- created_at
- prediction_date

## 🎨 Customization

### Modify Pricing
Update the price in Stripe Dashboard and the frontend `index.html`

### Change Color Scheme
Edit CSS variables in `frontend/static/styles.css`:
```css
:root {
    --primary-color: #6366f1;
    --primary-dark: #4f46e5;
    /* ... */
}
```

### Customize Horoscope Prompts
Edit prompts in `backend/gemini_client.py` in the `_create_prompt` method

### Add More Zodiac Features
Extend the models and add new endpoints in `backend/main.py`

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution**: Make sure virtual environment is activated and dependencies are installed
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: "Could not validate credentials"
**Solution**: Check that JWT token is being sent in Authorization header and SECRET_KEY matches

### Issue: Stripe webhook not working
**Solution**: 
- Verify webhook URL is correct
- Check STRIPE_WEBHOOK_SECRET is set
- Use Stripe CLI for local testing

### Issue: Gemini API errors
**Solution**: 
- Verify GEMINI_API_KEY is valid
- Check API quota/limits
- Fallback horoscope will be used if API fails

## 📚 Technologies Used

- **Backend**: FastAPI, SQLAlchemy, Python 3.12
- **Authentication**: JWT (python-jose), bcrypt
- **Payment**: Stripe API
- **AI**: Google Gemini API
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Stripe and Gemini API documentation
3. Check application logs for detailed error messages

## 🎉 Features to Add (Future Enhancements)

- [ ] Email notifications for horoscope generation
- [ ] Social sharing functionality
- [ ] Multiple user profiles/zodiac signs per account
- [ ] Horoscope history export (PDF/CSV)
- [ ] Admin dashboard for analytics
- [ ] Mobile app (React Native/Flutter)
- [ ] Compatibility readings between signs
- [ ] Birth chart analysis
- [ ] Push notifications
- [ ] Multi-language support

---

**Built with ❤️ using FastAPI, Stripe, and Google Gemini AI**


