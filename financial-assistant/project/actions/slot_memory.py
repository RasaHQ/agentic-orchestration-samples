"""Slot event dicts with metadata so the tracker syncs to the correct memory keys.

Stack frames may have an empty skill_id; explicit metadata ensures skill-scoped
memory (e.g. transaction_handling.transaction_list) matches flow crucial_memory_items.
"""

from typing import Any, Dict

from rasa_sdk.events import SlotSet

SKILL_TRANSACTION_HANDLING = "transaction_handling"
SKILL_PAYMENTS = "payments"
SKILL_CARDS = "cards"


def _with_meta(
    slot_name: str,
    value: Any,
    metadata: Dict[str, Any],
    *,
    filled_by: str,
) -> Dict[str, Any]:
    ev: Dict[str, Any] = SlotSet(slot_name, value)
    ev["metadata"] = metadata
    ev["filled_by"] = filled_by
    return ev


def skill_scoped_slot(slot_name: str, value: Any, skill_id: str) -> Dict[str, Any]:
    """Slot update stored under <skill_id>.<slot_name> in memory."""
    return _with_meta(
        slot_name,
        value,
        {"skill_id": skill_id},
        filled_by="custom_action",
    )


def system_scoped_slot(
    slot_name: str,
    value: Any,
    *,
    description: str,
) -> Dict[str, Any]:
    """Session context slots (e.g. user_profile) under system.<slot_name>."""
    return _with_meta(
        slot_name,
        value,
        {
            "scope": "system",
            "memory_key": f"system.{slot_name}",
            "description": description,
        },
        filled_by="system",
    )
