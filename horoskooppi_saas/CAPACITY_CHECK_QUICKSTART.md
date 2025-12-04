# Capacity Check - Quick Start Guide

## 🚀 Quick Setup (2 minutes)

### Step 1: Set Environment Variable
Choose one of these methods:

**Method A: Terminal (Temporary)**
```bash
cd horoskooppi_saas/backend
export CAPACITY_FULL=true  # Show waitlist (default)
# OR
export CAPACITY_FULL=false  # Allow checkouts
```

**Method B: Create .env file (Permanent)**
```bash
cd horoskooppi_saas/backend
echo "CAPACITY_FULL=true" >> .env
```

### Step 2: Start Server
```bash
cd horoskooppi_saas/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Step 3: Test It!
1. Open browser: `http://localhost:8000`
2. Click any "Get Started" button
3. Fill out Email, Phone, and Address
4. Watch the capacity check animation! 🎭

---

## 🎬 What You'll See

### With CAPACITY_FULL=true (Default)
1. ✨ 2.5 second animation showing "Verifying Membership Availability"
2. 🌟 Message: "We're At Full Capacity"  
3. 📧 Waitlist form to join priority list
4. ✅ Success message after submitting

### With CAPACITY_FULL=false
1. ✨ Same 2.5 second animation
2. ➡️ Automatically proceeds to payment step
3. 💳 Normal checkout continues

---

## 📊 Check Waitlist Data

### View in Database
```bash
cd horoskooppi_saas/backend
sqlite3 horoskooppi.db "SELECT email, selected_plan, created_at FROM waitlist;"
```

### Via API
```bash
# Get count
curl http://localhost:8000/api/checkout/waitlist/count

# Example response: {"total": 5}
```

---

## 🔄 Switch Between Modes

### Open Capacity (Accept Customers)
```bash
export CAPACITY_FULL=false
# Restart server
```

### Close Capacity (Show Waitlist)
```bash
export CAPACITY_FULL=true
# Restart server
```

**Note**: Change takes effect immediately after server restart.

---

## 🎨 Customization

### Change Animation Duration
Edit: `frontend/static/checkout.js` line ~248
```javascript
setTimeout(() => {
    // ...
}, 2500); // milliseconds (2500 = 2.5 sec)
```

### Change Messages
Edit: `frontend/templates/checkout.html` lines 106-145
- Update headline text
- Change waitlist description
- Modify call-to-action

### Update Styles
Edit: `frontend/static/styles.css` lines 2688+
- Modify colors
- Adjust animation speed
- Change spacing/sizing

---

## ✅ Testing Checklist

- [ ] Start server with `CAPACITY_FULL=true`
- [ ] Complete checkout to address step
- [ ] See capacity checking animation (2.5 sec)
- [ ] See waitlist form appear
- [ ] Submit email to waitlist
- [ ] See success message
- [ ] Check database has entry
- [ ] Set `CAPACITY_FULL=false` and restart
- [ ] Complete checkout again
- [ ] Verify it proceeds to payment automatically

---

## 🐛 Troubleshooting

### "Waitlist form doesn't appear"
- Check: Is `CAPACITY_FULL=true`?
- Check: Did you restart server after setting variable?
- Check browser console for errors (F12)

### "Animation stuck/frozen"
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Check server is running
- Check browser console for JS errors

### "Database error"
- Restart server once to create tables
- Check `horoskooppi.db` file exists
- View logs in terminal

### "Variable not working"
- Test endpoint directly: `curl http://localhost:8000/api/checkout/capacity-status`
- Should see: `{"is_full": true, ...}` or `{"is_full": false, ...}`
- If wrong, check environment variable spelling

---

## 📈 Recommended Strategy

### Phase 1: Build Waitlist (Week 1-2)
```bash
CAPACITY_FULL=true
```
- Collect interested customers
- Create urgency and demand
- Build email list for launch

### Phase 2: Limited Opening (Week 3)
```bash
CAPACITY_FULL=false
```
- Email waitlist: "Spots just opened!"
- Keep open for 24-48 hours
- Convert waitlist to customers

### Phase 3: Close Again (Week 4)
```bash
CAPACITY_FULL=true
```
- Back to waitlist mode
- Maintain exclusivity
- Repeat cycle monthly

---

## 🚀 Deploy to Production

### Render.com / Heroku / etc.
1. Go to environment variables section
2. Add: `CAPACITY_FULL` = `true` (or `false`)
3. Save and redeploy
4. Test: `https://your-domain.com/api/checkout/capacity-status`

### Vercel / Netlify
1. Add to environment variables in dashboard
2. Redeploy
3. Test endpoint

---

## 💡 Pro Tips

1. **Email Waitlist**: When opening capacity, send email blast to waitlist@
2. **Analytics**: Track waitlist size to gauge demand
3. **A/B Test**: Test different waitlist messages for higher conversion
4. **Scarcity**: Show "X spots remaining" for more urgency
5. **VIP Access**: Create bypass codes for special customers

---

## 📞 Support

Questions? Issues?
- Check full documentation: `CAPACITY_CHECK_FEATURE.md`
- Review server logs in terminal
- Test API endpoints with curl
- Check browser console (F12)

---

**That's it! You're ready to go!** 🎉

Start server → Set `CAPACITY_FULL` → Test checkout → Watch the magic happen ✨

