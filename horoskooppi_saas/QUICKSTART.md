# 🚀 Quick Start Guide

## One-Command Start (macOS/Linux)

```bash
./start.sh
```

## Manual Start

### 1. Setup Environment (First Time Only)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor

# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

Visit: **http://localhost:8000**

## 🔑 Required API Keys

### 1. Google Gemini API Key
- Get from: https://makersuite.google.com/app/apikey
- Free tier available
- Add to `.env` as `GEMINI_API_KEY`

### 2. Stripe API Keys
- Get from: https://dashboard.stripe.com/apikeys
- Need: `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`
- Test mode is fine for development

### 3. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy output to `.env` as `SECRET_KEY`

## 🧪 Test with Stripe

Use Stripe test card:
- **Card Number**: 4242 4242 4242 4242
- **Expiry**: Any future date
- **CVC**: Any 3 digits
- **ZIP**: Any 5 digits

## 📁 Project Structure

```
horoskooppi_saas/
├── backend/           # FastAPI backend
│   ├── main.py       # Main application
│   ├── models.py     # Database models
│   ├── auth.py       # Authentication
│   └── ...
├── frontend/         # HTML/CSS/JS frontend
│   ├── static/       # JS and CSS files
│   └── templates/    # HTML templates
├── .env.example      # Environment template
├── .env              # Your actual config (create this!)
└── README.md         # Full documentation
```

## 🎯 Key Features

✅ User registration & login with JWT
✅ Stripe subscription billing
✅ AI horoscope generation (Gemini)
✅ Beautiful responsive UI
✅ Webhook handling for subscriptions
✅ Role-based access control

## 🐛 Common Issues

**"Module not found"**
→ Activate virtual environment: `source venv/bin/activate`

**"Could not validate credentials"**
→ Check JWT token is being sent in headers

**"Stripe webhook failed"**
→ Use Stripe CLI for local testing: `stripe listen --forward-to localhost:8000/api/stripe/webhook`

**"Gemini API error"**
→ Check API key is valid and has quota remaining

## 📖 Full Documentation

See `README.md` for complete setup, deployment, and API documentation.

## 🎉 Quick Test Flow

1. Start the app: `./start.sh`
2. Register a new account
3. Subscribe using test card
4. Generate your horoscope
5. View horoscope history

---

**Need help?** Check the full README.md or application logs for detailed error messages.



