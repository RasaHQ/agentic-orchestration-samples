import json
import os  # Import os module to handle file paths


class MockCarSearchAPI:
    """
    A mock API server for car search, simulating a 3rd party service.
    It now reads car data from a JSON file and filters based on query.
    """

    def __init__(self, data_file="cars.json"):
        """
        Initializes the API by loading car data from the specified JSON file.

        Args:
            data_file (str): The path to the JSON file containing car data.
        """
        self.cars_data = self._load_car_data(data_file)

    def _load_car_data(self, data_file):
        """
        Loads car data from a JSON file.
        """
        # Ensure the file exists in the current working directory or specify full path
        file_path = os.path.join(os.getcwd(), data_file)
        if not os.path.exists(file_path):
            print(
                f"Error: Car data file not found at {file_path}. Please ensure '{data_file}' is in the same directory."
            )
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_availability(
        self,
        model_name: str,
        dealer_name: str = None,
        new_or_used: str = None,
        car_type: str = None,
    ):
        """
        Check if a specific car model is available at a specific dealer.

        Args:
            model_name (str): Specific model name to search for (e.g., "Tucson", "CR-V").
            dealer_name (str, optional): Specific dealer name to check.
            new_or_used (str, optional): Whether the car is "new" or "used".
            car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV").

        Returns:
            str: A JSON string containing availability results.
        """
        print(
            f"DEBUG: Check availability called with: model='{model_name}', dealer='{dealer_name}', new_or_used='{new_or_used}', type='{car_type}'"
        )

        matching_cars = []
        for car in self.cars_data:
            matches = True

            # Check model name (partial matching for flexibility)
            car_model_lower = car["model"].lower()
            if model_name.lower() not in car_model_lower:
                matches = False

            # Check dealer name if specified
            if dealer_name and matches:
                dealer_lower = car["dealer_location"].lower()
                if dealer_name.lower() not in dealer_lower:
                    matches = False

            # Check new_or_used if specified
            if new_or_used and matches:
                new_or_used_lower = car["new_or_used"].lower()
                if new_or_used.lower() != new_or_used_lower:
                    matches = False

            # Check car type if specified
            if car_type and matches:
                car_type_lower = car["type"].lower()
                if car_type.lower() not in car_type_lower:
                    matches = False

            if matches:
                matching_cars.append(car)

        if matching_cars:
            # Return all matching cars
            response_data = {
                "available": True,
                "cars": [
                    {
                        "model": car["model"],
                        "price": car["price"],
                        "dealer_location": car["dealer_location"],
                        "new_or_used": car["new_or_used"],
                        "type": car["type"],
                        "features": car.get("features", []),
                    }
                    for car in matching_cars
                ],
                "count": len(matching_cars),
            }
            return json.dumps(response_data)
        else:
            return json.dumps({
                "available": False,
                "message": f"No {model_name} found matching your criteria.",
                "cars": [],
                "count": 0,
            })

    def find_similar_cars(
        self,
        model_name: str,
        dealer_name: str = None,
        new_or_used: str = None,
        car_type: str = None,
    ):
        """
        Find similar cars at a specific dealer when the requested model is not available.

        Args:
            model_name (str): The original model name that was requested.
            dealer_name (str, optional): Specific dealer name to search at.
            new_or_used (str, optional): Whether the car is "new" or "used".
            car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV").

        Returns:
            str: A JSON string containing similar car recommendations.
        """
        print(
            f"DEBUG: Find similar cars called with: model='{model_name}', dealer='{dealer_name}', new_or_used='{new_or_used}', type='{car_type}'"
        )

        # First, try to determine the car type from the model name if not provided
        if not car_type:
            for car in self.cars_data:
                if model_name.lower() in car["model"].lower():
                    car_type = car["type"]
                    break

        similar_cars = []
        for car in self.cars_data:
            # Skip the exact model
            if model_name.lower() in car["model"].lower():
                continue

            matches = True

            # Check dealer name if specified
            if dealer_name:
                dealer_lower = car["dealer_location"].lower()
                if dealer_name.lower() not in dealer_lower:
                    matches = False

            # Check new_or_used if specified
            if new_or_used and matches:
                new_or_used_lower = car["new_or_used"].lower()
                if new_or_used.lower() != new_or_used_lower:
                    matches = False

            # Check car type if specified
            if car_type and matches:
                car_type_lower = car["type"].lower()
                if car_type.lower() not in car_type_lower:
                    matches = False

            if matches:
                similar_cars.append(car)

        # Sort by price to show most relevant options first
        similar_cars.sort(key=lambda x: x["price"])

        if similar_cars:
            response_data = {
                "similar_cars_available": True,
                "cars": [
                    {
                        "model": car["model"],
                        "price": car["price"],
                        "dealer_location": car["dealer_location"],
                        "new_or_used": car["new_or_used"],
                        "type": car["type"],
                        "features": car.get("features", []),
                    }
                    for car in similar_cars[:5]  # Limit to top 5 similar cars
                ],
                "count": len(similar_cars[:5]),
            }
            return json.dumps(response_data)
        else:
            return json.dumps({
                "similar_cars_available": False,
                "message": f"No similar cars found at the specified dealer.",
                "cars": [],
                "count": 0,
            })

    def get_dealer_recommendations(
        self,
        model_name: str,
        new_or_used: str = None,
        car_type: str = None,
    ):
        """
        Get dealer recommendations for a specific car model.

        Args:
            model_name (str): Specific model name to search for.
            new_or_used (str, optional): Whether the car is "new" or "used".
            car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV").

        Returns:
            str: A JSON string containing dealer recommendations.
        """
        print(
            f"DEBUG: Get dealer recommendations called with: model='{model_name}', new_or_used='{new_or_used}', type='{car_type}'"
        )

        matching_cars = []
        for car in self.cars_data:
            matches = True

            # Check model name (partial matching for flexibility)
            car_model_lower = car["model"].lower()
            if model_name.lower() not in car_model_lower:
                matches = False

            # Check new_or_used if specified
            if new_or_used and matches:
                new_or_used_lower = car["new_or_used"].lower()
                if new_or_used.lower() != new_or_used_lower:
                    matches = False

            # Check car type if specified
            if car_type and matches:
                car_type_lower = car["type"].lower()
                if car_type.lower() not in car_type_lower:
                    matches = False

            if matches:
                matching_cars.append(car)

        if matching_cars:
            # Group by dealer and get the best price for each dealer
            dealer_prices = {}
            for car in matching_cars:
                dealer = car["dealer_location"]
                if dealer not in dealer_prices or car["price"] < dealer_prices[dealer]["price"]:
                    dealer_prices[dealer] = {
                        "model": car["model"],
                        "price": car["price"],
                        "new_or_used": car["new_or_used"],
                        "type": car["type"],
                        "features": car.get("features", []),
                    }

            # Sort dealers by price
            sorted_dealers = sorted(dealer_prices.items(), key=lambda x: x[1]["price"])

            response_data = {
                "dealers_available": True,
                "dealers": [
                    {
                        "dealer_name": dealer,
                        "model": car_data["model"],
                        "price": car_data["price"],
                        "new_or_used": car_data["new_or_used"],
                        "type": car_data["type"],
                        "features": car_data["features"],
                    }
                    for dealer, car_data in sorted_dealers
                ],
                "count": len(sorted_dealers),
            }
            return json.dumps(response_data)
        else:
            return json.dumps({
                "dealers_available": False,
                "message": f"No dealers found with {model_name}.",
                "dealers": [],
                "count": 0,
            })

