
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.getrouteOSMR import get_route_details

def test_osrm_connection():
    """
    Tests the connection to the OSRM routing service.
    """
    start_coords = (19.4360, -99.1320)  # Example start coordinates (lat, lon)
    waypoints = [(19.4370, -99.1310)]    # Example waypoint coordinates (lat, lon)

    print("Testing OSRM connection...")
    print(f"Start coordinates: {start_coords}")
    print(f"Waypoints: {waypoints}")

    route_details = get_route_details(start_coords, waypoints)

    if route_details:
        print("\nOSRM connection successful!")
        print("Route details:")
        # Print some key details from the response
        print(f"  Duration: {route_details.get('duration')} seconds")
        print(f"  Distance: {route_details.get('distance')} meters")
    else:
        print("\nFailed to get route details from OSRM.")
        print("This could be due to a network issue, a timeout, or the OSRM service being unavailable.")

if __name__ == "__main__":
    test_osrm_connection()
