import json
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


from actions.financing import MockFinancingAPI


class ActionProvideFinancingOptions(Action):
    """
    Rasa Custom Action to calculate and set financing options for a car purchase.
    It leverages the MockFinancingAPI and the bank's internal savings knowledge.
    Instead of directly sending messages, it sets slots with the calculated details.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_provide_financing_options"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Executes the action to calculate financing options and set relevant slots.
        """
        # Retrieve necessary slot values from the tracker
        # 'car_price' should be set by the car selection bot before this action runs.
        # 'loan_term' and 'down_payment_amount' are collected from the user.
        car_price = tracker.get_slot("car_price")
        loan_term = tracker.get_slot("loan_term")
        down_payment_amount = tracker.get_slot("down_payment_amount")

        # Simulate the bank's internal knowledge of user's savings balance.
        # In a real system, this would come from a secure database query linked to the user's account.
        available_savings_balance = 15500.00

        # Initialize the list of events (slot sets) to return
        events = []

        # Ensure loan_term is an integer
        try:
            loan_term_int = int(loan_term)
        except (ValueError, TypeError):
            events.append(
                SlotSet(
                    "loan_error",
                    "Invalid loan term format. Please provide a number for months.",
                )
            )
            return events

        # Convert down_payment_amount to float if provided
        down_payment_float = None
        if down_payment_amount is not None:
            try:
                down_payment_float = float(down_payment_amount)
            except (ValueError, TypeError):
                events.append(
                    SlotSet(
                        "loan_error",
                        "Invalid down payment amount format. Please provide a number.",
                    )
                )
                return events

        # --- API Call ---
        financing_api = MockFinancingAPI()
        api_response_str = financing_api.calculate_loan_details(
            purchase_amount=car_price,
            loan_term_months=loan_term_int,
            available_savings_balance=available_savings_balance,
            down_payment=down_payment_float,
        )
        api_response = json.loads(api_response_str)



        # --- Process API Response and Set Slots ---
        if api_response.get("error"):
            # Set an error slot if the API returned an error
            events.append(SlotSet("loan_error", api_response["error"]))
        else:
            # format the api response to be more readable
            # round floats to 2 decimal places
            api_response = {
                k: round(v, 2) if isinstance(v, float) else v
                for k, v in api_response.items()
            }
            # Set all the relevant loan detail slots
            events.append(
                SlotSet(
                    "loan_monthly_payment", api_response["monthly_payment_estimate"]
                )
            )
            events.append(
                SlotSet("loan_total_interest", api_response["total_interest_paid"])
            )
            events.append(
                SlotSet("loan_principal_financed", api_response["principal_financed"])
            )

        return events
