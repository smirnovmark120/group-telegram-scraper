from geopy.distance import geodesic  # Assuming geopy is available for distance calculation
from timer_meta import TimerMeta

class GeoDataFilter(metaclass=TimerMeta):
    def __init__(self, data, importance_threshold=0.4):
        self.data = data
        self.importance_threshold = importance_threshold
        # Expanded geographical bounds to include Israel and surrounding areas (West Bank, Gaza)
        self.israel_bounds = {
            "min_lat": 29.3,
            "max_lat": 33.5,
            "min_lon": 34.0,
            "max_lon": 36.0
        }

    def is_within_israel(self, lat, lon):
        """
        Check if the coordinates are within the general bounds of Israel and nearby regions.
        """
        if lat is None or lon is None:
            return False
        return (self.israel_bounds["min_lat"] <= lat <= self.israel_bounds["max_lat"] and
                self.israel_bounds["min_lon"] <= lon <= self.israel_bounds["max_lon"])

    def calculate_avg_distance(self, coordinates):
        """
        Calculate the average distance (in kilometers) between all points in the coordinates list.
        Uses geopy to calculate geodesic distance between two points (lat, lon).
        """
        if len(coordinates) < 2:
            return 0  # If there's less than 2 points, return 0 as avg distance

        total_distance = 0
        count = 0

        # Compare every pair of points
        for i, coord1 in enumerate(coordinates):
            for coord2 in coordinates[i + 1:]:
                total_distance += geodesic(coord1, coord2).kilometers
                count += 1

        # Calculate average distance
        return total_distance / count if count else 0

    def filter_by_importance_and_location(self):
        """
        Filter results by location (inside Israel or nearby) and importance (above a threshold).
        Returns a sorted list of valid results.
        """
        valid_results = []
        
        # Filter OpenCage, Nominatim, and LocationIQ data
        for service in ['OpenCage', 'Nominatim', 'LocationIQ']:
            if service not in self.data:
                continue

            # Iterate over each result within the service
            for result in self.data[service]:
                lat = result.get("lat")
                lon = result.get("lon")
                importance = result.get("importance", 0)  # Default to 0 if not provided
                wikidata_aliases = result.get("wikidata_aliases", [])  # Extract wikidata_aliases if available

                # Extract name based on available fields
                if service == 'OpenCage':
                    name = (result.get("components", {}).get("city") or
                            result.get("components", {}).get("town") or
                            result.get("components", {}).get("village") or
                            result.get("components", {}).get("_normalized_city") or
                            result.get("components", {}).get("state") or
                            result.get("components", {}).get("country") or
                            result.get("formatted", "Unknown"))
                else:
                    name = result.get("display_name", "Unknown")

                # Convert lat/lon to float if they're strings
                try:
                    lat = float(lat) if lat else None
                    lon = float(lon) if lon else None
                    importance = float(importance) if importance else 0
                except ValueError:
                    lat, lon, importance = None, None, 0

                # Check if the result is within Israel and meets the importance threshold
                if self.is_within_israel(lat, lon) and importance >= self.importance_threshold:
                    valid_results.append({
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "importance": importance,
                        "service": service,  # Add service provider information
                        "wikidata_aliases": wikidata_aliases  # Include all wikidata_aliases
                    })

        # Sort results by importance in descending order
        return sorted(valid_results, key=lambda x: x['importance'], reverse=True)

    def get_highest_importance_per_service(self):
        """
        Get the highest importance result per service.
        """
        highest_importance_results = {}
        
        for result in self.filter_by_importance_and_location():
            service = result['service']
            if service not in highest_importance_results:
                highest_importance_results[service] = result
            elif result['importance'] > highest_importance_results[service]['importance']:
                highest_importance_results[service] = result

        return list(highest_importance_results.values())

    def get_coordinates_with_names(self):
        """
        Return the best result based on average distance and importance:
        1. If the average distance between the highest importance points per service is less than 5 km, 
           return the OpenCage result with the highest importance.
        2. Otherwise, return the result with the highest importance overall.
        """
        # Get the highest importance point per service
        highest_importance_results = self.get_highest_importance_per_service()

        if not highest_importance_results:
            return None  # No valid results found

        # Calculate average distance between all the highest importance points
        coordinates = [(result["lat"], result["lon"]) for result in highest_importance_results if result["lat"] and result["lon"]]
        avg_distance = self.calculate_avg_distance(coordinates)

        # Rule 1: If average distance is below 5 km, return the OpenCage result with the highest importance
        if avg_distance < 5:
            open_cage_results = [result for result in highest_importance_results if result["service"] == "OpenCage"]
            if open_cage_results:
                # Return the OpenCage result with the highest importance
                best_open_cage = max(open_cage_results, key=lambda x: x["importance"])
                return {
                    "service": best_open_cage["service"],
                    "name": best_open_cage["name"],
                    "lat": best_open_cage["lat"],
                    "lon": best_open_cage["lon"],
                    "wikidata_aliases": best_open_cage["wikidata_aliases"],
                    "importance": best_open_cage["importance"]
                }

        # Rule 2: Otherwise, return the result with the highest importance across all services
        best_result = max(highest_importance_results, key=lambda x: x["importance"])

        return {
            "service": best_result["service"],
            "name": best_result["name"],
            "lat": best_result["lat"],
            "lon": best_result["lon"],
            "wikidata_aliases": best_result["wikidata_aliases"],
            "importance": best_result["importance"]
        } or None  # Return None if no results