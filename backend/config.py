"""
Configuration management for the search engine
"""

class Config:
    """Configuration class for API settings and constants"""
    
    def __init__(self, api_key: str):
        """
        Initialize configuration
        
        Args:
            api_key (str): Google Places API key
        """
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.max_results_per_request = 20
        self.earth_radius_km = 6371.0
        
    def get_places_url(self) -> str:
        """Get Google Places API nearby search URL"""
        return f"{self.base_url}/nearbysearch/json"
    
    def get_details_url(self) -> str:
        """Get Google Places API place details URL"""
        return f"{self.base_url}/details/json" 