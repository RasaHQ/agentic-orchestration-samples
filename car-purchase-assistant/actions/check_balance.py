import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionCheckBalance(Action):
    """
    Rasa Custom Action to check the user's account balance.
    Returns a random balance between $5,000 and $100,000.
    """

    def name(self) -> Text:
        """Unique identifier of the action."""
        return "action_check_balance"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """
        Executes the action to check balance and set the balance slot.
        """
        # Generate a random balance between $5,000 and $100,000
        balance = random.randint(5000, 100000)

        # Set the balance slot
        events = [SlotSet("balance", balance)]

        return events
