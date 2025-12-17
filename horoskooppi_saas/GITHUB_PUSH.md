# 🐙 Push to GitHub

## Quick Commands

```bash
# 1. Navigate to project
cd /Users/leevikangas/Code/NousParadigma/horoskooppi_saas

# 2. Add GitHub remote (replace with YOUR repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 3. Push to GitHub
git push -u origin main
```

## Using SSH (Recommended)

If you have SSH keys set up on GitHub:

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## What's Being Pushed

✅ **32 files**
✅ **5,902 lines of code**

### Complete Nous Paradeigma SaaS:
- ✨ FastAPI backend with JWT auth
- 💳 Stripe subscription integration
- 🤖 Google Gemini AI horoscope generation
- 🎨 NOUS PARADEIGMA branded frontend
- 💰 4-tier pricing (Lifetime + 3 monthly)
- 📱 Multi-step checkout flow
- 📊 Conversion funnel analytics
- 🌍 Bilingual (EN/FI)
- 📹 Videos (woman.mov, timantti.gif)
- 🔮 Circle Gatherings feature
- 🛍️ Cosmic Merch Store section
- 💬 Testimonials
- 🛡️ Trust badges
- ❓ FAQ section
- 📚 Complete documentation

## After Pushing

Your repository will be live at:
```
https://github.com/YOUR_USERNAME/YOUR_REPO_NAME
```

## Set Up GitHub Actions (Optional)

Create `.github/workflows/deploy.yml` for CI/CD:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: echo "Add your deployment commands here"
```

## Add Secrets to GitHub

Go to: **Settings** → **Secrets and variables** → **Actions**

Add these secrets:
- `SECRET_KEY`
- `GEMINI_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_PRICE_ID_STARLIGHT`
- `STRIPE_PRICE_ID_COSMIC`
- `STRIPE_PRICE_ID_CELESTIAL`
- `STRIPE_PRICE_ID_LIFETIME`
- `STRIPE_WEBHOOK_SECRET`

## Future Updates

```bash
# Make changes, then:
git add .
git commit -m "Your update message"
git push
```

---

**Ready to push!** 🚀



