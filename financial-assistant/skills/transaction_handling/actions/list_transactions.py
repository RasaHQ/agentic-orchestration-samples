from typing import Any, Dict, List, Text

from project.actions.db import get_card_by_last_four, get_transactions_by_card
from project.actions.slot_memory import SKILL_TRANSACTION_HANDLING, skill_scoped_slot
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionListTransactions(Action):
    def name(self) -> Text:
        return "action_list_transactions"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        card_last_four = tracker.get_slot("txn_list_card_last_four")
        limit = 10

        if not card_last_four:
            return [SlotSet("return_value", "no_card")]

        card = get_card_by_last_four(user_id, card_last_four)
        if not card:
            return [SlotSet("return_value", "card_not_found")]

        transactions = get_transactions_by_card(user_id, card.id, limit=limit)

        if not transactions:
            return [SlotSet("return_value", "no_transactions")]

        # Raw list for transaction_list (same shape as lookup flow: id,
        # timestamp, amount float, etc.)
        raw_list = [
            {
                "id": txn.id,
                "timestamp": txn.timestamp,
                "merchant": txn.merchant,
                "category": txn.category,
                "amount": txn.amount,
                "location": txn.location,
                "is_disputed": txn.is_disputed,
            }
            for txn in transactions
        ]

        return [
            SlotSet("return_value", "success"),
            SlotSet("selected_card_id", card.id),
            skill_scoped_slot("transaction_list", raw_list, SKILL_TRANSACTION_HANDLING),
        ]
