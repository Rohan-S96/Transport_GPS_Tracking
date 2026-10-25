"""
Geodetic calculation utilities (Haversine distance, bearing, point containment).
"""
import math

EARTH_RADIUS_KM = 6371.0

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the Earth's surface
    using the Haversine formula.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters."""
    return haversine_distance_km(lat1, lon1, lat2, lon2) * 1000.0


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate compass bearing from point 1 to point 2 (0 - 360 degrees).
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)

    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    initial_bearing = math.atan2(y, x)
    initial_bearing_deg = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing_deg + 360.0) % 360.0
    return compass_bearing


def is_point_in_circle(point_lat: float, point_lon: float, center_lat: float, center_lon: float, radius_meters: float) -> bool:
    """Check if a coordinate lies within a circular perimeter."""
    dist_m = haversine_distance_meters(point_lat, point_lon, center_lat, center_lon)
    return dist_m <= radius_meters


def is_point_in_polygon(point_lat: float, point_lon: float, polygon_coords: list) -> bool:
    """
    Ray-casting algorithm to determine if a point [lat, lon] is inside a polygon.
    polygon_coords is a list of [lat, lon] or (lat, lon) vertices.
    """
    if not polygon_coords or len(polygon_coords) < 3:
        return False

    inside = False
    n = len(polygon_coords)
    p1_lat, p1_lon = polygon_coords[0][0], polygon_coords[0][1]

    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon_coords[i % n][0], polygon_coords[i % n][1]
        
        if point_lon > min(p1_lon, p2_lon):
            if point_lon <= max(p1_lon, p2_lon):
                if point_lat <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        lat_inters = (point_lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    if p1_lat == p2_lat or point_lat <= lat_inters:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon

    return inside
