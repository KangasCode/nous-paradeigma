"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use a relative path for local development to avoid permission issues with /data/
# When running locally, this will create horoskooppi.db in the backend directory
# In production (e.g. Render), env var DATABASE_URL should be set correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "horoskooppi.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Create engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables
    """
    # Import all models to ensure they're registered
    import models
    # import checkout_models # Might cause circular import if not careful, but generally ok here
    Base.metadata.create_all(bind=engine)
    
    # Run migrations to add any missing columns
    migrate_database()

def migrate_database():
    """
    Add missing columns to existing tables (SQLite doesn't support ALTER TABLE ADD COLUMN well,
    so we check and add manually)
    """
    from sqlalchemy import text, inspect
    
    inspector = inspect(engine)
    
    # Check if users table exists
    if 'users' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        with engine.connect() as conn:
            # Add birth_date if missing
            if 'birth_date' not in columns:
                print("Adding birth_date column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN birth_date VARCHAR"))
                conn.commit()
            
            # Add birth_time if missing
            if 'birth_time' not in columns:
                print("Adding birth_time column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN birth_time VARCHAR"))
                conn.commit()
            
            # Add birth_city if missing
            if 'birth_city' not in columns:
                print("Adding birth_city column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN birth_city VARCHAR"))
                conn.commit()
            
            # Add profile fields
            if 'first_name' not in columns:
                print("Adding first_name column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR"))
                conn.commit()
            
            if 'last_name' not in columns:
                print("Adding last_name column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR"))
                conn.commit()
            
            if 'phone' not in columns:
                print("Adding phone column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR"))
                conn.commit()
            
            if 'address' not in columns:
                print("Adding address column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN address VARCHAR"))
                conn.commit()
            
            # Add zodiac_sign (auto-calculated from birth_date, NEVER editable by user)
            if 'zodiac_sign' not in columns:
                print("Adding zodiac_sign column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN zodiac_sign VARCHAR"))
                conn.commit()
                # Update existing users with calculated zodiac signs
                update_existing_users_zodiac_signs()
    
    # Check if horoscopes table exists
    if 'horoscopes' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('horoscopes')]
        
        with engine.connect() as conn:
            # Add raw_data if missing
            if 'raw_data' not in columns:
                print("Adding raw_data column to horoscopes table...")
                conn.execute(text("ALTER TABLE horoscopes ADD COLUMN raw_data TEXT"))
                conn.commit()
    
    # Check if checkout_progress table exists (for birth date fields)
    if 'checkout_progress' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('checkout_progress')]
        
        with engine.connect() as conn:
            if 'birth_date' not in columns:
                print("Adding birth_date column to checkout_progress table...")
                conn.execute(text("ALTER TABLE checkout_progress ADD COLUMN birth_date VARCHAR"))
                conn.commit()
            
            if 'birth_time' not in columns:
                print("Adding birth_time column to checkout_progress table...")
                conn.execute(text("ALTER TABLE checkout_progress ADD COLUMN birth_time VARCHAR"))
                conn.commit()
            
            if 'birth_city' not in columns:
                print("Adding birth_city column to checkout_progress table...")
                conn.execute(text("ALTER TABLE checkout_progress ADD COLUMN birth_city VARCHAR"))
                conn.commit()
            
            if 'zodiac_sign' not in columns:
                print("Adding zodiac_sign column to checkout_progress table...")
                conn.execute(text("ALTER TABLE checkout_progress ADD COLUMN zodiac_sign VARCHAR"))
                conn.commit()
            
            if 'step_birthdate_completed' not in columns:
                print("Adding step_birthdate_completed column to checkout_progress table...")
                conn.execute(text("ALTER TABLE checkout_progress ADD COLUMN step_birthdate_completed BOOLEAN DEFAULT 0"))
                conn.commit()
            
            if 'birthdate_completed_at' not in columns:
                print("Adding birthdate_completed_at column to checkout_progress table...")
                conn.execute(text("ALTER TABLE checkout_progress ADD COLUMN birthdate_completed_at DATETIME"))
                conn.commit()
    
    print("Database migration completed.")

def update_existing_users_zodiac_signs():
    """
    Update zodiac signs for existing users who have birth_date but no zodiac_sign.
    This ensures all users have their zodiac sign calculated from their birth data.
    """
    from zodiac_utils import calculate_zodiac_sign
    from models import User
    
    db = SessionLocal()
    try:
        users_without_zodiac = db.query(User).filter(
            User.birth_date.isnot(None),
            User.zodiac_sign.is_(None)
        ).all()
        
        for user in users_without_zodiac:
            zodiac = calculate_zodiac_sign(user.birth_date)
            if zodiac:
                user.zodiac_sign = zodiac
                print(f"Updated zodiac sign for user {user.email}: {zodiac}")
        
        db.commit()
        print(f"Updated {len(users_without_zodiac)} users with zodiac signs")
    except Exception as e:
        print(f"Error updating zodiac signs: {e}")
        db.rollback()
    finally:
        db.close()

def init_test_data_if_needed():
    """
    Initialize test user if it doesn't exist (for both local and production)
    Creates if CREATE_TEST_USER or DEMO_MODE env var is set to 'true'
    """
    create_test_user = os.getenv("CREATE_TEST_USER", "false").lower() == "true"
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    print(f"🔍 Checking test user: CREATE_TEST_USER={create_test_user}, DEMO_MODE={demo_mode}")
    
    if not create_test_user and not demo_mode:
        print("⏭️ Skipping test user creation (CREATE_TEST_USER and DEMO_MODE are false)")
        return
    
    print(f"🚀 Test user creation triggered!")
    
    from models import User, Horoscope, Subscription
    from auth import get_password_hash
    from zodiac_utils import calculate_zodiac_sign
    from datetime import datetime, timedelta
    import json
    
    db = SessionLocal()
    try:
        email = "test@nousparadeigma.com"
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"✅ Test user {email} already exists")
            return
        
        print(f"🔧 Creating test user: {email}")
        hashed_password = get_password_hash("cosmos123")
        
        # Calculate zodiac sign from birth date (02.10.1992 = Libra)
        birth_date = "1992-10-02"
        zodiac_sign = calculate_zodiac_sign(birth_date)
        print(f"📊 Calculated zodiac sign: {zodiac_sign}")
        
        user = User(
            email=email,
            full_name="Test Cosmic Traveler",
            first_name="Test",
            last_name="Traveler",
            hashed_password=hashed_password,
            is_active=True,
            is_subscriber=True,
            birth_date=birth_date,
            birth_time="08:08",
            birth_city="Helsinki",
            zodiac_sign=zodiac_sign  # Auto-calculated from birth_date
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create subscription
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
        
        # Create example horoscope
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
        
        content = """**Daily Insight for Libra**

Your Sun in Libra at 9° seeks harmony today, but with the Moon in adventurous Sagittarius, your soul yearns for expansion and truth. The cosmic balance is shifting.

**Mental Clarity & Focus:**
Mercury in Scorpio deepens your perception. You are seeing beneath the surface. Trust your intuition, especially in conversations that feel heavy or loaded.

**Relationships:**
Venus in Scorpio suggests intensity. Shallow connections won't satisfy you right now. You might find yourself drawn to mysteries or secrets within your partnership.

**Practical Suggestion:**
Use your Mars in Cancer energy to nurture your home base before setting out on your next adventure. A clean space will clear your mind.

**Lucky Numbers:** 9, 14, 2"""
        
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
        
        print(f"✅ Test user {email} created successfully")
    except Exception as e:
        print(f"⚠️ Error creating test user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
