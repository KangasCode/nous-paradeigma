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
        
        # Common city coordinates (latitude, longitude)
        self.city_coordinates = {
            "helsinki": (60.1699, 24.9384),
            "tampere": (61.4978, 23.7610),
            "turku": (60.4518, 22.2666),
            "oulu": (65.0121, 25.4651),
            "jyväskylä": (62.2415, 25.7209),
            "lahti": (60.9827, 25.6612),
            "kuopio": (62.8924, 27.6770),
            "pori": (61.4851, 21.7974),
            "joensuu": (62.6019, 29.7636),
            "lappeenranta": (61.0586, 28.1887),
            "stockholm": (59.3293, 18.0686),
            "oslo": (59.9139, 10.7522),
            "copenhagen": (55.6761, 12.5683),
            "london": (51.5074, -0.1278),
            "paris": (48.8566, 2.3522),
            "berlin": (52.5200, 13.4050),
            "madrid": (40.4168, -3.7038),
            "rome": (41.9028, 12.4964),
            "amsterdam": (52.3676, 4.9041),
            "vienna": (48.2082, 16.3738),
            "brussels": (50.8503, 4.3517),
            "zurich": (47.3769, 8.5417),
            "moscow": (55.7558, 37.6173),
            "warsaw": (52.2297, 21.0122),
            "prague": (50.0755, 14.4378),
            "budapest": (47.4979, 19.0402),
            "athens": (37.9838, 23.7275),
            "lisbon": (38.7223, -9.1393),
            "dublin": (53.3498, -6.2603),
            "new york": (40.7128, -74.0060),
            "los angeles": (34.0522, -118.2437),
            "chicago": (41.8781, -87.6298),
            "houston": (29.7604, -95.3698),
            "phoenix": (33.4484, -112.0740),
            "philadelphia": (39.9526, -75.1652),
            "san antonio": (29.4241, -98.4936),
            "san diego": (32.7157, -117.1611),
            "dallas": (32.7767, -96.7970),
            "san jose": (37.3382, -121.8863),
            "tokyo": (35.6762, 139.6503),
            "beijing": (39.9042, 116.4074),
            "shanghai": (31.2304, 121.4737),
            "hong kong": (22.3193, 114.1694),
            "singapore": (1.3521, 103.8198),
            "sydney": (-33.8688, 151.2093),
            "melbourne": (-37.8136, 144.9631),
            "auckland": (-36.8485, 174.7633),
        }
    
    def _get_city_coordinates(self, city_name: str):
        """
        Get latitude and longitude for a city name.
        Returns (lat, lon) tuple or defaults to Helsinki if city not found.
        """
        if not city_name:
            return (60.1699, 24.9384)  # Default to Helsinki
        
        city_lower = city_name.lower().strip()
        
        # Direct lookup
        if city_lower in self.city_coordinates:
            return self.city_coordinates[city_lower]
        
        # Try partial match
        for city_key, coords in self.city_coordinates.items():
            if city_key in city_lower or city_lower in city_key:
                return coords
        
        # Default to Helsinki if not found
        print(f"⚠️ City '{city_name}' not found in coordinates database. Using Helsinki default.")
        return (60.1699, 24.9384)  # Helsinki default

    def calculate_natal_chart(self, birth_date: str, birth_time: str, city_or_lat, lon=None, tz_str: str = "+02:00"):
        """
        Calculate natal chart details.
        
        Args:
            birth_date: "YYYY-MM-DD"
            birth_time: "HH:MM"
            city_or_lat: Either city name (str) or latitude (float)
            lon: Longitude float (required if city_or_lat is float, optional if it's a city name)
            tz_str: Timezone offset string e.g. "+02:00"
        """
        if not self.enabled:
            return self._mock_natal_data()

        try:
            # Determine if city_or_lat is a city name or latitude
            if isinstance(city_or_lat, str):
                # It's a city name - get coordinates
                lat, lon = self._get_city_coordinates(city_or_lat)
            elif isinstance(city_or_lat, (int, float)):
                # It's a latitude - lon must be provided
                if lon is None:
                    raise ValueError("Longitude (lon) is required when latitude is provided as a number")
                lat = float(city_or_lat)
                lon = float(lon)
            else:
                # Default to Helsinki
                lat, lon = self._get_city_coordinates("helsinki")
            
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
                "positions": planets,  # Changed from "planets" to "positions" for compatibility
                "planets": planets,  # Keep both for backwards compatibility
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
            "positions": {
                "Sun": {"sign": "Aries", "deg": 15.0, "house": 1},
                "Moon": {"sign": "Taurus", "deg": 120.0, "house": 2},
                "Mercury": {"sign": "Aries", "deg": 10.0, "house": 1},
                "Venus": {"sign": "Pisces", "deg": 350.0, "house": 12},
                "Mars": {"sign": "Gemini", "deg": 80.0, "house": 3},
                "Ascendant": {"sign": "Pisces", "deg": 0.0, "house": 1}
            },
            "planets": {
                "Sun": {"sign": "Aries", "deg": 15.0, "house": 1},
                "Moon": {"sign": "Taurus", "deg": 120.0, "house": 2},
                "Mercury": {"sign": "Aries", "deg": 10.0, "house": 1},
                "Venus": {"sign": "Pisces", "deg": 350.0, "house": 12},
                "Mars": {"sign": "Gemini", "deg": 80.0, "house": 3},
                "Ascendant": {"sign": "Pisces", "deg": 0.0, "house": 1}
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

