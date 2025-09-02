import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionCheckExistingLoans(Action):
    """
    Rasa Custom Action to check the user's existing loans.
    Returns mock data about current loan obligations.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_check_existing_loans"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Executes the action to check existing loans and set relevant slots.
        """
        # Mock loan data - randomly generate 0-3 loans
        loan_count = random.randint(0, 3)

        if loan_count == 0:
            existing_loans = "None"
            total_monthly_payments = 0.0
        else:
            # Generate mock loan data
            loan_types = ["mortgage", "student loan", "personal loan", "credit card", "auto loan"]
            loans = []
            total_monthly_payments = 0.0

            for i in range(loan_count):
                loan_type = random.choice(loan_types)
                monthly_payment = random.randint(200, 2000)
                total_monthly_payments += monthly_payment
                loans.append(f"{loan_type} (${monthly_payment:,.2f}/month)")

            existing_loans = "; ".join(loans)

        # Set the slots
        events = [
            SlotSet("existing_loans", existing_loans),
            SlotSet("total_monthly_payments", total_monthly_payments),
            SlotSet("loan_count", loan_count)
        ]

        return events
