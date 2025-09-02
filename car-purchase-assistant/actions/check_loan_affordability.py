import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionCheckLoanAffordability(Action):
    """
    Rasa Custom Action to check if the user can afford a new car loan.
    Calculates affordability based on income, existing debt, and debt-to-income ratio.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_check_loan_affordability"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Executes the action to check loan affordability and set relevant slots.
        """
        total_monthly_payments = tracker.get_slot("monthly_expenses")
        monthly_income = tracker.get_slot("monthly_income")

        # Calculate debt-to-income ratio
        debt_to_income_ratio = (total_monthly_payments / monthly_income) * 100

        # Determine affordability status
        if debt_to_income_ratio > 50:
            affordability_status = "You have a high debt-to-income ratio and may struggle to qualify for additional financing."
            max_affordable_payment = 0
        elif debt_to_income_ratio > 36:
            affordability_status = "Your debt-to-income ratio is elevated. You may qualify for financing but with higher interest rates."
            max_affordable_payment = monthly_income * 0.15  # 15% of income for car payment
        else:
            affordability_status = "You have a healthy debt-to-income ratio and should qualify for competitive financing rates."
            max_affordable_payment = monthly_income * 0.20  # 20% of income for car payment

        # Set the slots
        events = [
            SlotSet("debt_to_income_ratio", debt_to_income_ratio),
            SlotSet("affordability_status", affordability_status),
            SlotSet("max_affordable_payment", max_affordable_payment)
        ]

        return events
