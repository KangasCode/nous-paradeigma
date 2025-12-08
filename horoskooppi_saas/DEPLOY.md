# 🚀 GitLab Deployment Guide

## Push to GitLab

### Step 1: Create GitLab Repository

1. Go to https://gitlab.com
2. Click **"New project"** → **"Create blank project"**
3. Name: `nous-paradeigma-horoscope-saas`
4. Visibility: Choose Private or Public
5. **Do NOT** initialize with README (we have one)
6. Click **"Create project"**

### Step 2: Connect and Push

```bash
# Navigate to project
cd /Users/leevikangas/Code/NousParadigma/horoskooppi_saas

# Add GitLab remote (replace with YOUR URL)
git remote add origin https://gitlab.com/YOUR_USERNAME/nous-paradeigma-horoscope-saas.git

# Push to GitLab
git push -u origin main
```

### Using SSH (Recommended)

If you have SSH keys set up:

```bash
git remote add origin git@gitlab.com:YOUR_USERNAME/nous-paradeigma-horoscope-saas.git
git push -u origin main
```

## 📊 What's Being Pushed

✅ **32 files**  
✅ **5,902 lines of code**

### Included:
- ✨ Complete backend (FastAPI, SQLAlchemy, Stripe, Gemini)
- 🎨 Complete frontend (HTML, CSS, JS with NOUS PARADEIGMA branding)
- 💳 Multi-step checkout flow with analytics
- 📱 Responsive design
- 🌍 Bilingual (EN/FI)
- 📹 Videos and assets
- 📝 Complete documentation

## 🔐 Before Pushing

Make sure `.env` is NOT committed (it's in `.gitignore`):

```bash
# Check what's being pushed
git status

# Should NOT see .env in the list
# Should see .env.example ✓
```

## 🎯 After Pushing

### Set up GitLab CI/CD (Optional)

Create `.gitlab-ci.yml` for auto-deployment:

```yaml
deploy:
  stage: deploy
  script:
    - echo "Deploy to production"
  only:
    - main
```

### Set up Environment Variables in GitLab

1. Go to **Settings** → **CI/CD** → **Variables**
2. Add these secrets:
   - `SECRET_KEY`
   - `GEMINI_API_KEY`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PRICE_ID_*`
   - `STRIPE_WEBHOOK_SECRET`

## 🚀 Quick Deploy Commands

```bash
# First time
git remote add origin YOUR_GITLAB_URL
git push -u origin main

# Future updates
git add .
git commit -m "Your update message"
git push
```

## 📦 Project Stats

```
Backend:        8 Python files
Frontend:       4 HTML + 2 JS + 1 CSS
Documentation:  3 MD files
Assets:         5 media files
Total:          32 files, ~6k lines
```

---

**Your complete Nous Paradeigma SaaS is ready to deploy!** 🌟


