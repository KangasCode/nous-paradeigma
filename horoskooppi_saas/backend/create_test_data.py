import os
import sys
import json
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, SessionLocal
from models import User, Horoscope, Subscription
from auth import get_password_hash

def create_test_data():
    print("🚀 Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        # Create Test User
        email = "test@nousparadeigma.com"
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"⚠️ User {email} already exists. Deleting related data...")
            # Delete related horoscopes first
            from models import Horoscope, Subscription
            db.query(Horoscope).filter(Horoscope.user_id == existing_user.id).delete()
            db.query(Subscription).filter(Subscription.user_id == existing_user.id).delete()
            db.delete(existing_user)
            db.commit()

        print(f"✨ Creating test user: {email}")
        hashed_password = get_password_hash("cosmos123")
        user = User(
            email=email,
            full_name="Test Cosmic Traveler",
            hashed_password=hashed_password,
            is_active=True,
            is_subscriber=True,
            birth_date="1992-10-02",
            birth_time="08:08",
            birth_city="Helsinki"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create Active Subscription
        print("💎 Creating active subscription...")
        sub = Subscription(
            user_id=user.id,
            stripe_customer_id="cus_test123",
            stripe_subscription_id="sub_test123",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.add(sub)
        db.commit()

        # Create Example Horoscope with Raw Data
        print("🔮 Creating example horoscope for 02.10.1992...")
        
        # Calculated Raw Data for 1992-10-02 08:08 Helsinki
        # Sun: Libra (~9 deg)
        # Moon: Sagittarius (~14 deg)
        # Ascendant: Libra (approx)
        # Mercury: Scorpio
        # Venus: Scorpio
        # Mars: Cancer
        
        raw_data = {
            "date": "1992-10-02 08:08",
            "location": "Helsinki",
            "positions": {
                "Sun": {"sign": "Libra", "deg": 9.2},
                "Moon": {"sign": "Sagittarius", "deg": 14.5},
                "Mercury": {"sign": "Scorpio", "deg": 2.1},
                "Venus": {"sign": "Scorpio", "deg": 5.8},
                "Mars": {"sign": "Cancer", "deg": 18.3},
                "Jupiter": {"sign": "Libra", "deg": 28.4},
                "Saturn": {"sign": "Aquarius", "deg": 12.1},
                "Uranus": {"sign": "Capricorn", "deg": 14.7},
                "Neptune": {"sign": "Capricorn", "deg": 16.2},
                "Pluto": {"sign": "Scorpio", "deg": 21.9},
                "Ascendant": {"sign": "Libra", "deg": 15.4}
            }
        }

        content = """
**Daily Insight for Libra**

Your Sun in Libra at 9° seeks harmony today, but with the Moon in adventurous Sagittarius, your soul yearns for expansion and truth. The cosmic balance is shifting.

**Mental Clarity & Focus:**
Mercury in Scorpio deepens your perception. You are seeing beneath the surface. Trust your intuition, especially in conversations that feel heavy or loaded.

**Relationships:**
Venus in Scorpio suggests intensity. Shallow connections won't satisfy you right now. You might find yourself drawn to mysteries or secrets within your partnership.

**Practical Suggestion:**
Use your Mars in Cancer energy to nurture your home base before setting out on your next adventure. A clean space will clear your mind.

**Lucky Numbers:** 9, 14, 2
"""

        horoscope = Horoscope(
            user_id=user.id,
            zodiac_sign="libra",
            prediction_type="daily",
            content=content.strip(),
            raw_data=json.dumps(raw_data),
            prediction_date=datetime.utcnow()
        )
        db.add(horoscope)
        db.commit()

        print("\n✅ Test Data Created Successfully!")
        print("------------------------------------------------")
        print(f"User: {email}")
        print("Pass: cosmos123")
        print("Birth: 02.10.1992 08:08 Helsinki")
        print("Sign: Libra / Moon: Sagittarius")
        print("Subscription: Active")
        print("Example Horoscope: Created with raw planetary data")
        print("------------------------------------------------")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()

