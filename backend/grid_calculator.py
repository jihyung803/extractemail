"""
Grid calculation utilities for dividing search area into smaller grids
"""

import math
from typing import List, Tuple


class GridCalculator:
    """Calculate grid points for dividing search area"""
    
    def __init__(self, earth_radius_km: float = 6371.0):
        """
        Initialize grid calculator
        
        Args:
            earth_radius_km (float): Earth radius in kilometers
        """
        self.earth_radius_km = earth_radius_km
    
    def calculate_grid_points(
        self, 
        center_lat: float, 
        center_lng: float, 
        radius_km: float, 
        grid_size: int
    ) -> List[Tuple[float, float, float]]:
        """
        Calculate grid center points within the search radius
        
        Args:
            center_lat (float): Center latitude
            center_lng (float): Center longitude
            radius_km (float): Search radius in kilometers
            grid_size (int): Grid size (NxN)
            
        Returns:
            List[Tuple[float, float, float]]: List of (lat, lng, grid_radius) tuples
        """
        grid_points = []
        
        # Calculate grid cell size
        grid_radius = radius_km / grid_size
        
        # Convert radius to degrees (approximate)
        lat_degree_km = 111.0  # 1 degree latitude ≈ 111 km
        lng_degree_km = lat_degree_km * math.cos(math.radians(center_lat))
        
        radius_lat = radius_km / lat_degree_km
        radius_lng = radius_km / lng_degree_km
        
        # Calculate step size for grid
        step_lat = (2 * radius_lat) / grid_size
        step_lng = (2 * radius_lng) / grid_size
        
        # Calculate grid points
        for i in range(grid_size):
            for j in range(grid_size):
                # Calculate grid center point
                grid_lat = center_lat - radius_lat + (i + 0.5) * step_lat
                grid_lng = center_lng - radius_lng + (j + 0.5) * step_lng
                
                # Check if grid center is within the search radius
                distance = self.calculate_distance(center_lat, center_lng, grid_lat, grid_lng)
                
                if distance <= radius_km:
                    grid_points.append((grid_lat, grid_lng, grid_radius))
        
        return grid_points
    
    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lng1: First point coordinates
            lat2, lng2: Second point coordinates
            
        Returns:
            float: Distance in kilometers
        """
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
        
        return self.earth_radius_km * c 