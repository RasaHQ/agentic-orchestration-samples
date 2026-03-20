from datetime import datetime
from typing import Any, Dict, List, Text

from project.actions.slot_memory import SKILL_TRANSACTION_HANDLING, skill_scoped_slot
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


def _txn_field(txn: Any, field: str, default: Any) -> Any:
    """Read a field from a transaction dict or object."""
    if isinstance(txn, dict):
        return txn.get(field, default)
    return getattr(txn, field, default)


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
            merchant = _txn_field(txn, "merchant", "")
            category = _txn_field(txn, "category", "")
            amount = _txn_field(txn, "amount", 0)
            timestamp = _txn_field(txn, "timestamp", "")
            location = _txn_field(txn, "location", "")
            is_disputed = _txn_field(txn, "is_disputed", False)

            # Format amount as currency
            amount_str = (
                f"${amount:,.2f}" if isinstance(amount, (int, float)) else str(amount)
            )
            # Shorten timestamp for display
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
            skill_scoped_slot(
                "transactions_display",
                displayed_transactions,
                SKILL_TRANSACTION_HANDLING,
            ),
        ]
