# 🚀 Render.com Deployment Guide

## Test Site (Demo Mode) - Track Checkouts Without Payment

### Step 1: Create Web Service on Render

1. Go to: https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `KangasCode/nous-paradeigma`

### Step 2: Configure Service

```
Name: nous-paradeigma-2
Region: Frankfurt (or closest to you)
Branch: main
Root Directory: backend
Runtime: Python 3
```

### Step 3: Build & Start Commands

```
Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 4: Environment Variables (DEMO MODE)

Click **"Advanced"** → **"Add Environment Variable"**:

```
SECRET_KEY=your-secret-key-generate-with-python
DEMO_MODE=true
BASE_URL=https://nous-paradeigma-2.onrender.com
DATABASE_URL=(Render auto-provides PostgreSQL)
GEMINI_API_KEY=not-needed-in-demo-mode
STRIPE_SECRET_KEY=not-needed-in-demo-mode
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Create PostgreSQL Database (Optional)

If you want persistent data:
1. Click **"New +"** → **"PostgreSQL"**
2. Name: `nous-paradeigma-db`
3. Copy the **Internal Database URL**
4. Add it as `DATABASE_URL` in your web service

Or just use the default SQLite (data resets on redeploy).

## 🧪 Demo Mode Features

When `DEMO_MODE=true`:

✅ **Checkout flow works** - all 4 steps
✅ **Data is saved** to database
✅ **Analytics work** - see conversion rates
✅ **No Stripe required** - skips payment
✅ **No Gemini required** - uses fallback horoscopes
✅ Users go to success page after completing checkout

### What You Can Track:

- How many click "Subscribe"
- How many complete email step
- How many complete phone step
- How many complete address step
- How many reach "payment" (conversion!)

**Access analytics:**
```
https://nous-paradeigma-2.onrender.com/api/checkout/analytics
```

## 📊 View Your Funnel Data

```bash
curl https://nous-paradeigma-2.onrender.com/api/checkout/analytics
```

Returns:
```json
{
  "total_started": 45,
  "step_email_completed": 38,
  "step_phone_completed": 30,
  "step_address_completed": 25,
  "step_payment_initiated": 25,
  "step_payment_completed": 25,
  "conversion_rate": 55.5
}
```

## 🔄 When Ready for Production

Just update environment variables:
1. Set `DEMO_MODE=false`
2. Add real `GEMINI_API_KEY`
3. Add real `STRIPE_SECRET_KEY` and price IDs
4. Set up Stripe webhook

**No code changes needed!**

## 🚀 Deploy Settings Summary

```
Service Type: Web Service
Runtime: Python 3
Root Directory: backend
Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Publish Directory: (leave empty)

Environment:
- SECRET_KEY=xxx
- DEMO_MODE=true
- BASE_URL=https://nous-paradeigma-2.onrender.com
```

---

**Your test site is ready to validate demand before adding paid APIs!** 📈


