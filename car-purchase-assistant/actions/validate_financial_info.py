import re
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionValidateFinancialInfo(Action):
    """
    Rasa Custom Action to validate the financial information provided by the user.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_validate_financial_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Validates the financial information and provides feedback.
        """
        events = []

        # Get the slots
        monthly_income = tracker.get_slot("monthly_income")
        monthly_expenses = tracker.get_slot("monthly_expenses")

        valid_financial_info = False

        # Validate and convert to float
        if monthly_income:
            try:
                income_float = float(monthly_income)
                if income_float > 0:
                    events.append(SlotSet("monthly_income", income_float))
                else:
                    events.append(SlotSet("monthly_income", None))
                    dispatcher.utter_message("Please provide a valid monthly income amount greater than $0.")
            except (ValueError, TypeError):
                events.append(SlotSet("monthly_income", None))
                dispatcher.utter_message("Please provide a valid monthly income amount (numbers only).")

        if monthly_expenses:
            try:
                expenses_float = float(monthly_expenses)
                if expenses_float >= 0:
                    events.append(SlotSet("monthly_expenses", expenses_float))
                else:
                    events.append(SlotSet("monthly_expenses", None))
                    dispatcher.utter_message("Please provide a valid monthly expenses amount (0 or greater).")
            except (ValueError, TypeError):
                events.append(SlotSet("monthly_expenses", None))
                dispatcher.utter_message("Please provide a valid monthly expenses amount (numbers only).")

        # Provide confirmation if all info is valid
        if monthly_income and monthly_expenses:
            dispatcher.utter_message("Thank you for providing your financial information. I'll now calculate your loan affordability.")
            valid_financial_info = True

        events.append(SlotSet("valid_financial_info", valid_financial_info))

        return events
