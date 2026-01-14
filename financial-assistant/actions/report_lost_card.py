from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_card_by_last_four, lock_card, report_card_lost


class ActionReportLostCard(Action):
    def name(self) -> Text:
        return "action_report_lost_card"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        session_id = tracker.sender_id
        last_four = tracker.get_slot("report_lost_card_last_four")

        if not last_four:
            return [SlotSet("return_value", "not_found")]

        card = get_card_by_last_four(session_id, last_four)
        if not card:
            return [SlotSet("return_value", "not_found")]

        if card.is_lost:
            return [SlotSet("return_value", "already_reported")]

        success = report_card_lost(session_id, card.id)
        if success:
            return [
                SlotSet("return_value", "success"),
                SlotSet("selected_card_id", card.id),
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
        session_id = tracker.sender_id
        card_id = tracker.get_slot("selected_card_id")

        if not card_id:
            return [SlotSet("return_value", "error")]

        success = lock_card(session_id, card_id)
        if success:
            return [SlotSet("return_value", "success")]
        else:
            return [SlotSet("return_value", "error")]
