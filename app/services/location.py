import requests
import logging
import math
from typing import Optional, Dict, List, Tuple
from ..models import Issue

logger = logging.getLogger(__name__)

class LocationService:
    """Service for location-based operations and geocoding"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.geocoding_base_url = "https://api.opencagedata.com/geocode/v1/json"
        self.reverse_geocoding_base_url = "https://api.opencagedata.com/geocode/v1/json"
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Convert address to coordinates"""
        try:
            if not self.api_key:
                logger.warning("No API key provided for geocoding")
                return None
            
            params = {
                'q': address,
                'key': self.api_key,
                'limit': 1
            }
            
            response = requests.get(self.geocoding_base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('results'):
                result = data['results'][0]
                return {
                    'latitude': result['geometry']['lat'],
                    'longitude': result['geometry']['lng'],
                    'formatted_address': result['formatted'],
                    'components': result.get('components', {})
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {str(e)}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Convert coordinates to address"""
        try:
            if not self.api_key:
                logger.warning("No API key provided for reverse geocoding")
                return None
            
            params = {
                'q': f"{latitude},{longitude}",
                'key': self.api_key,
                'limit': 1
            }
            
            response = requests.get(self.reverse_geocoding_base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('results'):
                result = data['results'][0]
                return {
                    'formatted_address': result['formatted'],
                    'components': result.get('components', {})
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error reverse geocoding coordinates ({latitude}, {longitude}): {str(e)}")
            return None
    
    def calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers using Haversine formula"""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def find_nearby_issues(
        self, 
        issues: List[Issue], 
        center_lat: float, 
        center_lon: float, 
        radius_km: float = 5.0
    ) -> List[Tuple[Issue, float]]:
        """Find issues within a specified radius of given coordinates"""
        nearby_issues = []
        
        for issue in issues:
            distance = self.calculate_distance(
                center_lat, center_lon, 
                issue.latitude, issue.longitude
            )
            
            if distance <= radius_km:
                nearby_issues.append((issue, distance))
        
        # Sort by distance
        return sorted(nearby_issues, key=lambda x: x[1])
    
    def get_location_bounds(self, issues: List[Issue]) -> Optional[Dict]:
        """Get bounding box for a list of issues"""
        if not issues:
            return None
        
        lats = [issue.latitude for issue in issues]
        lons = [issue.longitude for issue in issues]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons),
            'center_lat': sum(lats) / len(lats),
            'center_lon': sum(lons) / len(lons)
        }
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate if coordinates are within reasonable bounds"""
        return (
            -90 <= latitude <= 90 and 
            -180 <= longitude <= 180
        )
    
    def get_location_metadata(self, latitude: float, longitude: float) -> Dict:
        """Get additional metadata about a location"""
        metadata = {
            'coordinates_valid': self.validate_coordinates(latitude, longitude),
            'latitude': latitude,
            'longitude': longitude
        }
        
        # Try to get address information
        if self.api_key:
            geocoded = self.reverse_geocode(latitude, longitude)
            if geocoded:
                metadata.update({
                    'address': geocoded.get('formatted_address'),
                    'components': geocoded.get('components', {})
                })
        
        return metadata
    
    def cluster_issues(self, issues: List[Issue], cluster_radius_km: float = 1.0) -> List[List[Issue]]:
        """Group nearby issues into clusters"""
        if not issues:
            return []
        
        clusters = []
        processed = set()
        
        for i, issue in enumerate(issues):
            if i in processed:
                continue
            
            cluster = [issue]
            processed.add(i)
            
            # Find all issues within cluster radius
            for j, other_issue in enumerate(issues[i+1:], i+1):
                if j in processed:
                    continue
                
                distance = self.calculate_distance(
                    issue.latitude, issue.longitude,
                    other_issue.latitude, other_issue.longitude
                )
                
                if distance <= cluster_radius_km:
                    cluster.append(other_issue)
                    processed.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def get_issue_density_map(
        self, 
        issues: List[Issue], 
        grid_size_km: float = 0.5
    ) -> Dict:
        """Create a density map of issues"""
        if not issues:
            return {'grid': [], 'bounds': None}
        
        bounds = self.get_location_bounds(issues)
        if not bounds:
            return {'grid': [], 'bounds': None}
        
        # Create grid
        lat_step = grid_size_km / 111.0  # Rough conversion from km to degrees
        lon_step = grid_size_km / (111.0 * abs(math.cos(math.radians(bounds['center_lat']))))
        
        grid = []
        lat = bounds['min_lat']
        
        while lat <= bounds['max_lat']:
            lon = bounds['min_lon']
            row = []
            
            while lon <= bounds['max_lon']:
                # Count issues in this grid cell
                count = 0
                for issue in issues:
                    if (abs(issue.latitude - lat) <= lat_step/2 and 
                        abs(issue.longitude - lon) <= lon_step/2):
                        count += 1
                
                row.append({
                    'lat': lat,
                    'lon': lon,
                    'count': count
                })
                
                lon += lon_step
            
            grid.append(row)
            lat += lat_step
        
        return {
            'grid': grid,
            'bounds': bounds,
            'grid_size_km': grid_size_km
        }
