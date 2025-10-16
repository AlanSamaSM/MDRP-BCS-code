# Coordinate transformation helpers

# Range of x/y in MDRP public dataset
X_MIN, X_MAX = 0, 35124
Y_MIN, Y_MAX = 0, 54766

# Default bounding box around La Paz, B.C.S. (approx 10km x 10km)
LAT_MIN, LAT_MAX = 24.0976, 24.1876
LON_MIN, LON_MAX = -110.3624, -110.2636


def xy_to_latlon(x, y,
                 lat_min=LAT_MIN, lat_max=LAT_MAX,
                 lon_min=LON_MIN, lon_max=LON_MAX,
                 x_min=X_MIN, x_max=X_MAX,
                 y_min=Y_MIN, y_max=Y_MAX):
    """Affine transform from synthetic dataset coordinates to lat/lon."""
    lon = lon_min + (x - x_min) / (x_max - x_min) * (lon_max - lon_min)
    lat = lat_min + (y - y_min) / (y_max - y_min) * (lat_max - lat_min)
    return lat, lon
