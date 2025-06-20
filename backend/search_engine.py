"""
Grid-based search engine for location searches
"""

import time
from typing import List, Dict, Set, Any, Optional, Callable
from .config import Config
from .grid_calculator import GridCalculator
from .places_api import PlacesAPIClient
from .email_extractor import EmailExtractor


class GridSearchEngine:
    """Main search engine that performs grid-based location searches with progress tracking"""
    
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
        extract_emails: bool = False,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """
        Perform grid-based search for multiple keywords with progress tracking
        
        Args:
            center_lat (float): Center latitude
            center_lng (float): Center longitude
            radius_km (float): Search radius in kilometers
            keywords (List[str]): List of search keywords
            grid_size (int): Grid size (NxN)
            delay_between_requests (float): Delay between API requests in seconds
            extract_emails (bool): Whether to extract emails from websites
            progress_callback (Callable[[float, str], None]): Progress update callback
            
        Returns:
            List[Dict]: Combined search results from all grid cells and keywords
        """
        all_results = []
        seen_place_ids = set()
        
        try:
            # Step 1: Calculate grid points (2% of progress)
            if progress_callback:
                progress_callback(0.02, "격자 포인트 계산 중...")
            
            grid_points = self.grid_calculator.calculate_grid_points(
                center_lat, center_lng, radius_km, grid_size
            )
            
            total_searches = len(grid_points) * len(keywords)
            current_search = 0
            
            print(f"Starting grid search: {len(grid_points)} grid points × {len(keywords)} keywords = {total_searches} total searches")
            
            # Step 2: Perform grid searches (60% of progress)
            search_start_progress = 0.02
            search_end_progress = 0.62
            search_progress_span = search_end_progress - search_start_progress
            
            for grid_idx, (grid_lat, grid_lng, grid_radius) in enumerate(grid_points):
                for keyword_idx, keyword in enumerate(keywords):
                    current_search += 1
                    
                    # Update progress
                    search_progress = search_start_progress + (current_search / total_searches) * search_progress_span
                    if progress_callback:
                        progress_callback(
                            search_progress, 
                            f"검색 중... ({current_search}/{total_searches}) 격자 {grid_idx+1}/{len(grid_points)}, 키워드: '{keyword}'"
                        )
                    
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
                                result['search_keyword'] = keyword
                                all_results.append(result)
                                seen_place_ids.add(place_id)
                        
                        print(f"  Found {len(results)} results, {len(all_results)} total unique results so far")
                        
                    except Exception as e:
                        print(f"  Error in search: {e}")
                    
                    # Add delay between requests to avoid rate limiting
                    if delay_between_requests > 0:
                        time.sleep(delay_between_requests)
            
            # Step 3: Enrich with detailed information (30% of progress)
            detail_start_progress = 0.62
            detail_end_progress = 0.92
            detail_progress_span = detail_end_progress - detail_start_progress
            
            if progress_callback:
                progress_callback(0.62, "장소 상세 정보 수집 중...")
            
            print("Enriching results with detailed information...")
            
            for idx, place in enumerate(all_results):
                # Update progress
                detail_progress = detail_start_progress + (idx / len(all_results)) * detail_progress_span
                if progress_callback:
                    progress_callback(
                        detail_progress, 
                        f"상세 정보 수집 중... ({idx+1}/{len(all_results)}) {place.get('name', 'Unknown')}"
                    )
                
                # This will be handled by enrich_places_with_details method
                pass
            
            all_results = self.api_client.enrich_places_with_details(all_results)
            
            # Step 4: Extract emails if requested (8% of progress)
            if extract_emails:
                email_start_progress = 0.92
                email_end_progress = 1.0
                email_progress_span = email_end_progress - email_start_progress
                
                places_with_websites = [place for place in all_results if place.get('website')]
                
                if places_with_websites:
                    print("Extracting emails from websites...")
                    
                    for idx, place in enumerate(places_with_websites):
                        # Update progress
                        email_progress = email_start_progress + (idx / len(places_with_websites)) * email_progress_span
                        if progress_callback:
                            progress_callback(
                                email_progress, 
                                f"이메일 추출 중... ({idx+1}/{len(places_with_websites)}) {place.get('name', 'Unknown')}"
                            )
                        
                        # Extract emails for this place
                        try:
                            website = place.get('website')
                            if website:
                                emails = self.email_extractor.extract_emails_from_website(website)
                                place['emails'] = emails
                                place['has_email'] = len(emails) > 0
                            
                            # Small delay between website crawling
                            time.sleep(0.2)
                            
                        except Exception as e:
                            print(f"Error extracting emails from {place.get('name', 'Unknown')}: {e}")
                            place['emails'] = []
                            place['has_email'] = False
                            continue
                
                # Ensure all places have email fields
                for place in all_results:
                    if 'emails' not in place:
                        place['emails'] = []
                    if 'has_email' not in place:
                        place['has_email'] = False
            
            # Sort results by distance from center
            all_results.sort(key=lambda x: x.get('distance_from_center', float('inf')))
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0, f"검색 완료! 총 {len(all_results)}개 결과 발견")
            
            print(f"Grid search completed: {len(all_results)} unique results found")
            return all_results
            
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"오류 발생: {str(e)}")
            raise e
    
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
                        result['search_keyword'] = keyword
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
        Extract emails for places that have websites
        
        Args:
            places (List[Dict]): List of places
            
        Returns:
            List[Dict]: Places with email information added
        """
        for place in places:
            website = place.get('website')
            if website:
                try:
                    emails = self.email_extractor.extract_emails_from_website(website)
                    place['emails'] = emails
                    place['has_email'] = len(emails) > 0
                    
                    # Add delay between website crawling to be respectful
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"Error extracting emails from {place.get('name', 'Unknown')}: {e}")
                    place['emails'] = []
                    place['has_email'] = False
            else:
                place['emails'] = []
                place['has_email'] = False
        
        return places 

    def get_search_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get search statistics
        
        Args:
            results (List[Dict[str, Any]]): Search results
            
        Returns:
            Dict[str, Any]: Statistics
        """
        if not results:
            return {
                'total_places': 0,
                'places_with_emails': 0,
                'total_emails': 0,
                'keywords_distribution': {},
                'rating_distribution': {}
            }
        
        # Basic stats
        total_places = len(results)
        places_with_emails = sum(1 for place in results if place.get('has_email', False))
        total_emails = sum(len(place.get('emails', [])) for place in results)
        
        # Keyword distribution
        keywords_dist = {}
        for place in results:
            keyword = place.get('search_keyword', 'Unknown')
            keywords_dist[keyword] = keywords_dist.get(keyword, 0) + 1
        
        # Rating distribution
        rating_dist = {'5': 0, '4-5': 0, '3-4': 0, '2-3': 0, '1-2': 0, 'No rating': 0}
        for place in results:
            rating = place.get('rating')
            if rating is None:
                rating_dist['No rating'] += 1
            elif rating >= 5.0:
                rating_dist['5'] += 1
            elif rating >= 4.0:
                rating_dist['4-5'] += 1
            elif rating >= 3.0:
                rating_dist['3-4'] += 1
            elif rating >= 2.0:
                rating_dist['2-3'] += 1
            else:
                rating_dist['1-2'] += 1
        
        return {
            'total_places': total_places,
            'places_with_emails': places_with_emails,
            'total_emails': total_emails,
            'email_success_rate': (places_with_emails / total_places * 100) if total_places > 0 else 0,
            'keywords_distribution': keywords_dist,
            'rating_distribution': rating_dist
        } 