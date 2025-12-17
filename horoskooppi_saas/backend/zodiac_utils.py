"""
Zodiac Sign Calculation Utility

This module calculates the zodiac sign from a birth date.
The zodiac sign is determined ONCE at registration and CANNOT be changed.
All predictions must use this calculated sign.
"""
from datetime import datetime
from typing import Optional

# Zodiac sign date ranges (month, day) - start dates for each sign
ZODIAC_DATES = [
    ((1, 20), (2, 18), "aquarius"),    # Jan 20 - Feb 18
    ((2, 19), (3, 20), "pisces"),      # Feb 19 - Mar 20
    ((3, 21), (4, 19), "aries"),       # Mar 21 - Apr 19
    ((4, 20), (5, 20), "taurus"),      # Apr 20 - May 20
    ((5, 21), (6, 20), "gemini"),      # May 21 - Jun 20
    ((6, 21), (7, 22), "cancer"),      # Jun 21 - Jul 22
    ((7, 23), (8, 22), "leo"),         # Jul 23 - Aug 22
    ((8, 23), (9, 22), "virgo"),       # Aug 23 - Sep 22
    ((9, 23), (10, 22), "libra"),      # Sep 23 - Oct 22
    ((10, 23), (11, 21), "scorpio"),   # Oct 23 - Nov 21
    ((11, 22), (12, 21), "sagittarius"), # Nov 22 - Dec 21
    ((12, 22), (1, 19), "capricorn"),  # Dec 22 - Jan 19
]

ZODIAC_INFO = {
    "aries": {"element": "fire", "modality": "cardinal", "ruler": "Mars", "symbol": "♈"},
    "taurus": {"element": "earth", "modality": "fixed", "ruler": "Venus", "symbol": "♉"},
    "gemini": {"element": "air", "modality": "mutable", "ruler": "Mercury", "symbol": "♊"},
    "cancer": {"element": "water", "modality": "cardinal", "ruler": "Moon", "symbol": "♋"},
    "leo": {"element": "fire", "modality": "fixed", "ruler": "Sun", "symbol": "♌"},
    "virgo": {"element": "earth", "modality": "mutable", "ruler": "Mercury", "symbol": "♍"},
    "libra": {"element": "air", "modality": "cardinal", "ruler": "Venus", "symbol": "♎"},
    "scorpio": {"element": "water", "modality": "fixed", "ruler": "Pluto", "symbol": "♏"},
    "sagittarius": {"element": "fire", "modality": "mutable", "ruler": "Jupiter", "symbol": "♐"},
    "capricorn": {"element": "earth", "modality": "cardinal", "ruler": "Saturn", "symbol": "♑"},
    "aquarius": {"element": "air", "modality": "fixed", "ruler": "Uranus", "symbol": "♒"},
    "pisces": {"element": "water", "modality": "mutable", "ruler": "Neptune", "symbol": "♓"},
}


def calculate_zodiac_sign(birth_date: str) -> Optional[str]:
    """
    Calculate zodiac sign from birth date string.
    
    IMPORTANT: This calculation is performed ONCE during registration.
    The result is stored permanently and CANNOT be modified by the user.
    All predictions MUST use this calculated zodiac sign.
    
    Args:
        birth_date: Date string in format "YYYY-MM-DD"
        
    Returns:
        Zodiac sign as lowercase string (e.g., "libra", "aries")
        Returns None if birth_date is invalid
    """
    if not birth_date:
        return None
    
    try:
        # Parse the date
        if isinstance(birth_date, str):
            date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        else:
            date_obj = birth_date
            
        month = date_obj.month
        day = date_obj.day
        
        # Special case for Capricorn (spans year boundary)
        if (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "capricorn"
        
        # Check other signs
        for (start_month, start_day), (end_month, end_day), sign in ZODIAC_DATES:
            if start_month == end_month:
                if month == start_month and start_day <= day <= end_day:
                    return sign
            else:
                if (month == start_month and day >= start_day) or (month == end_month and day <= end_day):
                    return sign
        
        return None
        
    except (ValueError, TypeError) as e:
        print(f"Error calculating zodiac sign: {e}")
        return None


def get_zodiac_info(sign: str) -> dict:
    """
    Get detailed information about a zodiac sign.
    
    Args:
        sign: Zodiac sign name (lowercase)
        
    Returns:
        Dictionary with element, modality, ruler, and symbol
    """
    return ZODIAC_INFO.get(sign.lower(), {})


def get_zodiac_display_name(sign: str) -> str:
    """Get properly capitalized zodiac sign name."""
    return sign.capitalize() if sign else "Unknown"


def validate_birth_date(birth_date: str) -> bool:
    """
    Validate that a birth date string is valid.
    
    Args:
        birth_date: Date string in format "YYYY-MM-DD"
        
    Returns:
        True if valid, False otherwise
    """
    if not birth_date:
        return False
    
    try:
        date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        # Check reasonable date range (not in future, not before 1900)
        if date_obj.year < 1900 or date_obj > datetime.now():
            return False
        return True
    except ValueError:
        return False


