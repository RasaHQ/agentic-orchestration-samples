import re
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionValidateCreditInfo(Action):
    """
    Rasa Custom Action to validate the credit information provided by the user.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_validate_credit_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Validates the credit information and provides feedback.
        """
        events = []

        # Get the slots
        full_name = tracker.get_slot("full_name")
        ssn_last_four = tracker.get_slot("ssn_last_four")
        date_of_birth = tracker.get_slot("date_of_birth")

        valid_credit_info = False

        # Validate SSN last four digits
        if ssn_last_four:
            # Remove any non-digit characters
            ssn_clean = re.sub(r'\D', '', ssn_last_four)
            if len(ssn_clean) == 4:
                events.append(SlotSet("ssn_last_four", ssn_clean))
            else:
                events.append(SlotSet("ssn_last_four", None))
                dispatcher.utter_message("Please provide the last 4 digits of your SSN (numbers only).")

        # Validate date of birth format
        if date_of_birth:
            # Check if it's in a reasonable date format
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
                r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
                r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            ]

            is_valid_date = any(re.match(pattern, date_of_birth) for pattern in date_patterns)
            if not is_valid_date:
                events.append(SlotSet("date_of_birth", None))
                dispatcher.utter_message("Please provide your date of birth in MM/DD/YYYY format.")

        # Provide confirmation if all info is valid
        if full_name and ssn_last_four and date_of_birth:
            dispatcher.utter_message(f"Thank you, {full_name}. I have your information and will now check your credit score.")
            valid_credit_info = True

        events.append(SlotSet("valid_credit_info", valid_credit_info))
        return events
