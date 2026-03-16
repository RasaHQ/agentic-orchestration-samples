"""Action to confirm the user's payment reminder preference (stored in discovered memory, not profile)."""

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionSetPaymentReminder(Action):
    """Confirm reminder preference; facts stay in conversation/discovered memory."""

    def name(self) -> Text:
        return "action_set_payment_reminder"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        timing = tracker.get_slot("payment_reminder_timing")
        method = tracker.get_slot("payment_reminder_notification_method")

        if not timing or not str(timing).strip():
            return [SlotSet("return_value", "missing_timing")]
        if not method or not str(method).strip():
            return [SlotSet("return_value", "missing_method")]

        return [SlotSet("return_value", "success")]
