"""
Automatic Prediction Scheduler Service

This service handles:
1. Generating predictions automatically for all active subscribers
2. Sending predictions via email
3. Scheduling:
   - Daily predictions: Every day at 7:00 AM (except first one after purchase)
   - Weekly predictions: Every Sunday at 7:00 AM
   - Monthly predictions: Every 30th of the month at 7:00 AM
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from models import User, Horoscope, Subscription
from gemini_client import gemini_client, GeminiAPIError
from email_service import email_service


# =============================================================================
# PREDICTION GENERATION FUNCTIONS
# =============================================================================

def generate_prediction_for_user(
    db: Session, 
    user: User, 
    prediction_type: str
) -> Optional[Horoscope]:
    """
    Generate a prediction for a specific user.
    
    Args:
        db: Database session
        user: User object
        prediction_type: 'daily', 'weekly', or 'monthly'
    
    Returns:
        Horoscope object if successful, None otherwise
    """
    if not user.zodiac_sign:
        print(f"⚠️ User {user.email} has no zodiac sign - skipping prediction")
        return None
    
    # Calculate user age
    age = None
    if user.birth_date:
        try:
            birth_date = datetime.strptime(user.birth_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except (ValueError, TypeError):
            age = None
    
    # Build user profile
    user_profile = {
        "birth_date": user.birth_date,
        "birth_time": user.birth_time,
        "birth_city": user.birth_city,
        "zodiac_sign": user.zodiac_sign,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "prediction_language": getattr(user, 'prediction_language', 'fi') or 'fi',
        "age": age
    }
    
    try:
        content, raw_data = gemini_client.generate_horoscope(
            zodiac_sign=user.zodiac_sign,
            prediction_type=prediction_type,
            user_profile=user_profile
        )
        
        # Save to database
        new_horoscope = Horoscope(
            user_id=user.id,
            zodiac_sign=user.zodiac_sign,
            prediction_type=prediction_type,
            content=content,
            raw_data=json.dumps(raw_data),
            prediction_date=datetime.utcnow()
        )
        
        db.add(new_horoscope)
        db.commit()
        db.refresh(new_horoscope)
        
        print(f"✅ Generated {prediction_type} prediction for {user.email}")
        return new_horoscope
        
    except GeminiAPIError as e:
        print(f"❌ Failed to generate {prediction_type} prediction for {user.email}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error generating prediction for {user.email}: {e}")
        db.rollback()
        return None


def get_active_subscribers(db: Session) -> List[User]:
    """Get all users with active subscriptions."""
    return db.query(User).join(Subscription).filter(
        User.is_subscriber == True,
        Subscription.status == "active"
    ).all()


# =============================================================================
# SCHEDULED JOB FUNCTIONS
# =============================================================================

async def run_daily_predictions():
    """
    Generate daily predictions for all active subscribers.
    Runs every day at 7:00 AM.
    """
    print(f"🌅 Starting daily prediction generation at {datetime.now()}")
    
    db = SessionLocal()
    try:
        subscribers = get_active_subscribers(db)
        print(f"📊 Found {len(subscribers)} active subscribers")
        
        success_count = 0
        for user in subscribers:
            horoscope = generate_prediction_for_user(db, user, "daily")
            if horoscope:
                # Send email with prediction
                send_prediction_email(user, horoscope, "daily")
                success_count += 1
        
        print(f"✅ Daily predictions completed: {success_count}/{len(subscribers)} successful")
        
    except Exception as e:
        print(f"❌ Error in daily prediction job: {e}")
    finally:
        db.close()


async def run_weekly_predictions():
    """
    Generate weekly predictions for all active subscribers.
    Runs every Sunday at 7:00 AM.
    """
    print(f"📅 Starting weekly prediction generation at {datetime.now()}")
    
    db = SessionLocal()
    try:
        subscribers = get_active_subscribers(db)
        print(f"📊 Found {len(subscribers)} active subscribers")
        
        success_count = 0
        for user in subscribers:
            horoscope = generate_prediction_for_user(db, user, "weekly")
            if horoscope:
                send_prediction_email(user, horoscope, "weekly")
                success_count += 1
        
        print(f"✅ Weekly predictions completed: {success_count}/{len(subscribers)} successful")
        
    except Exception as e:
        print(f"❌ Error in weekly prediction job: {e}")
    finally:
        db.close()


async def run_monthly_predictions():
    """
    Generate monthly predictions for all active subscribers.
    Runs every 30th of the month at 7:00 AM.
    """
    print(f"📆 Starting monthly prediction generation at {datetime.now()}")
    
    db = SessionLocal()
    try:
        subscribers = get_active_subscribers(db)
        print(f"📊 Found {len(subscribers)} active subscribers")
        
        success_count = 0
        for user in subscribers:
            horoscope = generate_prediction_for_user(db, user, "monthly")
            if horoscope:
                send_prediction_email(user, horoscope, "monthly")
                success_count += 1
        
        print(f"✅ Monthly predictions completed: {success_count}/{len(subscribers)} successful")
        
    except Exception as e:
        print(f"❌ Error in monthly prediction job: {e}")
    finally:
        db.close()


# =============================================================================
# INITIAL PREDICTIONS (AFTER PURCHASE)
# =============================================================================

def generate_initial_predictions(db: Session, user: User) -> dict:
    """
    Generate all initial predictions right after purchase.
    Creates daily, weekly, and monthly predictions immediately.
    
    Args:
        db: Database session
        user: User who just completed purchase
    
    Returns:
        Dict with results for each prediction type
    """
    print(f"🎉 Generating initial predictions for new subscriber: {user.email}")
    
    results = {
        "daily": None,
        "weekly": None,
        "monthly": None
    }
    
    for prediction_type in ["daily", "weekly", "monthly"]:
        horoscope = generate_prediction_for_user(db, user, prediction_type)
        if horoscope:
            results[prediction_type] = horoscope
    
    # Send welcome email with all initial predictions
    send_welcome_predictions_email(user, results)
    
    return results


# =============================================================================
# EMAIL SENDING FUNCTIONS
# =============================================================================

def send_prediction_email(user: User, horoscope: Horoscope, prediction_type: str) -> bool:
    """
    Send a prediction email to a user.
    
    Args:
        user: User object
        horoscope: Horoscope object with the prediction content
        prediction_type: 'daily', 'weekly', or 'monthly'
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not email_service.is_configured():
        print(f"⚠️ Email not configured - prediction for {user.email} not sent")
        return False
    
    lang = user.prediction_language or 'fi'
    user_name = user.first_name or user.full_name or None
    
    # Get translated texts
    translations = get_prediction_email_translations(prediction_type, lang)
    
    # Build email content
    site_url = os.getenv("SITE_URL", "http://localhost:8000")
    dashboard_link = f"{site_url}/dashboard"
    
    html_content = build_prediction_email_html(
        user_name=user_name,
        prediction_type=prediction_type,
        content=horoscope.content,
        zodiac_sign=horoscope.zodiac_sign,
        dashboard_link=dashboard_link,
        translations=translations
    )
    
    text_content = build_prediction_email_text(
        user_name=user_name,
        prediction_type=prediction_type,
        content=horoscope.content,
        zodiac_sign=horoscope.zodiac_sign,
        dashboard_link=dashboard_link,
        translations=translations
    )
    
    try:
        import requests
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {email_service.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": email_service.from_email,
                "to": [user.email],
                "subject": translations['subject'],
                "html": html_content,
                "text": text_content
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ {prediction_type.capitalize()} prediction email sent to {user.email}")
            return True
        else:
            print(f"❌ Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending prediction email: {e}")
        return False


def send_welcome_predictions_email(user: User, predictions: dict) -> bool:
    """
    Send welcome email with all initial predictions after purchase.
    
    Args:
        user: User object
        predictions: Dict with daily, weekly, monthly Horoscope objects
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not email_service.is_configured():
        print(f"⚠️ Email not configured - welcome predictions for {user.email} not sent")
        return False
    
    lang = user.prediction_language or 'fi'
    user_name = user.first_name or user.full_name or None
    
    translations = get_welcome_predictions_translations(lang)
    
    site_url = os.getenv("SITE_URL", "http://localhost:8000")
    dashboard_link = f"{site_url}/dashboard"
    
    # Build combined predictions content
    predictions_html = ""
    predictions_text = ""
    
    for pred_type, horoscope in predictions.items():
        if horoscope:
            type_name = translations.get(f'{pred_type}_title', pred_type.capitalize())
            predictions_html += f"""
            <tr>
                <td style="padding: 20px 40px; border-top: 1px solid rgba(138, 116, 249, 0.2);">
                    <h3 style="color: #d4af37; font-size: 18px; margin: 0 0 15px;">
                        {get_prediction_emoji(pred_type)} {type_name}
                    </h3>
                    <div style="color: #b8b8c8; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
                        {horoscope.content[:500]}{'...' if len(horoscope.content) > 500 else ''}
                    </div>
                </td>
            </tr>
            """
            predictions_text += f"\n\n{type_name}\n{'='*40}\n{horoscope.content[:500]}{'...' if len(horoscope.content) > 500 else ''}"
    
    html_content = build_welcome_predictions_html(
        user_name=user_name,
        predictions_html=predictions_html,
        dashboard_link=dashboard_link,
        translations=translations
    )
    
    text_content = build_welcome_predictions_text(
        user_name=user_name,
        predictions_text=predictions_text,
        dashboard_link=dashboard_link,
        translations=translations
    )
    
    try:
        import requests
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {email_service.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": email_service.from_email,
                "to": [user.email],
                "subject": translations['subject'],
                "html": html_content,
                "text": text_content
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Welcome predictions email sent to {user.email}")
            return True
        else:
            print(f"❌ Failed to send welcome email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending welcome predictions email: {e}")
        return False


# =============================================================================
# EMAIL TEMPLATES AND TRANSLATIONS
# =============================================================================

def get_prediction_emoji(prediction_type: str) -> str:
    """Get emoji for prediction type."""
    emojis = {
        "daily": "☀️",
        "weekly": "📅",
        "monthly": "🌙"
    }
    return emojis.get(prediction_type, "✨")


PREDICTION_EMAIL_TRANSLATIONS = {
    'fi': {
        'daily': {
            'subject': '☀️ Päivän ennustuksesi - Nous Paradeigma',
            'title': 'Päivän ennustus',
            'greeting': 'Hyvää huomenta',
            'intro': 'Tässä on päivittäinen kosminen ohjauksesi.',
            'button': 'Lue lisää hallintapaneelissa',
            'footer': '© 2024 Nous Paradeigma. Kaikki oikeudet pidätetään.'
        },
        'weekly': {
            'subject': '📅 Viikon ennustuksesi - Nous Paradeigma',
            'title': 'Viikon ennustus',
            'greeting': 'Hyvää sunnuntaita',
            'intro': 'Tässä on viikottainen kosminen ohjauksesi tulevalle viikolle.',
            'button': 'Lue lisää hallintapaneelissa',
            'footer': '© 2024 Nous Paradeigma. Kaikki oikeudet pidätetään.'
        },
        'monthly': {
            'subject': '🌙 Kuukauden ennustuksesi - Nous Paradeigma',
            'title': 'Kuukauden ennustus',
            'greeting': 'Hei',
            'intro': 'Tässä on kuukausittainen sieluennustuksesi.',
            'button': 'Lue lisää hallintapaneelissa',
            'footer': '© 2024 Nous Paradeigma. Kaikki oikeudet pidätetään.'
        }
    },
    'en': {
        'daily': {
            'subject': '☀️ Your Daily Prediction - Nous Paradeigma',
            'title': 'Daily Prediction',
            'greeting': 'Good morning',
            'intro': 'Here is your daily cosmic guidance.',
            'button': 'Read more in your dashboard',
            'footer': '© 2024 Nous Paradeigma. All rights reserved.'
        },
        'weekly': {
            'subject': '📅 Your Weekly Prediction - Nous Paradeigma',
            'title': 'Weekly Prediction',
            'greeting': 'Happy Sunday',
            'intro': 'Here is your weekly cosmic guidance for the coming week.',
            'button': 'Read more in your dashboard',
            'footer': '© 2024 Nous Paradeigma. All rights reserved.'
        },
        'monthly': {
            'subject': '🌙 Your Monthly Prediction - Nous Paradeigma',
            'title': 'Monthly Prediction',
            'greeting': 'Hello',
            'intro': 'Here is your monthly soul prediction.',
            'button': 'Read more in your dashboard',
            'footer': '© 2024 Nous Paradeigma. All rights reserved.'
        }
    },
    'sv': {
        'daily': {
            'subject': '☀️ Din dagliga förutsägelse - Nous Paradeigma',
            'title': 'Daglig förutsägelse',
            'greeting': 'God morgon',
            'intro': 'Här är din dagliga kosmiska vägledning.',
            'button': 'Läs mer i din instrumentpanel',
            'footer': '© 2024 Nous Paradeigma. Alla rättigheter förbehållna.'
        },
        'weekly': {
            'subject': '📅 Din veckans förutsägelse - Nous Paradeigma',
            'title': 'Veckans förutsägelse',
            'greeting': 'Glad söndag',
            'intro': 'Här är din kosmiska vägledning för den kommande veckan.',
            'button': 'Läs mer i din instrumentpanel',
            'footer': '© 2024 Nous Paradeigma. Alla rättigheter förbehållna.'
        },
        'monthly': {
            'subject': '🌙 Din månads förutsägelse - Nous Paradeigma',
            'title': 'Månads förutsägelse',
            'greeting': 'Hej',
            'intro': 'Här är din månatliga själsförutsägelse.',
            'button': 'Läs mer i din instrumentpanel',
            'footer': '© 2024 Nous Paradeigma. Alla rättigheter förbehållna.'
        }
    }
}

WELCOME_PREDICTIONS_TRANSLATIONS = {
    'fi': {
        'subject': '🎉 Tervetuloa - Ensimmäiset ennustuksesi ovat valmiit!',
        'greeting': 'Tervetuloa kosmiseen matkaasi',
        'message': 'Tilauksesi on vahvistettu ja ensimmäiset ennustuksesi ovat valmiit!',
        'intro': 'Olemme luoneet sinulle henkilökohtaiset päivä-, viikko- ja kuukausikohtaiset ennustukset. Tässä on esimakua siitä, mitä sinua odottaa:',
        'button': '🔮 Lue kaikki ennustuksesi',
        'schedule_title': 'Ennustusaikataulusi',
        'schedule_daily': '☀️ Päivittäinen ennustus: joka päivä klo 7:00',
        'schedule_weekly': '📅 Viikottainen ennustus: joka sunnuntai',
        'schedule_monthly': '🌙 Kuukausittainen ennustus: joka kuun 30. päivä',
        'daily_title': 'Päivän ennustus',
        'weekly_title': 'Viikon ennustus',
        'monthly_title': 'Kuukauden ennustus',
        'footer': '© 2024 Nous Paradeigma. Kaikki oikeudet pidätetään.'
    },
    'en': {
        'subject': '🎉 Welcome - Your First Predictions Are Ready!',
        'greeting': 'Welcome to your cosmic journey',
        'message': 'Your subscription is confirmed and your first predictions are ready!',
        'intro': 'We have created personalized daily, weekly, and monthly predictions for you. Here is a preview of what awaits you:',
        'button': '🔮 Read all your predictions',
        'schedule_title': 'Your Prediction Schedule',
        'schedule_daily': '☀️ Daily prediction: every day at 7:00 AM',
        'schedule_weekly': '📅 Weekly prediction: every Sunday',
        'schedule_monthly': '🌙 Monthly prediction: every 30th of the month',
        'daily_title': 'Daily Prediction',
        'weekly_title': 'Weekly Prediction',
        'monthly_title': 'Monthly Prediction',
        'footer': '© 2024 Nous Paradeigma. All rights reserved.'
    },
    'sv': {
        'subject': '🎉 Välkommen - Dina första förutsägelser är klara!',
        'greeting': 'Välkommen till din kosmiska resa',
        'message': 'Din prenumeration är bekräftad och dina första förutsägelser är klara!',
        'intro': 'Vi har skapat personliga dagliga, veckovisa och månatliga förutsägelser för dig. Här är en förhandstitt på vad som väntar dig:',
        'button': '🔮 Läs alla dina förutsägelser',
        'schedule_title': 'Ditt förutsägelseschema',
        'schedule_daily': '☀️ Daglig förutsägelse: varje dag kl 7:00',
        'schedule_weekly': '📅 Veckovis förutsägelse: varje söndag',
        'schedule_monthly': '🌙 Månadsvis förutsägelse: varje 30:e i månaden',
        'daily_title': 'Daglig förutsägelse',
        'weekly_title': 'Veckans förutsägelse',
        'monthly_title': 'Månads förutsägelse',
        'footer': '© 2024 Nous Paradeigma. Alla rättigheter förbehållna.'
    }
}


def get_prediction_email_translations(prediction_type: str, lang: str) -> dict:
    """Get translations for prediction emails."""
    lang_translations = PREDICTION_EMAIL_TRANSLATIONS.get(lang, PREDICTION_EMAIL_TRANSLATIONS['fi'])
    return lang_translations.get(prediction_type, lang_translations['daily'])


def get_welcome_predictions_translations(lang: str) -> dict:
    """Get translations for welcome predictions email."""
    return WELCOME_PREDICTIONS_TRANSLATIONS.get(lang, WELCOME_PREDICTIONS_TRANSLATIONS['fi'])


# =============================================================================
# HTML/TEXT EMAIL BUILDERS
# =============================================================================

def build_prediction_email_html(
    user_name: str,
    prediction_type: str,
    content: str,
    zodiac_sign: str,
    dashboard_link: str,
    translations: dict
) -> str:
    """Build HTML content for prediction email."""
    greeting = f"{translations['greeting']} {user_name}," if user_name else f"{translations['greeting']},"
    emoji = get_prediction_emoji(prediction_type)
    
    # Truncate content for email (show preview, full content in dashboard)
    preview_content = content[:800] + "..." if len(content) > 800 else content
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0a0f;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0f; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0f 100%); border-radius: 16px; border: 1px solid rgba(138, 116, 249, 0.3);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <h1 style="color: #d4af37; font-size: 28px; margin: 0;">✨ Nous Paradeigma</h1>
                        </td>
                    </tr>
                    
                    <!-- Title -->
                    <tr>
                        <td align="center" style="padding: 10px 40px;">
                            <div style="font-size: 40px; margin-bottom: 10px;">{emoji}</div>
                            <h2 style="color: #ffffff; font-size: 22px; margin: 0;">{translations['title']}</h2>
                            <p style="color: #8a74f9; font-size: 14px; margin: 5px 0 0;">{zodiac_sign.capitalize()}</p>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #ffffff; font-size: 18px; margin-bottom: 10px;">{greeting}</p>
                            <p style="color: #b8b8c8; font-size: 14px; line-height: 1.6;">
                                {translations['intro']}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Prediction Content -->
                    <tr>
                        <td style="padding: 0 40px 20px;">
                            <div style="background: rgba(138, 116, 249, 0.1); border-radius: 12px; padding: 20px; border-left: 4px solid #d4af37;">
                                <div style="color: #e8e8f0; font-size: 15px; line-height: 1.7; white-space: pre-wrap;">{preview_content}</div>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Button -->
                    <tr>
                        <td align="center" style="padding: 20px 40px 30px;">
                            <a href="{dashboard_link}" style="display: inline-block; background: linear-gradient(135deg, #8a74f9 0%, #6b5ce7 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                                {translations['button']}
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; border-top: 1px solid rgba(138, 116, 249, 0.2);">
                            <p style="color: #6b6b7b; font-size: 12px; text-align: center; margin: 0;">
                                {translations['footer']}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def build_prediction_email_text(
    user_name: str,
    prediction_type: str,
    content: str,
    zodiac_sign: str,
    dashboard_link: str,
    translations: dict
) -> str:
    """Build plain text content for prediction email."""
    greeting = f"{translations['greeting']} {user_name}," if user_name else f"{translations['greeting']},"
    preview_content = content[:800] + "..." if len(content) > 800 else content
    
    return f"""
{translations['title']} - {zodiac_sign.capitalize()}

{greeting}

{translations['intro']}

{'='*50}

{preview_content}

{'='*50}

{translations['button']}: {dashboard_link}

{translations['footer']}
"""


def build_welcome_predictions_html(
    user_name: str,
    predictions_html: str,
    dashboard_link: str,
    translations: dict
) -> str:
    """Build HTML content for welcome predictions email."""
    greeting = f"{translations['greeting']}, {user_name}!" if user_name else f"{translations['greeting']}!"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0a0f;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0f; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0f 100%); border-radius: 16px; border: 1px solid rgba(138, 116, 249, 0.3);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <h1 style="color: #d4af37; font-size: 28px; margin: 0;">✨ Nous Paradeigma</h1>
                        </td>
                    </tr>
                    
                    <!-- Welcome -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
                            <h2 style="color: #ffffff; font-size: 24px; margin: 0 0 10px;">{greeting}</h2>
                            <p style="color: #d4af37; font-size: 16px; margin: 0;">{translations['message']}</p>
                        </td>
                    </tr>
                    
                    <!-- Intro -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #b8b8c8; font-size: 15px; line-height: 1.6; text-align: center;">
                                {translations['intro']}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Predictions -->
                    {predictions_html}
                    
                    <!-- Button -->
                    <tr>
                        <td align="center" style="padding: 30px 40px;">
                            <a href="{dashboard_link}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #b8962e 100%); color: #0a0a0f; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                                {translations['button']}
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Schedule Info -->
                    <tr>
                        <td style="padding: 20px 40px; border-top: 1px solid rgba(138, 116, 249, 0.2);">
                            <h4 style="color: #ffffff; font-size: 16px; margin: 0 0 15px;">{translations['schedule_title']}</h4>
                            <p style="color: #b8b8c8; font-size: 14px; margin: 5px 0;">{translations['schedule_daily']}</p>
                            <p style="color: #b8b8c8; font-size: 14px; margin: 5px 0;">{translations['schedule_weekly']}</p>
                            <p style="color: #b8b8c8; font-size: 14px; margin: 5px 0;">{translations['schedule_monthly']}</p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; border-top: 1px solid rgba(138, 116, 249, 0.2);">
                            <p style="color: #6b6b7b; font-size: 12px; text-align: center; margin: 0;">
                                {translations['footer']}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def build_welcome_predictions_text(
    user_name: str,
    predictions_text: str,
    dashboard_link: str,
    translations: dict
) -> str:
    """Build plain text content for welcome predictions email."""
    greeting = f"{translations['greeting']}, {user_name}!" if user_name else f"{translations['greeting']}!"
    
    return f"""
{greeting}

{translations['message']}

{translations['intro']}

{'='*60}
{predictions_text}
{'='*60}

{translations['button']}: {dashboard_link}

{translations['schedule_title']}
{translations['schedule_daily']}
{translations['schedule_weekly']}
{translations['schedule_monthly']}

{translations['footer']}
"""


# =============================================================================
# SCHEDULER SETUP
# =============================================================================

class PredictionScheduler:
    """
    Manages scheduled prediction generation jobs.
    
    Schedule:
    - Daily: Every day at 7:00 AM local time
    - Weekly: Every Sunday at 7:00 AM
    - Monthly: Every 30th of the month at 7:00 AM
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._started = False
    
    def start(self):
        """Start the prediction scheduler."""
        if self._started:
            print("⚠️ Scheduler already running")
            return
        
        # Get timezone from environment or default to Europe/Helsinki (Finland)
        timezone = os.getenv("PREDICTION_TIMEZONE", "Europe/Helsinki")
        
        # Daily predictions - every day at 7:00 AM
        self.scheduler.add_job(
            run_daily_predictions,
            CronTrigger(hour=7, minute=0, timezone=timezone),
            id="daily_predictions",
            name="Generate daily predictions",
            replace_existing=True
        )
        
        # Weekly predictions - every Sunday at 7:00 AM
        self.scheduler.add_job(
            run_weekly_predictions,
            CronTrigger(day_of_week="sun", hour=7, minute=0, timezone=timezone),
            id="weekly_predictions",
            name="Generate weekly predictions",
            replace_existing=True
        )
        
        # Monthly predictions - every 30th at 7:00 AM
        self.scheduler.add_job(
            run_monthly_predictions,
            CronTrigger(day=30, hour=7, minute=0, timezone=timezone),
            id="monthly_predictions",
            name="Generate monthly predictions",
            replace_existing=True
        )
        
        self.scheduler.start()
        self._started = True
        
        print(f"🚀 Prediction scheduler started (timezone: {timezone})")
        print("   📅 Daily predictions: Every day at 7:00 AM")
        print("   📅 Weekly predictions: Every Sunday at 7:00 AM")
        print("   📅 Monthly predictions: Every 30th at 7:00 AM")
    
    def stop(self):
        """Stop the scheduler."""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            print("🛑 Prediction scheduler stopped")
    
    def get_jobs(self) -> list:
        """Get list of scheduled jobs."""
        if not self._started:
            return []
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]


# Singleton instance
prediction_scheduler = PredictionScheduler()

