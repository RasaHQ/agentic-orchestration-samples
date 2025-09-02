import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionCheckCreditScore(Action):
    """
    Rasa Custom Action to check the user's credit score.
    Returns a random credit score between 300-850 with corresponding rating.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_check_credit_score"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Executes the action to check credit score and set relevant slots.
        """
        # Generate a random credit score between 300-850
        credit_score = random.randint(300, 850)

        # Determine credit rating based on score
        if credit_score >= 800:
            credit_rating = "excellent"
        elif credit_score >= 740:
            credit_rating = "very good"
        elif credit_score >= 670:
            credit_rating = "good"
        elif credit_score >= 580:
            credit_rating = "fair"
        else:
            credit_rating = "poor"

        # Set the slots
        events = [
            SlotSet("credit_score", credit_score),
            SlotSet("credit_rating", credit_rating)
        ]

        return events
