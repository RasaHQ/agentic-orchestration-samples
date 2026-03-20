from typing import Any, Dict, List, Text

from project.actions.db import get_card_by_last_four, lock_card, report_card_lost
from project.actions.slot_memory import SKILL_CARDS, skill_scoped_slot
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionReportLostCard(Action):
    def name(self) -> Text:
        return "action_report_lost_card"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        last_four = tracker.get_slot("report_lost_card_last_four")

        if not last_four:
            return [SlotSet("return_value", "not_found")]

        card = get_card_by_last_four(user_id, last_four)
        if not card:
            return [SlotSet("return_value", "not_found")]

        if card.is_lost:
            return [SlotSet("return_value", "already_reported")]

        success = report_card_lost(user_id, card.id)
        if success:
            return [
                SlotSet("return_value", "success"),
                skill_scoped_slot("selected_card_id", card.id, SKILL_CARDS),
            ]
        else:
            return [SlotSet("return_value", "error")]


class ActionLockReportedCard(Action):
    def name(self) -> Text:
        return "action_lock_reported_card"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        card_id = tracker.get_slot("selected_card_id")

        if not card_id:
            return [SlotSet("return_value", "error")]

        success = lock_card(user_id, card_id)
        if success:
            return [SlotSet("return_value", "success")]
        else:
            return [SlotSet("return_value", "error")]
