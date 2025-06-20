"""
Google Places API client for searching locations
"""

import requests
import time
from typing import List, Dict, Optional
from .config import Config


class PlacesAPIClient:
    """Client for Google Places API"""
    
    def __init__(self, config: Config):
        """
        Initialize API client
        
        Args:
            config (Config): Configuration object containing API key and settings
        """
        self.config = config
        self.session = requests.Session()
    
    def nearby_search(
        self, 
        lat: float, 
        lng: float, 
        radius_km: float, 
        keyword: str, 
        language: str = "ko"
    ) -> List[Dict]:
        """
        Search for places near the given location
        
        Args:
            lat (float): Latitude
            lng (float): Longitude  
            radius_km (float): Search radius in kilometers
            keyword (str): Search keyword
            language (str): Language for results
            
        Returns:
            List[Dict]: List of place information dictionaries
        """
        url = self.config.get_places_url()
        
        params = {
            'location': f"{lat},{lng}",
            'radius': int(radius_km * 1000),  # Convert km to meters
            'keyword': keyword,
            'language': language,
            'key': self.config.api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK':
                return self._parse_places(data.get('results', []), lat, lng, keyword)
            elif data.get('status') == 'ZERO_RESULTS':
                return []
            else:
                print(f"API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    def _parse_places(self, places: List[Dict], search_lat: float, search_lng: float, keyword: str) -> List[Dict]:
        """
        Parse places data from API response
        
        Args:
            places (List[Dict]): Raw places data from API
            search_lat (float): Search center latitude
            search_lng (float): Search center longitude
            keyword (str): Search keyword
            
        Returns:
            List[Dict]: Parsed place information
        """
        parsed_places = []
        
        for place in places:
            try:
                location = place.get('geometry', {}).get('location', {})
                place_lat = location.get('lat')
                place_lng = location.get('lng')
                
                if place_lat is None or place_lng is None:
                    continue
                
                # Calculate distance from search center
                distance = self._calculate_distance(search_lat, search_lng, place_lat, place_lng)
                
                parsed_place = {
                    'place_id': place.get('place_id'),
                    'name': place.get('name', ''),
                    'address': place.get('vicinity', ''),
                    'lat': place_lat,
                    'lng': place_lng,
                    'rating': place.get('rating', 0),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'types': place.get('types', []),
                    'keyword': keyword,
                    'distance': round(distance, 2),
                    'price_level': place.get('price_level'),
                    'opening_hours': place.get('opening_hours', {}).get('open_now'),
                    'photos': len(place.get('photos', [])) > 0,
                    'website': None,  # Will be filled by place details API
                    'emails': [],      # Will be filled by email extraction
                    'phone': None     # Will be filled by place details API
                }
                
                parsed_places.append(parsed_place)
                
            except Exception as e:
                print(f"Error parsing place: {e}")
                continue
        
        return parsed_places
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lng1: First point coordinates
            lat2, lng2: Second point coordinates
            
        Returns:
            float: Distance in kilometers
        """
        import math
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371.0 * c  # Earth radius in km
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific place
        
        Args:
            place_id (str): Google Places place ID
            
        Returns:
            Optional[Dict]: Detailed place information or None if error
        """
        url = self.config.get_details_url()
        
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,website,opening_hours,rating,reviews',
            'language': 'ko',
            'key': self.config.api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('result', {})
            else:
                print(f"Place details API Error: {data.get('status')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error getting place details: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting place details: {e}")
            return None
    
    def enrich_places_with_details(self, places: List[Dict]) -> List[Dict]:
        """
        Enrich places with detailed information including website
        
        Args:
            places (List[Dict]): List of places from nearby search
            
        Returns:
            List[Dict]: Places enriched with detailed information
        """
        enriched_places = []
        
        for place in places:
            place_id = place.get('place_id')
            if not place_id:
                enriched_places.append(place)
                continue
            
            try:
                # Get detailed information
                details = self.get_place_details(place_id)
                
                if details:
                    # Update place with detailed information
                    place['website'] = details.get('website')
                    place['phone'] = details.get('formatted_phone_number')
                    place['formatted_address'] = details.get('formatted_address', place.get('address'))
                
                enriched_places.append(place)
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error enriching place {place.get('name', 'Unknown')}: {e}")
                enriched_places.append(place)
        
        return enriched_places 