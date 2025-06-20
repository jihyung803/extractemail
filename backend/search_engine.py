"""
Grid-based search engine for location searches
"""

import time
from typing import List, Dict, Set
from .config import Config
from .grid_calculator import GridCalculator
from .places_api import PlacesAPIClient
from .email_extractor import EmailExtractor


class GridSearchEngine:
    """Main search engine that performs grid-based location searches"""
    
    def __init__(self, config: Config):
        """
        Initialize search engine
        
        Args:
            config (Config): Configuration object
        """
        self.config = config
        self.grid_calculator = GridCalculator()
        self.api_client = PlacesAPIClient(config)
        self.email_extractor = EmailExtractor()
        
    def search_grid(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float,
        keywords: List[str],
        grid_size: int = 3,
        delay_between_requests: float = 0.1,
        extract_emails: bool = False
    ) -> List[Dict]:
        """
        Perform grid-based search for multiple keywords
        
        Args:
            center_lat (float): Center latitude
            center_lng (float): Center longitude
            radius_km (float): Search radius in kilometers
            keywords (List[str]): List of search keywords
            grid_size (int): Grid size (NxN)
            delay_between_requests (float): Delay between API requests in seconds
            extract_emails (bool): Whether to extract emails from websites
            
        Returns:
            List[Dict]: Combined search results from all grid cells and keywords
        """
        all_results = []
        seen_place_ids = set()
        
        # Calculate grid points
        grid_points = self.grid_calculator.calculate_grid_points(
            center_lat, center_lng, radius_km, grid_size
        )
        
        total_searches = len(grid_points) * len(keywords)
        current_search = 0
        
        print(f"Starting grid search: {len(grid_points)} grid points × {len(keywords)} keywords = {total_searches} total searches")
        
        # Search each grid point for each keyword
        for grid_lat, grid_lng, grid_radius in grid_points:
            for keyword in keywords:
                current_search += 1
                print(f"Search {current_search}/{total_searches}: Grid({grid_lat:.4f}, {grid_lng:.4f}) Keyword='{keyword}'")
                
                try:
                    # Perform search for current grid cell and keyword
                    results = self.api_client.nearby_search(
                        lat=grid_lat,
                        lng=grid_lng,
                        radius_km=grid_radius,
                        keyword=keyword
                    )
                    
                    # Filter out duplicates and results outside original radius
                    for result in results:
                        place_id = result.get('place_id')
                        
                        # Skip if we've already seen this place
                        if place_id in seen_place_ids:
                            continue
                        
                        # Check if result is within original search radius
                        distance_from_center = self.grid_calculator.calculate_distance(
                            center_lat, center_lng,
                            result['lat'], result['lng']
                        )
                        
                        if distance_from_center <= radius_km:
                            result['distance_from_center'] = round(distance_from_center, 2)
                            all_results.append(result)
                            seen_place_ids.add(place_id)
                    
                    print(f"  Found {len(results)} results, {len(all_results)} total unique results so far")
                    
                except Exception as e:
                    print(f"  Error in search: {e}")
                
                # Add delay between requests to avoid rate limiting
                if delay_between_requests > 0:
                    time.sleep(delay_between_requests)
        
        # Enrich results with detailed information including websites
        print("Enriching results with detailed information...")
        all_results = self.api_client.enrich_places_with_details(all_results)
        
        # Extract emails if requested
        if extract_emails:
            print("Extracting emails from websites...")
            all_results = self._extract_emails_for_places(all_results)
        
        # Sort results by distance from center
        all_results.sort(key=lambda x: x.get('distance_from_center', float('inf')))
        
        print(f"Grid search completed: {len(all_results)} unique results found")
        return all_results
    
    def search_single_point(
        self,
        lat: float,
        lng: float,
        radius_km: float,
        keywords: List[str],
        delay_between_requests: float = 0.1,
        extract_emails: bool = False
    ) -> List[Dict]:
        """
        Perform search from a single point for multiple keywords
        
        Args:
            lat (float): Search center latitude
            lng (float): Search center longitude
            radius_km (float): Search radius in kilometers
            keywords (List[str]): List of search keywords
            delay_between_requests (float): Delay between API requests in seconds
            extract_emails (bool): Whether to extract emails from websites
            
        Returns:
            List[Dict]: Combined search results from all keywords
        """
        all_results = []
        seen_place_ids = set()
        
        print(f"Starting single-point search for {len(keywords)} keywords")
        
        for i, keyword in enumerate(keywords):
            print(f"Searching keyword {i+1}/{len(keywords)}: '{keyword}'")
            
            try:
                results = self.api_client.nearby_search(
                    lat=lat,
                    lng=lng,
                    radius_km=radius_km,
                    keyword=keyword
                )
                
                # Filter out duplicates
                for result in results:
                    place_id = result.get('place_id')
                    if place_id not in seen_place_ids:
                        all_results.append(result)
                        seen_place_ids.add(place_id)
                
                print(f"  Found {len(results)} results, {len(all_results)} total unique results")
                
            except Exception as e:
                print(f"  Error searching keyword '{keyword}': {e}")
            
            # Add delay between requests
            if delay_between_requests > 0 and i < len(keywords) - 1:
                time.sleep(delay_between_requests)
        
        # Enrich results with detailed information including websites
        print("Enriching results with detailed information...")
        all_results = self.api_client.enrich_places_with_details(all_results)
        
        # Extract emails if requested
        if extract_emails:
            print("Extracting emails from websites...")
            all_results = self._extract_emails_for_places(all_results)
        
        # Sort results by distance
        all_results.sort(key=lambda x: x.get('distance', float('inf')))
        
        print(f"Single-point search completed: {len(all_results)} unique results found")
        return all_results
    
    def _extract_emails_for_places(self, places: List[Dict]) -> List[Dict]:
        """
        Extract emails from websites for all places
        
        Args:
            places (List[Dict]): List of places with website information
            
        Returns:
            List[Dict]: Places with extracted email information
        """
        total_places = len(places)
        places_with_websites = [p for p in places if p.get('website')]
        
        print(f"Found {len(places_with_websites)} places with websites out of {total_places} total places")
        
        for i, place in enumerate(places):
            website = place.get('website')
            if website:
                try:
                    print(f"Extracting emails from {place.get('name', 'Unknown')} ({i+1}/{total_places})")
                    emails = self.email_extractor.extract_emails_from_website(website)
                    place['emails'] = emails
                    
                    if emails:
                        print(f"  Found emails: {', '.join(emails)}")
                    else:
                        print(f"  No emails found")
                        
                except Exception as e:
                    print(f"  Error extracting emails: {e}")
                    place['emails'] = []
            else:
                place['emails'] = []
        
        return places 