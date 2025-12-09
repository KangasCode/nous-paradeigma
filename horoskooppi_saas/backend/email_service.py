"""
Email service using Resend API for magic link authentication.
Supports multiple languages (Finnish, English, Swedish).
"""
import os
import requests
from typing import Optional

# =============================================================================
# EMAIL TRANSLATIONS
# =============================================================================
EMAIL_TRANSLATIONS = {
    'fi': {
        'magic_link_subject': '🔮 Kirjautumislinkki - Nous Paradeigma',
        'magic_link_greeting': 'Hei',
        'magic_link_intro': 'Klikkaa alla olevaa painiketta kirjautuaksesi turvallisesti kosmiseen hallintapaneeliisi. Tämä linkki vanhenee 10 minuutissa.',
        'magic_link_button': '🔮 Kirjaudu sisään',
        'magic_link_security': 'Jos et pyytänyt tätä kirjautumislinkkiä, voit turvallisesti jättää tämän sähköpostin huomiotta. Joku on saattanut syöttää sähköpostiosoitteesi vahingossa.',
        'welcome_subject': '🎉 Tervetuloa Nous Paradeigmaan - Kosminen matkasi alkaa',
        'welcome_greeting': 'Tervetuloa',
        'welcome_message': 'Kosminen matkasi alkaa nyt.',
        'welcome_intro': 'Kiitos liittymisestäsi Nous Paradeigmaan! Klikkaa alla päästäksesi henkilökohtaiseen kosmiseen hallintapaneeliisi ja vastaanottaaksesi ensimmäiset ennustuksesi.',
        'welcome_button': '🔮 Siirry hallintapaneeliin',
        'welcome_features': ['✨ Henkilökohtaiset päiväviestit', '🌙 Viikottainen polun ohjaus', '💫 Kuukausittaiset sielunennustukset'],
        'welcome_note': 'Tämä kirjautumislinkki vanhenee 10 minuutissa. Voit aina pyytää uuden kirjautumissivultamme.',
        'footer': '© 2024 Nous Paradeigma. Kaikki oikeudet pidätetään.'
    },
    'en': {
        'magic_link_subject': '🔮 Your Magic Login Link - Nous Paradeigma',
        'magic_link_greeting': 'Hello',
        'magic_link_intro': 'Click the button below to securely log in to your cosmic dashboard. This link will expire in 10 minutes.',
        'magic_link_button': '🔮 Enter Your Space',
        'magic_link_security': "If you didn't request this login link, you can safely ignore this email. Someone may have entered your email by mistake.",
        'welcome_subject': '🎉 Welcome to Nous Paradeigma - Access Your Cosmic Dashboard',
        'welcome_greeting': 'Welcome',
        'welcome_message': 'Your cosmic journey begins now.',
        'welcome_intro': 'Thank you for joining Nous Paradeigma! Click below to access your personalized cosmic dashboard and receive your first predictions.',
        'welcome_button': '🔮 Enter Your Space',
        'welcome_features': ['✨ Personal Daily Messages', '🌙 Weekly Path Guidance', '💫 Monthly Soul Predictions'],
        'welcome_note': 'This login link will expire in 10 minutes. You can always request a new one from our login page.',
        'footer': '© 2024 Nous Paradeigma. All rights reserved.'
    },
    'sv': {
        'magic_link_subject': '🔮 Din magiska inloggningslänk - Nous Paradeigma',
        'magic_link_greeting': 'Hej',
        'magic_link_intro': 'Klicka på knappen nedan för att logga in säkert på din kosmiska instrumentpanel. Länken går ut om 10 minuter.',
        'magic_link_button': '🔮 Logga in',
        'magic_link_security': 'Om du inte begärde denna länk kan du ignorera detta mail.',
        'welcome_subject': '🎉 Välkommen till Nous Paradeigma',
        'welcome_greeting': 'Välkommen',
        'welcome_message': 'Din kosmiska resa börjar nu.',
        'welcome_intro': 'Tack för att du gick med! Klicka nedan för att komma åt din personliga instrumentpanel.',
        'welcome_button': '🔮 Logga in',
        'welcome_features': ['✨ Personliga dagliga meddelanden', '🌙 Veckans vägledning', '💫 Månadens förutsägelser'],
        'welcome_note': 'Denna länk går ut om 10 minuter.',
        'footer': '© 2024 Nous Paradeigma. Alla rättigheter förbehållna.'
    }
}

def get_email_text(key: str, lang: str = 'fi') -> str:
    """Get translated email text."""
    return EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS['fi']).get(key, EMAIL_TRANSLATIONS['fi'].get(key, key))


