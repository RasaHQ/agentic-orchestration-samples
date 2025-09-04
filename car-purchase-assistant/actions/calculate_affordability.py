import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionCalculateAffordability(Action):
    """
    Rasa Custom Action to calculate loan affordability based on user-provided financial information.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_calculate_affordability"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Calculates affordability based on user-provided financial information.
        """
        # Get user-provided financial information
        monthly_income = tracker.get_slot("monthly_income")
        monthly_expenses = tracker.get_slot("monthly_expenses")
        desired_car_payment = tracker.get_slot("desired_car_payment")

        # Get existing debt payments from previous flow or generate mock data
        total_monthly_payments = tracker.get_slot("total_monthly_payments")
        if total_monthly_payments is None:
            total_monthly_payments = random.randint(500, 3000)

        # Calculate total monthly obligations (expenses + existing debt)
        total_monthly_obligations = monthly_expenses + total_monthly_payments

        # Calculate debt-to-income ratio
        debt_to_income_ratio = (total_monthly_obligations / monthly_income) * 100

        # Calculate available income for new car payment
        available_income = monthly_income - total_monthly_obligations

        # Determine affordability status and max affordable payment
        if debt_to_income_ratio > 50:
            affordability_status = "You have a high debt-to-income ratio and may struggle to qualify for additional financing."
            max_affordable_payment = 0
        elif debt_to_income_ratio > 36:
            affordability_status = "Your debt-to-income ratio is elevated. You may qualify for financing but with higher interest rates."
            max_affordable_payment = available_income * 0.5  # 50% of available income
        else:
            affordability_status = "You have a healthy debt-to-income ratio and should qualify for competitive financing rates."
            max_affordable_payment = available_income * 0.8  # 80% of available income

        # Ensure max_affordable_payment is not negative
        max_affordable_payment = max(0, max_affordable_payment)

        # round values to 2 decimal places
        debt_to_income_ratio = round(debt_to_income_ratio, 2)
        max_affordable_payment = round(max_affordable_payment, 2)

        # Set the slots
        events = [
            SlotSet("debt_to_income_ratio", debt_to_income_ratio),
            SlotSet("affordability_status", affordability_status),
            SlotSet("max_affordable_payment", max_affordable_payment)
        ]

        return events
