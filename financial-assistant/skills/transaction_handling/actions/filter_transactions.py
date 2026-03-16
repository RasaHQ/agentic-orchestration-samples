from datetime import datetime
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

class ActionFormatTransactions(Action):
    def name(self) -> Text:
        return "action_format_transactions"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        transactions = tracker.get_slot("selected_transactions")
        if not transactions:
            return [SlotSet("return_value", "no_transactions")]

        # Format each transaction for readable UI display
        lines = []
        for i, txn in enumerate(transactions, start=1):
            # Support both object and dict (slot may come from LLM or prior action)
            merchant = txn.get("merchant", "") if isinstance(txn, dict) else getattr(txn, "merchant", "")
            category = txn.get("category", "") if isinstance(txn, dict) else getattr(txn, "category", "")
            amount = txn.get("amount", 0) if isinstance(txn, dict) else getattr(txn, "amount", 0)
            timestamp = txn.get("timestamp", "") if isinstance(txn, dict) else getattr(txn, "timestamp", "")
            location = txn.get("location", "") if isinstance(txn, dict) else getattr(txn, "location", "")
            is_disputed = txn.get("is_disputed", False) if isinstance(txn, dict) else getattr(txn, "is_disputed", False)

            # Format amount as currency
            amount_str = f"${amount:,.2f}" if isinstance(amount, (int, float)) else str(amount)
            # Shorten timestamp for display (e.g. "2026-01-20T08:30:00Z" -> "Jan 20, 2026")
            date_str = timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y")
                except (ValueError, TypeError):
                    pass
            disputed_str = "Yes" if is_disputed else "No"

            lines.append(
                f"{i}. **{merchant}** — {category}\n"
                f"   {date_str} · {amount_str} · {location}\n"
                f"   Disputed: {disputed_str}"
            )

        displayed_transactions = "\n\n".join(lines)

        return [
            SlotSet("return_value", "success"),
            SlotSet("transactions_display", displayed_transactions),
        ]
