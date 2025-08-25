import json
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionCarShopping(Action):
    """
    Rasa Custom Action to check if a dealer sells the car the user is looking for.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_car_shopping"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Executes the action to calculate financing options and set relevant slots.
        """
        recommended_car_details = tracker.get_slot("recommended_car_details")

        # If there are no recommended cars, return no events
        if not recommended_car_details or not isinstance(recommended_car_details, dict):
            return []

        found_dealer = False

        for car_info in recommended_car_details.values():
            api_result = self._check_car(car_info)
            if api_result.get("available", False):
                found_dealer = True
                break

        if not found_dealer:
            return []

        # Set slots based on API result
        return [
            SlotSet("dealer_found", api_result.get("available", False)),
            SlotSet("dealer_name", api_result.get("dealer_name")),
            SlotSet("car_model", api_result.get("car_model")),
            SlotSet("car_price", api_result.get("price")),
        ]

    def _check_car(self, car_info: dict[str, Any]) -> dict[str, Any]:
        # Extract car details
        car_model = car_info.get("model")

        car_price = None
        car_price_min = None
        car_price_max = None

        # Try to extract price or price range
        price_range_str = car_info.get("price_range")
        if price_range_str:
            # Try to parse price range like "under 50000", "25000-30000", etc.
            if "under" in price_range_str:
                try:
                    car_price_max = float(price_range_str.replace("under", "").strip())
                except Exception:
                    car_price_max = None
            if "up to" in price_range_str:
                try:
                    car_price_max = float(price_range_str.replace("up to", "").strip())
                except Exception:
                    car_price_max = None
            elif "-" in price_range_str:
                try:
                    min_str, max_str = price_range_str.split("-", 1)
                    car_price_min = float(min_str.strip())
                    car_price_max = float(max_str.strip())
                except Exception:
                    car_price_min = None
                    car_price_max = None
            else:
                # Try to parse as a single price
                try:
                    car_price = float(price_range_str.strip())
                except Exception:
                    car_price = None

        # Prepare price and price_range for the API
        price = None
        price_range = None
        try:
            if car_price is not None:
                price = float(car_price)
        except (ValueError, TypeError):
            price = None

        try:
            if car_price_min is not None and car_price_max is not None:
                price_range = (float(car_price_min), float(car_price_max))
        except (ValueError, TypeError):
            price_range = None

        # Import the MockDealerAPI here to avoid circular import issues
        from actions.shopping import MockDealerAPI

        # Call the MockDealerAPI to check car availability
        dealer_api = MockDealerAPI()
        return dealer_api.check_car_availability(
            car_model=car_model, price=price, price_range=price_range
        )
