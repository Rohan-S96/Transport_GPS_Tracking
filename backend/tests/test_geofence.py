"""
Unit tests for Geofence spatial calculations.
"""
from app.utils.geo_utils import is_point_in_circle, is_point_in_polygon

def test_point_in_circle():
    center_lat, center_lng = 19.0000, 72.8500
    radius_meters = 1000.0

    # Inside point (approx ~100m away)
    assert is_point_in_circle(19.0005, 72.8505, center_lat, center_lng, radius_meters) is True
    # Outside point (approx ~15km away)
    assert is_point_in_circle(19.1500, 72.9500, center_lat, center_lng, radius_meters) is False


def test_point_in_polygon():
    # Square polygon
    square = [
        [10.0, 10.0],
        [10.0, 20.0],
        [20.0, 20.0],
        [20.0, 10.0],
        [10.0, 10.0]
    ]
    # Inside point
    assert is_point_in_polygon(15.0, 15.0, square) is True
    # Outside point
    assert is_point_in_polygon(25.0, 25.0, square) is False