class EmailService:
    """
    Service for sending emails via Resend API.
    Used for magic link authentication.
    Supports multiple languages.
    """
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.site_url = os.getenv("SITE_URL", "http://localhost:8000")
        self.from_email = os.getenv("FROM_EMAIL", "Nous Paradeigma <noreply@nousparadeigma.com>")
        self.api_url = "https://api.resend.com/emails"
    
    def is_configured(self) -> bool:
        """Check if Resend API is properly configured."""
        return bool(self.api_key and self.api_key != "your-resend-api-key")
    
    def send_magic_link(self, to_email: str, token: str, user_name: Optional[str] = None, lang: str = 'fi') -> bool:
        """
        Send a magic link login email to the user.
        
        Args:
            to_email: Recipient email address
            token: Magic link token
            user_name: Optional user name for personalization
            lang: Language code (fi, en, sv)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            print(f"⚠️ Resend not configured. Magic link would be: {self.site_url}/magic-login?token={token}")
            return False
        
        magic_link = f"{self.site_url}/magic-login?token={token}"
        greeting_text = get_email_text('magic_link_greeting', lang)
        greeting = f"{greeting_text} {user_name}," if user_name else f"{greeting_text},"
        
        intro_text = get_email_text('magic_link_intro', lang)
        button_text = get_email_text('magic_link_button', lang)
        security_text = get_email_text('magic_link_security', lang)
        footer_text = get_email_text('footer', lang)
        
        html_content = f"""
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
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #ffffff; font-size: 18px; margin-bottom: 10px;">{greeting}</p>
                            <p style="color: #b8b8c8; font-size: 16px; line-height: 1.6;">
                                {intro_text}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Button -->
                    <tr>
                        <td align="center" style="padding: 20px 40px 30px;">
                            <a href="{magic_link}" style="display: inline-block; background: linear-gradient(135deg, #8a74f9 0%, #6b5ce7 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                                {button_text}
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Security Note -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <p style="color: #6b6b7b; font-size: 14px; line-height: 1.5;">
                                {security_text}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; border-top: 1px solid rgba(138, 116, 249, 0.2);">
                            <p style="color: #6b6b7b; font-size: 12px; text-align: center; margin: 0;">
                                {footer_text}
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
        
        text_content = f"""
{greeting}

{intro_text}

{magic_link}

{security_text}

{footer_text}
"""
        
        subject = get_email_text('magic_link_subject', lang)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": self.from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                    "text": text_content
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Magic link email sent to {to_email} (lang: {lang})")
                return True
            else:
                print(f"❌ Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, token: str, user_name: Optional[str] = None, lang: str = 'fi') -> bool:
        """
        Send a welcome email with magic link after successful checkout.
        
        Args:
            to_email: Recipient email address
            token: Magic link token
            user_name: Optional user name for personalization
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            print(f"⚠️ Resend not configured. Welcome magic link would be: {self.site_url}/magic-login?token={token}")
            return False
        
        magic_link = f"{self.site_url}/magic-login?token={token}"
        
        # Get translated texts
        greeting_word = get_email_text('welcome_greeting', lang)
        greeting = f"{greeting_word} {user_name}!" if user_name else f"{greeting_word}!"
        message = get_email_text('welcome_message', lang)
        intro = get_email_text('welcome_intro', lang)
        button_text = get_email_text('welcome_button', lang)
        features = get_email_text('welcome_features', lang)
        note = get_email_text('welcome_note', lang)
        footer = get_email_text('footer', lang)
        
        # Build features HTML
        features_html = ''.join([f'<tr><td style="color: #b8b8c8; font-size: 14px; padding: 8px 0;">{f}</td></tr>' for f in features])
        features_text = '\n'.join(features)
        
        html_content = f"""
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
                    
                    <!-- Welcome Message -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
                            <h2 style="color: #ffffff; font-size: 24px; margin: 0 0 10px;">{greeting}</h2>
                            <p style="color: #d4af37; font-size: 18px; margin: 0;">{message}</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #b8b8c8; font-size: 16px; line-height: 1.6; text-align: center;">
                                {intro}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Button -->
                    <tr>
                        <td align="center" style="padding: 20px 40px 30px;">
                            <a href="{magic_link}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #b8962e 100%); color: #0a0a0f; text-decoration: none; padding: 16px 40px; border-radius: 12px; font-size: 16px; font-weight: 600;">
                                {button_text}
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Features -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {features_html}
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Note -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <p style="color: #6b6b7b; font-size: 13px; line-height: 1.5;">
                                {note}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; border-top: 1px solid rgba(138, 116, 249, 0.2);">
                            <p style="color: #6b6b7b; font-size: 12px; text-align: center; margin: 0;">
                                {footer}
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
        
        text_content = f"""
{greeting}

{message}

{intro}

{magic_link}

{features_text}

{note}

{footer}
"""
        
        subject = get_email_text('welcome_subject', lang)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": self.from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                    "text": text_content
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Welcome email sent to {to_email} (lang: {lang})")
                return True
            else:
                print(f"❌ Failed to send welcome email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending welcome email: {e}")
            return False


# =============================================================================
# RESEND AUDIENCE SEGMENTATION
# Sync users to different Resend audiences based on their state
# =============================================================================

# Audience IDs from environment variables
AUDIENCE_CHECKOUT_VISITED = os.getenv("RESEND_AUDIENCE_ID_CHECKOUT_VISITED")
AUDIENCE_ACTIVE_SUBSCRIBERS = os.getenv("RESEND_AUDIENCE_ID_ACTIVE_SUBSCRIBERS")
AUDIENCE_CANCELED_SUBSCRIBERS = os.getenv("RESEND_AUDIENCE_ID_CANCELED_SUBSCRIBERS")


def sync_user_to_resend(email: str, audience_id: str, first_name: Optional[str] = None) -> bool:
    """
    Upsert a user (email + name) into a Resend audience.
    
    Args:
        email: User's email address
        audience_id: Resend audience ID to add user to
        first_name: Optional first name for personalization
    
    Returns:
        True if sync successful, False otherwise
    
    Note: Fails silently - never breaks checkout or Stripe flow
    """
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key or not audience_id:
        print(f"⚠️ Resend audience sync skipped - missing API key or audience ID")
        return False
    
    try:
        # Resend Contacts API endpoint
        url = f"https://api.resend.com/audiences/{audience_id}/contacts"
        
        payload = {
            "email": email.lower(),
            "unsubscribed": False
        }
        
        if first_name:
            payload["first_name"] = first_name
        
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Synced {email} to Resend audience {audience_id[:8]}...")
            return True
        else:
            print(f"⚠️ Resend sync failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️ Resend sync error (silent): {e}")
        return False


def remove_user_from_resend(email: str, audience_id: str) -> bool:
    """
    Remove a user from a Resend audience.
    
    Args:
        email: User's email address
        audience_id: Resend audience ID to remove user from
    
    Returns:
        True if removal successful, False otherwise
    
    Note: Fails silently - never breaks checkout or Stripe flow
    """
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key or not audience_id:
        print(f"⚠️ Resend audience removal skipped - missing API key or audience ID")
        return False
    
    try:
        # First, get the contact ID by email
        # Resend requires contact ID to delete, so we need to find it first
        list_url = f"https://api.resend.com/audiences/{audience_id}/contacts"
        
        list_response = requests.get(
            list_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if list_response.status_code != 200:
            print(f"⚠️ Failed to list contacts for removal: {list_response.status_code}")
            return False
        
        contacts = list_response.json().get("data", [])
        contact_id = None
        
        for contact in contacts:
            if contact.get("email", "").lower() == email.lower():
                contact_id = contact.get("id")
                break
        
        if not contact_id:
            # Contact not found - that's fine, nothing to remove
            print(f"ℹ️ Contact {email} not found in audience {audience_id[:8]}... (nothing to remove)")
            return True
        
        # Delete the contact
        delete_url = f"https://api.resend.com/audiences/{audience_id}/contacts/{contact_id}"
        
        delete_response = requests.delete(
            delete_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if delete_response.status_code in [200, 204]:
            print(f"✅ Removed {email} from Resend audience {audience_id[:8]}...")
            return True
        else:
            print(f"⚠️ Resend removal failed: {delete_response.status_code} - {delete_response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️ Resend removal error (silent): {e}")
        return False


def sync_checkout_visited(email: str, first_name: Optional[str] = None):
    """
    Sync user to CHECKOUT_VISITED segment.
    Called when user enters email in checkout but hasn't completed purchase.
    """
    if AUDIENCE_CHECKOUT_VISITED:
        sync_user_to_resend(email, AUDIENCE_CHECKOUT_VISITED, first_name)


def sync_active_subscriber(email: str, first_name: Optional[str] = None):
    """
    Sync user to ACTIVE_SUBSCRIBERS segment.
    Also removes from CHECKOUT_VISITED (they converted) and CANCELED (they resubscribed).
    """
    if AUDIENCE_ACTIVE_SUBSCRIBERS:
        sync_user_to_resend(email, AUDIENCE_ACTIVE_SUBSCRIBERS, first_name)
    
    # Remove from checkout visited - they converted
    if AUDIENCE_CHECKOUT_VISITED:
        remove_user_from_resend(email, AUDIENCE_CHECKOUT_VISITED)
    
    # Remove from canceled - they're active again
    if AUDIENCE_CANCELED_SUBSCRIBERS:
        remove_user_from_resend(email, AUDIENCE_CANCELED_SUBSCRIBERS)


def sync_canceled_subscriber(email: str, first_name: Optional[str] = None):
    """
    Sync user to CANCELED_SUBSCRIBERS segment.
    Also removes from ACTIVE_SUBSCRIBERS (mutually exclusive).
    """
    if AUDIENCE_CANCELED_SUBSCRIBERS:
        sync_user_to_resend(email, AUDIENCE_CANCELED_SUBSCRIBERS, first_name)
    
    # Remove from active - they're no longer active
    if AUDIENCE_ACTIVE_SUBSCRIBERS:
        remove_user_from_resend(email, AUDIENCE_ACTIVE_SUBSCRIBERS)


# Singleton instance
email_service = EmailService()

