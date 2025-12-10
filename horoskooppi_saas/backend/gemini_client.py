"""
Google Gemini API client for horoscope generation

IMPORTANT RULES FOR AI PREDICTION GENERATION:
1. User's core data (birth_date, birth_time, birth_city, zodiac_sign) comes from the database
2. The zodiac_sign is calculated ONCE from birth_date at registration and CANNOT be changed
3. All predictions MUST use the stored profile data, never user-edited temporary values
4. Every new prediction MUST be saved to the database and listed on /patterns page
5. Predictions are personalized based on: zodiac_sign, birth_date, birth_time, birth_city

CRITICAL: NO FALLBACK HOROSCOPES ARE ALLOWED
- Gemini MUST generate all horoscopes directly
- If Gemini fails, return an error - NEVER return fallback text
"""
import os
import google.generativeai as genai
from typing import Optional, Tuple, Any, Dict
from datetime import datetime
import json

# Import generation rules
from gemini_rules import GENERAL_RULES, DAILY_RULES, WEEKLY_RULES, MONTHLY_RULES, VOCABULARY_BANK


class GeminiAPIError(Exception):
    """Exception raised when Gemini API fails to generate horoscope"""
    pass


class GeminiClient:
    """Client for interacting with Google Gemini API for personalized horoscope generation"""
    
    def __init__(self):
        """Initialize Gemini client"""
        self.model = None
        self._initialized = False
        self._api_key_available = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Gemini client"""
        if self._initialized:
            return
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY not set. Horoscope generation will fail.")
            self._initialized = True
            self._api_key_available = False
            return
        
        try:
            genai.configure(api_key=api_key)
            # Use gemini-2.5-flash model
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self._initialized = True
            self._api_key_available = True
        except Exception as e:
            print(f"ERROR: Failed to initialize Gemini: {e}")
            self._initialized = True
            self._api_key_available = False
    
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

        # 2. Generate Content - NO FALLBACKS ALLOWED
        if not self.model:
            raise GeminiAPIError("Gemini API not initialized. GEMINI_API_KEY may not be set.")
        
        prompt = self._create_prompt(zodiac_sign, prediction_type, raw_data, user_profile)
        
        try:
            response = self.model.generate_content(prompt)
            if not response.text:
                raise GeminiAPIError("Gemini returned empty response")
            return response.text, raw_data
        except GeminiAPIError:
            raise
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise GeminiAPIError(f"Failed to generate horoscope: {str(e)}")
    
    def _create_prompt(
        self, 
        zodiac_sign: str, 
        prediction_type: str, 
        raw_data: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a technically precise astrology prompt.
        
        The AI will generate predictions STRICTLY from the provided chart data.
        Output format: 3 sections (Key Influences, Detailed Prediction, Technical Summary)
        """
        
        # Get prediction language from user profile (default to 'fi' for Finnish)
        prediction_language = "fi"
        if user_profile:
            prediction_language = user_profile.get("prediction_language", "fi")
        
        # Language instructions
        language_instructions = {
            "fi": "IMPORTANT: Write ALL predictions in Finnish (Suomi). Use natural Finnish language.",
            "sv": "IMPORTANT: Write ALL predictions in Swedish (Svenska). Use natural Swedish language.",
            "no": "IMPORTANT: Write ALL predictions in Norwegian (Norsk). Use natural Norwegian language.",
            "da": "IMPORTANT: Write ALL predictions in Danish (Dansk). Use natural Danish language.",
            "de": "IMPORTANT: Write ALL predictions in German (Deutsch). Use natural German language.",
            "fr": "IMPORTANT: Write ALL predictions in French (Français). Use natural French language.",
            "es": "IMPORTANT: Write ALL predictions in Spanish (Español). Use natural Spanish language.",
            "it": "IMPORTANT: Write ALL predictions in Italian (Italiano). Use natural Italian language.",
            "en": "Write predictions in English."
        }
        
        lang_instruction = language_instructions.get(prediction_language, language_instructions["en"])
        
        # Get type-specific rules
        type_rules = {
            "daily": DAILY_RULES,
            "weekly": WEEKLY_RULES,
            "monthly": MONTHLY_RULES
        }
        specific_rules = type_rules.get(prediction_type, DAILY_RULES)
        
        # Get user age for age-specific voice
        user_age = None
        if user_profile:
            user_age = user_profile.get("age")
        
        age_instruction = ""
        if user_age is not None:
            age_instruction = f"\nIMPORTANT: The user's age is {user_age} years old. You MUST use the age-specific voice guidelines from GENERAL_RULES section 6 to match the appropriate tone, focus, and language style for this age group."
        
        # SYSTEM PROMPT - Strict technical rules with gemini_rules
        system_prompt = f"""You are an astrology prediction engine.

{lang_instruction}{age_instruction}

{GENERAL_RULES}

{specific_rules}

{VOCABULARY_BANK}

You generate predictions strictly and only from the technical chart data provided to you.

Never invent planets, aspects, angles or meanings not included in the input.

Follow these rules:
1. Use only the data given in the input JSON.
2. Interpret planetary positions, houses, and aspects using classical astrological rules.
3. Stronger aspects (orb under 1 degree) must be highlighted clearly.
4. Tie each interpretation to the correct life area based on the house system.
5. If no relevant aspect exists for a topic, say nothing about that topic.
6. Produce a prediction that feels personal but is fully traceable back to the data.
7. Do not mention that you are an AI.
8. Never change the user's zodiac sign.

All predictions must be derived from:
- natal positions
- current transits
- aspects between current and natal planets
- house meanings
- planetary nature

IMMUTABLE DATA RULES:
- The user's zodiac_sign is calculated from birth_date and CANNOT be changed
- All birth data (birth_date, birth_time, birth_city) are permanent
- Predictions must use stored profile data, not user-edited values"""

        # Build natal chart array
        natal_chart = raw_data.get("natal_chart", {})
        birth_chart_array = []
        
        if natal_chart and "positions" in natal_chart:
            positions = natal_chart.get("positions", {})
            house_num = 1
            for planet, data in positions.items():
                if isinstance(data, dict):
                    birth_chart_array.append({
                        "planet": planet,
                        "sign": data.get("sign", "Unknown"),
                        "degree": data.get("deg", 0),
                        "lon": data.get("lon", 0),  # Absolute longitude for aspect calculations
                        "house": data.get("house", house_num % 12 + 1)
                    })
                    house_num += 1
        else:
            # Default natal positions based on zodiac sign if no birth data
            birth_chart_array = [
                {"planet": "Sun", "sign": zodiac_sign.capitalize(), "degree": 15.0, "house": 1},
                {"planet": "Moon", "sign": "Unknown", "degree": 0, "house": 4},
                {"planet": "Mercury", "sign": zodiac_sign.capitalize(), "degree": 10.0, "house": 1},
                {"planet": "Venus", "sign": "Unknown", "degree": 0, "house": 2},
                {"planet": "Mars", "sign": "Unknown", "degree": 0, "house": 6}
            ]
        
        # Build current transits array
        transits = raw_data.get("transits", {})
        current_transits_array = []
        
        if transits and "positions" in transits:
            transit_positions = transits.get("positions", {})
            house_num = 1
            for planet, data in transit_positions.items():
                if isinstance(data, dict):
                    current_transits_array.append({
                        "planet": planet,
                        "sign": data.get("sign", "Unknown"),
                        "degree": data.get("deg", 0),
                        "lon": data.get("lon", 0),  # Absolute longitude for aspect calculations
                        "house": house_num % 12 + 1
                    })
                    house_num += 1
        else:
            # Use current date approximations
            current_transits_array = [
                {"planet": "Sun", "sign": self._get_current_sun_sign(), "degree": 15.0, "house": 1},
                {"planet": "Moon", "sign": "Variable", "degree": 0, "house": 4},
                {"planet": "Mercury", "sign": self._get_current_sun_sign(), "degree": 10.0, "house": 1},
                {"planet": "Mars", "sign": "Capricorn", "degree": 15.0, "house": 5},
                {"planet": "Venus", "sign": "Scorpio", "degree": 20.0, "house": 2}
            ]
        
        # Calculate aspects between transits and natal
        aspects_array = self._calculate_aspects(birth_chart_array, current_transits_array)
        
        # Build the structured input JSON
        user_name = ""
        if user_profile:
            first = user_profile.get("first_name", "")
            last = user_profile.get("last_name", "")
            user_name = f"{first} {last}".strip() or "Cosmic Traveler"
        else:
            user_name = "Cosmic Traveler"
        
        input_data = {
            "user": {
                "name": user_name,
                "sun_sign": zodiac_sign.capitalize(),
                "birth_chart": birth_chart_array
            },
            "current_transits": current_transits_array,
            "aspects": aspects_array
        }
        
        # Output format instructions based on prediction type
        output_instructions = {
            "daily": """
OUTPUT FORMAT (3 sections required):

**Key Influences Today**
Short bullet points of the strongest transits (orb under 2 degrees).

**Detailed Daily Prediction**
A coherent text of 120 to 200 words that directly references the technical data.

**Technical Summary**
A compact list of all aspects used.
Format: Planet A → Planet B, Aspect, Angle, Orb, House impact.""",
            
            "weekly": """
OUTPUT FORMAT (3 sections required):

**Key Influences This Week**
Bullet points of the strongest transits affecting the week (orb under 3 degrees).

**Detailed Weekly Prediction**
A coherent text of 250 to 400 words covering:
- Overall energy of the week
- Key days to watch
- Themes: growth, relationships, challenges
Directly reference the technical data throughout.

**Technical Summary**
A compact list of all major aspects for the week.
Format: Planet A → Planet B, Aspect, Angle, Orb, House impact.""",
            
            "monthly": """
OUTPUT FORMAT (3 sections required):

**Key Influences This Month**
Bullet points of major planetary movements and lunar phases affecting the month.

**Detailed Monthly Prediction**
A coherent text of 500 to 700 words covering:
- Main theme of the month
- Career and professional life
- Relationships and social connections
- Finances and material matters
- Health and well-being
- Key dates to note
Directly reference the technical data throughout.

**Technical Summary**
A comprehensive list of all major aspects and transits for the month.
Format: Planet A → Planet B, Aspect, Angle, Orb, House impact."""
        }
        
        # Assemble full prompt
        full_prompt = f"""{system_prompt}

{output_instructions.get(prediction_type, output_instructions['daily'])}

=== INPUT DATA (JSON) ===
{json.dumps(input_data, indent=2)}
=== END INPUT DATA ===

Generate the {prediction_type} prediction for {zodiac_sign.capitalize()} now.
Use ONLY the data provided above. Do not invent aspects or positions not in the input."""
        
        return full_prompt
    
    def _get_current_sun_sign(self) -> str:
        """Get the current Sun sign based on date"""
        now = datetime.now()
        month = now.month
        day = now.day
        
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "Capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Aquarius"
        else:
            return "Pisces"
    
    def _calculate_aspects(
        self, 
        natal_chart: list, 
        current_transits: list
    ) -> list:
        """
        Calculate aspects between natal and transit planets.
        Returns list of aspect dictionaries.
        """
        aspects = []
        
        # Aspect definitions: name, angle, orb_allowed
        aspect_definitions = [
            ("Conjunction", 0, 8),
            ("Sextile", 60, 4),
            ("Square", 90, 6),
            ("Trine", 120, 6),
            ("Opposition", 180, 8)
        ]
        
        # House meanings for effect descriptions
        house_meanings = {
            1: "Self and identity",
            2: "Finances and values",
            3: "Communication and learning",
            4: "Home and family",
            5: "Creativity and self-expression",
            6: "Work and health",
            7: "Partnerships and relationships",
            8: "Transformation and shared resources",
            9: "Higher learning and travel",
            10: "Career and public image",
            11: "Friends and aspirations",
            12: "Spirituality and subconscious"
        }
        
        for transit in current_transits:
            for natal in natal_chart:
                # Use absolute longitude (lon) for aspect calculations, fallback to degree if lon not available
                transit_lon = transit.get("lon", transit.get("degree", 0))
                natal_lon = natal.get("lon", natal.get("degree", 0))
                
                # If we only have sign degrees (0-30), we need to estimate absolute longitude
                # This is approximate - ideally we'd have the full longitude
                if transit_lon < 30 and natal_lon < 30:
                    # Estimate: assume middle of sign for approximation
                    # This is not ideal but better than 0
                    transit_sign = transit.get("sign", "Aries")
                    natal_sign = natal.get("sign", "Aries")
                    sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
                    try:
                        transit_sign_idx = sign_order.index(transit_sign) if transit_sign in sign_order else 0
                        natal_sign_idx = sign_order.index(natal_sign) if natal_sign in sign_order else 0
                        transit_lon = (transit_sign_idx * 30) + transit_lon
                        natal_lon = (natal_sign_idx * 30) + natal_lon
                    except:
                        pass
                
                # Calculate angle difference (absolute longitude 0-360)
                diff = abs(transit_lon - natal_lon)
                if diff > 180:
                    diff = 360 - diff
                
                # Check each aspect type
                for aspect_name, aspect_angle, max_orb in aspect_definitions:
                    orb = abs(diff - aspect_angle)
                    
                    if orb <= max_orb:
                        house = natal.get("house", 1)
                        aspects.append({
                            "transit_planet": transit.get("planet", "Unknown"),
                            "natal_planet": natal.get("planet", "Unknown"),
                            "aspect": aspect_name,
                            "angle": round(diff, 1),
                            "orb": round(orb, 1),
                            "house_effect": house_meanings.get(house, "General life areas")
                        })
        
        # Sort by orb (tightest aspects first)
        aspects.sort(key=lambda x: x["orb"])
        
        return aspects[:10]  # Return top 10 tightest aspects


# Create a singleton instance
gemini_client = GeminiClient()
