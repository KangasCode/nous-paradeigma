# Test Your Deployment ✅

## Quick Deployment Check

### 1. Check if Site is Live
Visit your Render URL (example):
```
https://your-app-name.onrender.com
```

You should see the **Nous Paradeigma landing page**.

### 2. Test Capacity Check Feature

**Step-by-step:**
1. Go to your live site
2. Click any "Get Started" button
3. Fill out the checkout form:
   - Email step
   - Phone step
   - Address step
4. **Watch for the capacity check animation!** ✨
5. Should see waitlist form (since `CAPACITY_FULL=true`)

### 3. Test Waitlist Submission
1. Enter an email in the waitlist form
2. Click "Join Waiting List"
3. Should see success message

### 4. View Waitlist Dashboard
Visit:
```
https://your-app-name.onrender.com/waitlist
```

Should show:
- Capacity status (Full/Open)
- Total count of waitlist entries

### 5. Test API Endpoints

**Check capacity status:**
```bash
curl https://your-app-name.onrender.com/api/checkout/capacity-status
```

Should return:
```json
{"is_full": true, "message": "We're currently at full capacity"}
```

**Check waitlist count:**
```bash
curl https://your-app-name.onrender.com/api/checkout/waitlist/count
```

Should return:
```json
{"total": 0}
```
(or higher if you've added entries)

---

## If Something's Wrong

### Build Failed
- Check Render logs
- Verify build command: `pip install -r horoskooppi_saas/backend/requirements.txt`
- Verify start command: `cd horoskooppi_saas/backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### Site Shows Error
- Check Render logs for Python errors
- Verify all environment variables are set
- Check that `BASE_URL` matches your Render URL

### Capacity Check Not Showing
- Verify `CAPACITY_FULL` environment variable is set
- Check browser console for JavaScript errors
- Clear browser cache and refresh

### Database Errors
- Render should auto-create tables on first run
- Check logs for "Database initialized successfully"
- If issues, try manual deploy again

---

## Environment Variables Checklist

Make sure these are set in Render:

- ✅ `SECRET_KEY` (auto-generated or set)
- ✅ `DATABASE_URL` (default: `sqlite:///./horoskooppi.db`)
- ✅ `CAPACITY_FULL` (set to `true`)
- ✅ `DEMO_MODE` (set to `true` if no Stripe)
- ✅ `BASE_URL` (your Render URL)
- ⚠️ `GEMINI_API_KEY` (optional, for horoscope generation)
- ⚠️ `STRIPE_SECRET_KEY` (optional, for payments)
- ⚠️ `STRIPE_PRICE_ID` (optional, for payments)
- ⚠️ `STRIPE_WEBHOOK_SECRET` (optional, for payments)

---

## Success Indicators ✅

Your deployment is successful if:

1. ✅ Landing page loads without errors
2. ✅ Can navigate through checkout steps
3. ✅ Capacity check animation plays
4. ✅ Waitlist form appears
5. ✅ Can submit email to waitlist
6. ✅ `/waitlist` dashboard loads
7. ✅ API endpoints respond correctly

---

## Next Steps After Success

1. **Share the URL** - Your site is live!
2. **Test on mobile** - Check responsiveness
3. **Add real Stripe keys** - When ready for payments
4. **Add Gemini API key** - For AI horoscope generation
5. **Monitor logs** - Check for any errors
6. **Collect waitlist** - Start building your audience!

---

**Need help?** Check the Render logs or let me know what error you're seeing!


