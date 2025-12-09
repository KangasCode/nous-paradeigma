"""
Google Gemini API client for horoscope generation

IMPORTANT RULES FOR AI PREDICTION GENERATION:
1. User's core data (birth_date, birth_time, birth_city, zodiac_sign) comes from the database
2. The zodiac_sign is calculated ONCE from birth_date at registration and CANNOT be changed
3. All predictions MUST use the stored profile data, never user-edited temporary values
4. Every new prediction MUST be saved to the database and listed on /patterns page
5. Predictions are personalized based on: zodiac_sign, birth_date, birth_time, birth_city
"""
import os
import google.generativeai as genai
from typing import Optional, Tuple, Any, Dict
from datetime import datetime
import json


class GeminiClient:
    """Client for interacting with Google Gemini API for personalized horoscope generation"""
    
    def __init__(self):
        """Initialize Gemini client"""
        self.model = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Gemini client"""
        if self._initialized:
            return
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set. Using fallback horoscopes.")
            self._initialized = True
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self._initialized = True
        except Exception as e:
            print(f"WARNING: Failed to initialize Gemini: {e}. Using fallback horoscopes.")
            self._initialized = True
    
    def generate_horoscope(
        self, 
        zodiac_sign: str, 
        prediction_type: str = "daily",
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a horoscope prediction based on user's stored profile data.
        
        IMPORTANT: 
        - zodiac_sign comes from user's database record, calculated from birth_date
        - User CANNOT change their zodiac_sign - it is immutable
        - All birth data (birth_date, birth_time, birth_city) are immutable after registration
        
        Args:
            zodiac_sign: The user's zodiac sign from database (IMMUTABLE)
            prediction_type: Type of prediction ('daily', 'weekly', 'monthly')
            user_profile: User's stored profile data from database (birth_date, birth_time, birth_city, etc.)
        
        Returns:
            Tuple containing:
            - Generated horoscope text
            - Dictionary with raw calculation data used for generation
        """
        self._ensure_initialized()
        
        # Build raw data structure
        raw_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "prediction_type": prediction_type,
            "zodiac_sign": zodiac_sign,
            "user_profile": user_profile or {},
            "transits": {}
        }
        
        # 1. Fetch Astrology Data (transits)
        try:
            from astrology_service import astrology_service
            current_date = datetime.now().strftime("%Y-%m-%d")
            raw_data["transits"] = astrology_service.calculate_transits(current_date)
            raw_data["transits"]["date"] = current_date
            
            # Calculate natal chart if user has birth data
            if user_profile and user_profile.get("birth_date") and user_profile.get("birth_time"):
                natal_data = astrology_service.calculate_natal_chart(
                    user_profile["birth_date"],
                    user_profile["birth_time"],
                    user_profile.get("birth_city", "Unknown")
                )
                raw_data["natal_chart"] = natal_data
        except ImportError:
            print("Astrology service import failed")
            raw_data["transits"] = {"error": "Service unavailable"}
        except Exception as e:
            print(f"Astrology calculation failed: {e}")
            raw_data["transits"] = {"error": str(e)}

        # 2. Generate Content
        if not self.model:
            return self._generate_fallback_horoscope(zodiac_sign, prediction_type), raw_data
        
        prompt = self._create_prompt(zodiac_sign, prediction_type, raw_data, user_profile)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text, raw_data
        except Exception as e:
            print(f"Gemini API error: {e}. Using fallback.")
            return self._generate_fallback_horoscope(zodiac_sign, prediction_type), raw_data
    
    def _create_prompt(
        self, 
        zodiac_sign: str, 
        prediction_type: str, 
        raw_data: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a prompt for horoscope generation with strict rules about data sources"""
        
        # CRITICAL AI INSTRUCTIONS
        ai_instructions = """
=== CRITICAL INSTRUCTIONS FOR AI ===

DATA SOURCE RULES (MUST BE FOLLOWED):
1. The user's zodiac_sign is AUTOMATICALLY CALCULATED from their birth_date at registration
2. The zodiac_sign CANNOT be changed by the user under any circumstances
3. All predictions MUST be based on the STORED PROFILE DATA provided below
4. Never use temporary values or user-edited values for predictions
5. The following data is IMMUTABLE and comes from the database:
   - birth_date (date of birth)
   - birth_time (time of birth)
   - birth_city (place of birth)
   - zodiac_sign (calculated from birth_date, never editable)

PREDICTION GENERATION RULES:
1. Every prediction you generate will be SAVED to the database
2. All predictions appear on the user's /patterns page, newest first
3. Never repeat content from previous predictions
4. Use the natal chart data and current transits for accurate predictions
5. Predictions must be personalized based on the provided profile data
6. If birth data is missing, use general zodiac archetypes but note the limitation

=== END CRITICAL INSTRUCTIONS ===
"""

        # Base horoscope instructions
        base_prompt = """
You generate personal horoscope predictions for a subscribed user. All predictions must be based on real calculated astrology data including the natal chart, planetary positions, houses, aspects, and current transits. You must never repeat earlier predictions. Your writing style must be modern, personal, psychologically insightful, and based on astrological interpretation without making supernatural promises.

Every prediction is permanently saved in the user's archive and categorized as Daily, Weekly, or Monthly. The newest prediction always appears first.
"""

        # Type-specific instructions
        type_instructions = {
            "daily": """
DAILY PREDICTION REQUIREMENTS:
- Calculate current Moon sign and aspects
- Include effects on mental clarity, relationships, energy, motivation
- One practical suggestion for the day
- Length: 70-120 words
- Must be unique from all previous daily predictions
""",
            "weekly": """
WEEKLY PREDICTION REQUIREMENTS:
- Overview of the week's astrological atmosphere
- Three thematic areas: growth, relationships, challenges
- Key planetary movements affecting the week
- One practical weekly recommendation
- Length: 180-300 words
- Must be unique from all previous weekly predictions
""",
            "monthly": """
MONTHLY PREDICTION REQUIREMENTS:
- Main theme of the month based on planetary positions
- New Moon and Full Moon impacts
- Predictions for: career, relationships, finances, well-being
- Major planetary aspects and their effects
- Length: 400-700 words
- Must be unique from all previous monthly predictions
"""
        }

        # Build user profile context
        profile_context = ""
        if user_profile:
            profile_context = f"""
=== USER PROFILE DATA (FROM DATABASE - IMMUTABLE) ===
Zodiac Sign: {zodiac_sign.upper()} (calculated from birth date, cannot be changed)
Birth Date: {user_profile.get('birth_date', 'Not provided')}
Birth Time: {user_profile.get('birth_time', 'Not provided')}
Birth City: {user_profile.get('birth_city', 'Not provided')}
User Name: {user_profile.get('first_name', '')} {user_profile.get('last_name', '')}
=== END PROFILE DATA ===
"""
        else:
            profile_context = f"""
=== USER PROFILE DATA ===
Zodiac Sign: {zodiac_sign.upper()}
Birth Data: Not yet provided by user
NOTE: Generate prediction using zodiac archetypes until full birth data is available
=== END PROFILE DATA ===
"""

        # Build astrology data context
        astrology_context = f"""
=== CALCULATED ASTROLOGY DATA ===
Current Date: {raw_data.get('transits', {}).get('date', datetime.now().strftime('%Y-%m-%d'))}

Transit Positions:
{json.dumps(raw_data.get('transits', {}), indent=2)}

Natal Chart Data:
{json.dumps(raw_data.get('natal_chart', {'status': 'Not calculated - birth data needed'}), indent=2)}
=== END ASTROLOGY DATA ===
"""

        # Task specification
        task = f"""
=== CURRENT TASK ===
Generate a {prediction_type.upper()} prediction for {zodiac_sign.capitalize()}
This prediction will be saved to the database and displayed on /patterns page
=== END TASK ===
"""

        # Assemble full prompt
        full_prompt = f"""
{ai_instructions}

{base_prompt}

{type_instructions.get(prediction_type, type_instructions['daily'])}

{profile_context}

{astrology_context}

{task}

Now generate the {prediction_type} prediction:
"""
        
        return full_prompt
    
    def _generate_fallback_horoscope(self, zodiac_sign: str, prediction_type: str) -> str:
        """Generate a fallback horoscope if API fails"""
        return f"""**{zodiac_sign.capitalize()} - {prediction_type.capitalize()} Horoscope**

🌟 **Love & Relationships**: The stars align favorably for your connections today. Open communication will strengthen your bonds.

💼 **Career**: Professional opportunities may present themselves. Stay alert and ready to seize the moment.

💪 **Health**: Your energy levels are balanced. Focus on maintaining healthy habits and rest when needed.

🍀 **Lucky Numbers**: 7, 14, 23

*Remember: The universe has a plan for you. Stay positive and trust your journey!*

---
*This prediction is based on your zodiac sign ({zodiac_sign.capitalize()}) stored in your profile.*
"""


# Create a singleton instance
gemini_client = GeminiClient()
