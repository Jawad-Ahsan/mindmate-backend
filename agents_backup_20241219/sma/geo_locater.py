# geo_locator.py

import math
import aiohttp
import logging
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Represents a geographic location with coordinates and address info."""
    latitude: float
    longitude: float
    address: str
    city: str = ""
    state: str = ""
    country: str = ""

@dataclass
class DistanceResult:
    """Represents the distance calculation result between two locations."""
    distance_km: float
    distance_miles: float
    patient_location: Location
    specialist_location: Location


class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str = ""
    state: str = ""
    country: str = ""


class AsyncGeoLocationService:
    """Async service for handling geolocation and distance calculations."""
    
    def __init__(self, use_free_service: bool = True):
        self.use_free_service = use_free_service
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'MindMateLocationService/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def geocode_address(self, address: str) -> Optional[Location]:
        """Convert an address to coordinates using geocoding API."""
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            async with self.session.get(self.nominatim_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data:
                    result = data[0]
                    address_details = result.get('address', {})

                    return Location(
                        latitude=float(result['lat']),
                        longitude=float(result['lon']),
                        address=result.get('display_name', address),
                        city=address_details.get('city', address_details.get('town', '')),
                        state=address_details.get('state', ''),
                        country=address_details.get('country', '')
                    )

        except (aiohttp.ClientError, KeyError, ValueError) as e:
            logger.error(f"Nominatim Geocoding error: {e}")

        return None

    def calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate the distance between two locations using the Haversine formula."""
        lat1_rad = math.radians(loc1.latitude)
        lon1_rad = math.radians(loc1.longitude)
        lat2_rad = math.radians(loc2.latitude)
        lon2_rad = math.radians(loc2.longitude)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        earth_radius_km = 6371
        return earth_radius_km * c

    def km_to_miles(self, km: float) -> float:
        """Convert kilometers to miles."""
        return km * 0.621371

    async def get_patient_specialist_distance(self, patient_address: str, 
                                              specialist_address: str) -> Optional[DistanceResult]:
        """Calculate distance between patient and specialist locations."""
        patient_location = await self.geocode_address(patient_address)
        specialist_location = await self.geocode_address(specialist_address)

        if not patient_location or not specialist_location:
            return None

        distance_km = self.calculate_distance(patient_location, specialist_location)
        distance_miles = self.km_to_miles(distance_km)

        return DistanceResult(
            distance_km=round(distance_km, 2),
            distance_miles=round(distance_miles, 2),
            patient_location=patient_location,
            specialist_location=specialist_location
        )
