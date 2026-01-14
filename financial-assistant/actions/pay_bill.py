from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_card_by_last_four, pay_card_bill


class ActionGetCardBalance(Action):
    def name(self) -> Text:
        return "action_get_card_balance"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        session_id = tracker.sender_id
        last_four = tracker.get_slot("pay_bill_card_last_four")

        if not last_four:
            return [SlotSet("return_value", "not_found")]

        card = get_card_by_last_four(session_id, last_four)
        if not card:
            return [SlotSet("return_value", "not_found")]

        return [
            SlotSet("return_value", "success"),
            SlotSet("selected_card_id", card.id),
            SlotSet("card_balance_due", card.balance_due),
            SlotSet("card_due_date", card.due_date),
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
        session_id = tracker.sender_id
        card_id = tracker.get_slot("selected_card_id")
        amount = tracker.get_slot("pay_bill_amount")

        if not card_id or not amount:
            return [SlotSet("return_value", "error")]

        result = pay_card_bill(session_id, card_id, float(amount))

        if result["success"]:
            return [
                SlotSet("return_value", "success"),
                SlotSet("payment_new_balance", result["new_balance"]),
            ]
        elif result.get("error") == "Payment exceeds balance due":
            return [SlotSet("return_value", "exceeds_balance")]
        else:
            return [SlotSet("return_value", "error")]
