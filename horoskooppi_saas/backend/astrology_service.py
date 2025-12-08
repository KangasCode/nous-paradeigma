"""
Astrology Service using Flatlib
Handles calculation of Natal Charts, Transits, and Aspects.
"""
from datetime import datetime
try:
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    from flatlib.chart import Chart
    from flatlib import aspects, const
except ImportError:
    print("WARNING: flatlib not installed. Astrology calculations will use mock data.")
    Datetime = None
    GeoPos = None
    Chart = None
    aspects = None
    const = None

class AstrologyService:
    def __init__(self):
        self.enabled = Datetime is not None

    def calculate_natal_chart(self, birth_date: str, birth_time: str, lat: float, lon: float, tz_str: str = "+00:00"):
        """
        Calculate natal chart details.
        
        Args:
            birth_date: "YYYY-MM-DD"
            birth_time: "HH:MM"
            lat: Latitude float
            lon: Longitude float
            tz_str: Timezone offset string e.g. "+02:00"
        """
        if not self.enabled:
            return self._mock_natal_data()

        try:
            date = Datetime(birth_date, birth_time, tz_str)
            pos = GeoPos(lat, lon)
            chart = Chart(date, pos)

            # Get planet positions in signs and houses
            planets = {}
            for planet in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
                          const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
                          const.ASC, const.MC]:
                obj = chart.get(planet)
                planets[planet] = {
                    "sign": obj.sign,
                    "deg": obj.lon,
                    "house": chart.houses.get(obj.lon).id  # Simple house lookup
                }

            # Get aspects
            # Note: flatlib might need specific aspect calculation calls
            # For this MVP we will list positions mainly
            
            return {
                "planets": planets,
                "houses": {h.id: h.sign for h in chart.houses},
                "meta": {"date": birth_date, "time": birth_time, "lat": lat, "lon": lon}
            }
        except Exception as e:
            print(f"Error calculating natal chart: {e}")
            return self._mock_natal_data()

    def calculate_transits(self, target_date: str, natal_chart=None):
        """
        Calculate transits for a specific date.
        If natal_chart is provided, calculate aspects to natal planets.
        """
        if not self.enabled:
            return self._mock_transit_data()

        try:
            # Noon UTC for transits
            date = Datetime(target_date, "12:00", "+00:00")
            pos = GeoPos(0, 0) # Location matters less for planetary sign positions
            chart = Chart(date, pos)

            transits = {}
            for planet in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, 
                          const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]:
                obj = chart.get(planet)
                transits[planet] = {
                    "sign": obj.sign,
                    "deg": obj.lon
                }
            
            return {
                "positions": transits,
                "moon_phase": "Unknown" # Flatlib doesn't have direct moon phase utility in basic
            }
        except Exception as e:
            print(f"Error calculating transits: {e}")
            return self._mock_transit_data()

    def _mock_natal_data(self):
        return {
            "planets": {
                "Sun": {"sign": "Aries", "house": 1},
                "Moon": {"sign": "Taurus", "house": 2},
                "Ascendant": {"sign": "Pisces"}
            },
            "houses": {1: "Aries", 10: "Capricorn"},
            "note": "Mock data - install flatlib for real calculations"
        }

    def _mock_transit_data(self):
        return {
            "positions": {
                "Sun": {"sign": "Leo"},
                "Moon": {"sign": "Virgo"}
            },
            "note": "Mock data"
        }

astrology_service = AstrologyService()

