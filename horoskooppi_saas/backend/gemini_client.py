"""
Google Gemini API client for horoscope generation
"""
import os
import google.generativeai as genai
from typing import Optional, Tuple, Any, Dict
from datetime import datetime
import json

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
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
        prediction_type: str = "daily"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a horoscope prediction for a zodiac sign
        
        Args:
            zodiac_sign: The zodiac sign (e.g., 'aries', 'taurus')
            prediction_type: Type of prediction ('daily', 'weekly', 'monthly')
        
        Returns:
            Tuple containing:
            - Generated horoscope text
            - Dictionary with raw calculation data
        """
        self._ensure_initialized()
        
        # 1. Fetch Astrology Data
        transit_data = {}
        try:
            from astrology_service import astrology_service
            current_date = datetime.now().strftime("%Y-%m-%d")
            # For now, we simulate natal data absence or add placeholders
            transit_data = astrology_service.calculate_transits(current_date)
            # Add date meta
            transit_data["date"] = current_date
        except ImportError:
            print("Astrology service import failed")
            transit_data = {"error": "Service unavailable"}
        except Exception as e:
            print(f"Astrology calculation failed: {e}")
            transit_data = {"error": str(e)}

        # 2. Generate Content
        # If model is not available, use fallback
        if not self.model:
            return self._generate_fallback_horoscope(zodiac_sign, prediction_type), transit_data
        
        prompt = self._create_prompt(zodiac_sign, prediction_type, transit_data)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text, transit_data
        except Exception as e:
            # Fallback response if API fails
            print(f"Gemini API error: {e}. Using fallback.")
            return self._generate_fallback_horoscope(zodiac_sign, prediction_type), transit_data
    
    def _create_prompt(self, zodiac_sign: str, prediction_type: str, transit_data: Dict[str, Any]) -> str:
        """Create a prompt for horoscope generation"""
        
        # Base instructions
        base_prompt = """
You generate personal horoscope predictions for a subscribed user. All predictions must be based on real calculated astrology data including the natal chart, planetary positions, houses, aspects, and current transits. You must never repeat earlier predictions. You always receive the user’s previous predictions as context and must generate fresh, unique content every time. All predictions appear on the user’s logged-in dashboard. Every prediction is permanently saved in the user’s archive and categorized as Daily, Weekly, or Monthly. The newest prediction must always appear first in its category. After generating any new prediction, the system will send the user an email with the subject “Your new personal horoscope is ready”. You must avoid any recycled text or reused structures from previous predictions. Your writing style must be modern, personal, psychologically insightful, and based on astrological interpretation without making supernatural promises.

Inputs provided to you include: the user’s full birth data; the calculated natal chart (Sun, Moon, Rising, planets, houses, aspects); the current date and timezone; current planetary positions; calculated transits; and the user’s entire prediction history so you can ensure the new prediction does not repeat older ones. You are also told the prediction type required: Daily, Weekly or Monthly.
"""

        # Specific instructions by type
        type_instructions = {
            "daily": """
For DAILY predictions, you must calculate: the current Moon sign and Moon house; fast-moving transits affecting the natal Sun, Moon, Rising, Mercury, Venus, and Mars; and all notable daily aspects (conjunctions, sextiles, squares, trines, oppositions). Write the daily prediction as follows: one sentence describing the day’s overall theme; a short section explaining effects on mental clarity, relationships, energy, motivation, and focus; one practical suggestion; a total length of 70 to 120 words. Category: Daily.
""",
            "weekly": """
For WEEKLY predictions, generated every Sunday evening, you must calculate: transits from Jupiter, Saturn, Uranus, Neptune, and Pluto; key Mercury, Venus, and Mars movements; moon phases during the week; retrogrades; and transit impacts on natal houses. Write the weekly prediction as: an overview of the week’s atmosphere; three thematic areas (growth, relationships, challenges); one practical weekly recommendation; a length of 180 to 300 words. Category: Weekly.
""",
            "monthly": """
For MONTHLY predictions, generated on the 1st day of each month, you must calculate: all long-term aspects from outer planets; New Moon and Full Moon with their house placements; Mercury, Venus, and Mars movements by house; major shifts or retrogrades; and which life areas are emphasized this month. Write the monthly prediction as: one main theme of the month; a description of significant astrological events; predictions covering at least three life areas (career, relationships, finances, well-being); and a final summary with monthly guidance. Length 400 to 700 words. Category: Monthly.
"""
        }

        technical_rules = """
You must ensure that before generating a new prediction, you compare the new output with the provided history of earlier predictions. You must avoid reusing sentence structures, metaphors, or themes, and the content must be genuinely new. Use consistent astrological logic and remain aligned with the user’s natal chart.

Technical rules for star chart calculation: For natal chart generation, convert the user’s birth time to UTC; compute planetary positions with a library such as Swiss Ephemeris, Astropy, Flatlib, or PyEphem; calculate Ascendant and Midheaven; generate a 12-house system (recommended: Placidus); identify planets by sign and by house; compute all aspects using orb allowances. For daily transits, compute planetary positions for the current date, determine aspects between transit planets and natal planets, identify house transits, identify the Moon sign and Moon house, determine the Moon phase, and check which planets are retrograde. For weekly calculations, compute all exact aspects occurring during the week, sign ingresses, major moon phase events, and slow planet influences. For monthly calculations, compute all planetary sign changes, New Moon and Full Moon placements, all major aspects from outer planets, and house transitions of Mercury, Venus, and Mars.

The system will deliver structured input to you including natal chart data, current transit data, prediction type, and previous predictions. You must output only the new prediction text according to the category rules above. Ensure all interpretations are unique, consistent with the transits, and clearly structured. Always create content that feels newly written, not derivative of earlier predictions.
"""

        # Context construction
        astrology_context = f"""
        CALCULATED ASTROLOGY DATA:
        Current Date: {transit_data.get('date', 'Unknown')}
        
        Transits (Current Planetary Positions):
        {json.dumps(transit_data, indent=2)}
        """

        context_data = f"""
        CURRENT TASK:
        Prediction Type: {prediction_type.upper()}
        Zodiac Sign: {zodiac_sign.capitalize()}
        
        {astrology_context}
        
        [SYSTEM NOTE: Full natal chart data is currently unavailable as user birth data is not yet collected. 
        Please generate a {prediction_type} prediction for {zodiac_sign.capitalize()} 
        using the provided Transit data and general archetypes for this sign.]
        """

        full_prompt = f"{base_prompt}\n\n{type_instructions.get(prediction_type, type_instructions['daily'])}\n\n{technical_rules}\n\n{context_data}"
        
        return full_prompt
    
    def _generate_fallback_horoscope(self, zodiac_sign: str, prediction_type: str) -> str:
        """Generate a fallback horoscope if API fails"""
        return f"""**{zodiac_sign.capitalize()} - {prediction_type.capitalize()} Horoscope**

🌟 Love & Relationships: The stars align favorably for your connections today. Open communication will strengthen your bonds.

💼 Career: Professional opportunities may present themselves. Stay alert and ready to seize the moment.

💪 Health: Your energy levels are balanced. Focus on maintaining healthy habits and rest when needed.

🍀 Lucky Numbers: 7, 14, 23

Remember: The universe has a plan for you. Stay positive and trust your journey!"""

# Create a singleton instance
gemini_client = GeminiClient()
