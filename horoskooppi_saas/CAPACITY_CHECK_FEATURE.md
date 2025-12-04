# Capacity Check Feature

## Overview
This feature adds an exclusive "capacity check" step in the checkout process that creates scarcity and urgency by showing customers that memberships are limited.

## How It Works

### Customer Experience
1. Customer completes Email, Phone, and Address steps
2. **NEW: Capacity Check Step** - Shows a 2.5 second animation checking "membership availability"
3. Two possible outcomes:
   - **Capacity Full (Default)**: Shows waitlist form where customer can join priority waiting list
   - **Capacity Available**: Automatically continues to payment step

### Visual Flow
```
Email → Phone → Address → Capacity Check → Payment
                              ↓
                         Waitlist Form
```

## Configuration

### Environment Variable
Control whether capacity is full or available:

```bash
# Show waitlist (default behavior)
CAPACITY_FULL=true

# Allow checkouts (open capacity)
CAPACITY_FULL=false
```

**Location**: Add this to your `.env` file or set in your deployment environment (e.g., Render.com environment variables)

### Default Behavior
- **Default**: `CAPACITY_FULL=true` - Shows waitlist to create exclusivity
- When capacity is open, users are automatically directed to payment after the animation

## Features

### 1. Animated Capacity Check
- Beautiful spinning animation with pulsing effect
- Shows for 2.5 seconds to create anticipation
- Three animated dots for loading effect
- Uses brand colors (gold/celestial theme)

### 2. Waitlist System
When capacity is full:
- Shows elegant message explaining exclusivity
- Collects email for priority waiting list
- Prevents duplicate waitlist entries
- Success message after joining
- Stores waitlist data in database

### 3. Backend Tracking
All waitlist submissions are stored with:
- Email address
- Session ID
- Selected plan (which tier they wanted)
- Timestamp
- Notification status (for future use)

## API Endpoints

### Check Capacity Status
```http
GET /api/checkout/capacity-status
```

Response:
```json
{
  "is_full": true,
  "message": "We're currently at full capacity"
}
```

### Join Waitlist
```http
POST /api/checkout/waitlist
Content-Type: application/json

{
  "session_id": "abc123...",
  "email": "customer@example.com"
}
```

Response:
```json
{
  "success": true,
  "message": "You've been added to the priority waiting list!"
}
```

### Get Waitlist Count
```http
GET /api/checkout/waitlist/count
```

Response:
```json
{
  "total": 42
}
```

## Database

### New Table: `waitlist`
Fields:
- `id` (Primary Key)
- `session_id` (Links to checkout session)
- `email` (Customer email)
- `selected_plan` (Which plan they wanted)
- `created_at` (Timestamp)
- `notified` (Boolean - tracked for future notifications)
- `notified_at` (When they were notified about opening)

## Styling

All styles follow the Nous Paradeigma brand guidelines:
- **Colors**: Muted gold (#C1A15A), Celestial blue (#6A88FF)
- **Animations**: Smooth, mystical feel
- **Typography**: Space Grotesk font family
- **Effects**: Glow effects, backdrop blur, gradient backgrounds

## Marketing Strategy

### Why This Works
1. **Scarcity**: Creates urgency by limiting access
2. **Exclusivity**: Makes customers feel special to be on priority list
3. **FOMO**: Fear of missing out drives action
4. **Data Collection**: Captures interested leads even when "closed"
5. **Perceived Value**: Limited access = higher value perception

### Recommended Usage
- **Launch Phase**: Keep `CAPACITY_FULL=true` to build waitlist
- **Flash Opens**: Periodically set to `false` and email waitlist
- **Tiered Access**: Different plans could have different availability
- **Special Events**: Open capacity for limited time promotions

## Future Enhancements

### Possible Additions
1. **Email Notifications**: Auto-email waitlist when capacity opens
2. **Admin Dashboard**: Manage waitlist, notify users manually
3. **Per-Plan Capacity**: Different limits for different tiers
4. **Dynamic Limits**: Auto-close when X subscribers reached
5. **VIP Codes**: Allow certain users to bypass capacity check
6. **Analytics**: Track conversion from waitlist to purchase

## Testing

### Test Capacity Full (Waitlist)
```bash
# Set environment variable
export CAPACITY_FULL=true

# Restart server
cd horoskooppi_saas/backend
source venv/bin/activate
uvicorn main:app --reload
```

Navigate to checkout and complete through address step. You should see the capacity check animation followed by the waitlist form.

### Test Capacity Available
```bash
# Set environment variable
export CAPACITY_FULL=false

# Restart server
```

Navigate to checkout and complete through address step. You should see the capacity check animation followed by automatic redirect to payment.

### View Waitlist Entries
```bash
# Option 1: Check database directly
sqlite3 horoskooppi_saas/backend/horoskooppi.db
sqlite> SELECT * FROM waitlist;

# Option 2: API call
curl http://localhost:8000/api/checkout/waitlist/count
```

## Deployment

### On Render.com (or similar)
1. Add environment variable in dashboard:
   - Key: `CAPACITY_FULL`
   - Value: `true` (or `false`)

2. Deploy/restart your service

3. The database will automatically create the `waitlist` table on first run

### Local Development
1. Add to your `.env` file or export in terminal
2. Restart FastAPI server
3. Test both capacity states

## Support

If you encounter issues:
1. Check server logs for errors
2. Verify `CAPACITY_FULL` environment variable is set
3. Ensure database was reinitialized (restart server once)
4. Check browser console for JavaScript errors
5. Verify `/api/checkout/capacity-status` endpoint returns expected data

## Customization

### Change Animation Duration
In `checkout.js`, line ~248:
```javascript
setTimeout(() => {
    // ...
}, 2500); // Change 2500 to desired milliseconds (2500 = 2.5 seconds)
```

### Customize Messages
Edit `checkout.html` around line 106-120 to change:
- Waitlist headline
- Description text
- Call-to-action wording

### Modify Styling
Edit `styles.css` starting at line ~2688:
- `.capacity-checking` - Animation styles
- `.capacity-waitlist` - Waitlist form styles
- `.capacity-spinner` - Spinner appearance
- Animation keyframes for effects

