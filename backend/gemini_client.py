"""
Google Gemini API client for horoscope generation
"""
import os
import google.generativeai as genai
from typing import Optional

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
    ) -> str:
        """
        Generate a horoscope prediction for a zodiac sign
        
        Args:
            zodiac_sign: The zodiac sign (e.g., 'aries', 'taurus')
            prediction_type: Type of prediction ('daily', 'weekly', 'monthly')
        
        Returns:
            Generated horoscope text
        """
        self._ensure_initialized()
        
        # If model is not available, use fallback
        if not self.model:
            return self._generate_fallback_horoscope(zodiac_sign, prediction_type)
        
        prompt = self._create_prompt(zodiac_sign, prediction_type)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Fallback response if API fails
            print(f"Gemini API error: {e}. Using fallback.")
            return self._generate_fallback_horoscope(zodiac_sign, prediction_type)
    
    def _create_prompt(self, zodiac_sign: str, prediction_type: str) -> str:
        """Create a prompt for horoscope generation"""
        zodiac_sign_capitalized = zodiac_sign.capitalize()
        
        prompts = {
            "daily": f"""Generate a personalized daily horoscope for {zodiac_sign_capitalized}. 
            Include insights about: love, career, health, and lucky numbers. 
            Make it positive, engaging, and around 150-200 words. 
            Format it with clear sections.""",
            
            "weekly": f"""Generate a personalized weekly horoscope for {zodiac_sign_capitalized}. 
            Include detailed predictions for: relationships, professional life, wellness, and financial matters. 
            Make it insightful and optimistic, around 250-300 words.
            Format it with clear sections for each area.""",
            
            "monthly": f"""Generate a comprehensive monthly horoscope for {zodiac_sign_capitalized}. 
            Include in-depth predictions for: love and relationships, career and opportunities, 
            health and well-being, financial outlook, and personal growth. 
            Make it detailed and inspiring, around 400-500 words.
            Format it with clear sections and include key dates to watch."""
        }
        
        return prompts.get(prediction_type, prompts["daily"])
    
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

