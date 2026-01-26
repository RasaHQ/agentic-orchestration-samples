from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_card_by_last_four, get_transactions_by_card


class ActionViewTransactions(Action):
    def name(self) -> Text:
        return "action_view_transactions"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        session_id = tracker.sender_id
        card_last_four = tracker.get_slot("view_transactions_card_last_four")
        limit_slot = tracker.get_slot("view_transactions_limit")
        if limit_slot is not None and limit_slot > 0:
            limit = int(limit_slot)
        else:
            limit = 5

        if not card_last_four:
            return [SlotSet("return_value", "no_card")]

        card = get_card_by_last_four(session_id, card_last_four)
        if not card:
            return [SlotSet("return_value", "card_not_found")]

        transactions = get_transactions_by_card(session_id, card.id, limit=limit)

        if not transactions:
            return [SlotSet("return_value", "no_transactions")]

        # Format transactions for display
        formatted_transactions = []
        for txn in transactions:
            formatted_txn = {
                "id": txn.id,
                "date": txn.timestamp[:10],
                "time": txn.timestamp[11:16],
                "merchant": txn.merchant,
                "category": txn.category,
                "amount": f"${txn.amount:.2f}",
                "location": txn.location,
                "disputed": txn.is_disputed,
            }
            formatted_transactions.append(formatted_txn)

        # Create a readable transaction list
        transaction_lines = []
        for txn in formatted_transactions:
            disputed_text = " (DISPUTED)" if txn["disputed"] else ""
            line = (
                f"• {txn['date']} {txn['time']} - {txn['merchant']} "
                f"({txn['category']}) - {txn['amount']} - {txn['location']}{disputed_text}"
            )
            transaction_lines.append(line)

        transactions_text = "\n".join(transaction_lines)

        return [
            SlotSet("return_value", "success"),
            SlotSet("selected_card_id", card.id),
            SlotSet("transaction_list", transactions_text),
            SlotSet("transaction_count", float(len(formatted_transactions))),
            SlotSet("viewed_transactions", {
                "card_last_four": card_last_four,
                "card_type": card.type,
                "transactions": formatted_transactions,
            }),
        ]
