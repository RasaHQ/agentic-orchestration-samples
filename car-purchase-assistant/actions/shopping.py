import random
from typing import Any


class MockDealerAPI:
    """
    A mock API to check if a specific car is available at any dealer.
    Randomly decides availability and generates dealer names and prices.
    """

    DEALER_NAMES = [
        "Auto Galaxy",
        "Prime Motors",
        "Cityline Cars",
        "Sunset Auto Mall",
        "Metro Car Center",
        "Greenlight Dealership",
        "Starline Autos",
        "Urban Wheels",
        "Prestige Motors",
        "Highway Auto Plaza",
    ]

    def check_car_availability(
        self,
        car_model: str,
        price: float = None,
        price_range: tuple[float, float] = None,
    ) -> dict[str, Any]:
        """
        Simulates checking if a car is available at a dealer.

        Args:
            car_model (str): The model of the car.
            price (float, optional): A target price for the car.
            price_range (tuple, optional): A (min_price, max_price) tuple.

        Returns:
            dict: {
                "available": bool,
                "dealer_name": str or None,
                "price": float or None
            }
        """
        is_available = random.choices([True, False], weights=[0.6, 0.4])[0]
        if is_available:
            dealer_name = random.choice(self.DEALER_NAMES)
            car_price = self._determine_price(price, price_range)
        else:
            dealer_name = None
            car_price = None

        return {
            "available": is_available,
            "dealer_name": dealer_name,
            "price": car_price,
        }

    def _determine_price(
        self, price: float | None, price_range: tuple[float, float] | None
    ):
        """
        Determines the price of a car based on the provided price or price range.
        """
        # Determine price
        if (
            price_range is not None
            and isinstance(price_range, tuple)
            and len(price_range) == 2
        ):
            min_price, max_price = price_range
            # Add a little randomness within the range, but bias toward the middle
            base_price = (min_price + max_price) / 2
            spread = (max_price - min_price) / 4
            car_price = round(
                random.uniform(base_price - spread, base_price + spread), 2
            )
            car_price = max(min_price, min(car_price, max_price))
        elif price is not None:
            # Add a small random variation (+/- 5%)
            variation = price * 0.05
            car_price = round(random.uniform(price - variation, price + variation), 2)
            car_price = max(0, car_price)
        else:
            # Default to a random price in a typical car price range
            car_price = round(random.uniform(18000, 45000), 2)

        return car_price
