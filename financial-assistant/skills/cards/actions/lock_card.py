from typing import Any, Dict, List, Text

from project.actions.db import get_card_by_last_four, lock_card
from project.actions.slot_memory import SKILL_CARDS, skill_scoped_slot
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionLockCard(Action):
    def name(self) -> Text:
        return "action_lock_card"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        last_four = tracker.get_slot("lock_card_last_four")

        if not last_four:
            return [SlotSet("return_value", "not_found")]

        # Find the card
        card = get_card_by_last_four(user_id, last_four)
        if not card:
            return [SlotSet("return_value", "not_found")]

        # Check if already locked
        if card.is_locked:
            return [SlotSet("return_value", "already_locked")]

        # Lock the card
        success = lock_card(user_id, card.id)
        if success:
            return [
                SlotSet("return_value", "success"),
                skill_scoped_slot("selected_card_id", card.id, SKILL_CARDS),
            ]
        else:
            return [SlotSet("return_value", "error")]
