from typing import Any, Dict, List, Text

from project.actions.db import (
    get_card_by_last_four,
    get_transactions_by_card,
    pay_card_bill,
)
from project.actions.slot_memory import SKILL_PAYMENTS, skill_scoped_slot
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionGetCardBalance(Action):
    def name(self) -> Text:
        return "action_get_card_balance"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        last_four = tracker.get_slot("pay_bill_card_last_four")

        if not last_four:
            return [SlotSet("return_value", "not_found")]

        card = get_card_by_last_four(user_id, last_four)
        if not card:
            return [SlotSet("return_value", "not_found")]

        # Fetch recent transactions for the card after payment
        transactions = get_transactions_by_card(user_id, card.id, limit=5)

        # Format transactions for display
        formatted_transactions: List[Dict[str, Any]] = []
        for txn in transactions:
            formatted_txn: Dict[str, Any] = {
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

        return [
            SlotSet("return_value", "success"),
            SlotSet("selected_card_id", card.id),
            skill_scoped_slot("card_balance_due", card.balance_due, SKILL_PAYMENTS),
            skill_scoped_slot("card_due_date", card.due_date, SKILL_PAYMENTS),
            skill_scoped_slot(
                "transaction_list", formatted_transactions, SKILL_PAYMENTS
            ),
        ]


class ActionPayBill(Action):
    def name(self) -> Text:
        return "action_pay_bill"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id: str = tracker.sender_id
        card_id = tracker.get_slot("selected_card_id")
        amount = tracker.get_slot("pay_bill_amount")

        if not card_id or not amount:
            return [SlotSet("return_value", "error")]

        result = pay_card_bill(user_id, card_id, float(amount))

        if result["success"]:
            # Fetch recent transactions for the card after payment
            transactions = get_transactions_by_card(user_id, card_id, limit=5)

            # Format transactions for display
            formatted_transactions: List[Dict[str, Any]] = []
            for txn in transactions:
                formatted_txn: Dict[str, Any] = {
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

            return [
                SlotSet("return_value", "success"),
                skill_scoped_slot(
                    "payment_new_balance", result["new_balance"], SKILL_PAYMENTS
                ),
                skill_scoped_slot(
                    "transaction_list", formatted_transactions, SKILL_PAYMENTS
                ),
            ]
        elif result.get("error") == "Payment exceeds balance due":
            return [SlotSet("return_value", "exceeds_balance")]
        else:
            return [SlotSet("return_value", "error")]
