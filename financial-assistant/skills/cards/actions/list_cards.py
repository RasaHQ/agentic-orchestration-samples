import json
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from project.actions.db import get_credit_cards
from project.actions.slot_memory import SKILL_CARDS, skill_scoped_slot


class ActionListCards(Action):
    def name(self) -> Text:
        return "action_list_cards"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        cards = get_credit_cards(user_id)

        if not cards:
            return [
                skill_scoped_slot("cards_list", "No credit cards found.", SKILL_CARDS),
                skill_scoped_slot("cards_raw", "[]", SKILL_CARDS),
            ]

        # Store raw card data as JSON
        cards_raw = [card.model_dump() for card in cards]

        # Format the cards list for display
        card_descriptions = []
        for card in cards:
            status_parts = []
            if card.is_locked:
                status_parts.append("locked")
            if card.is_lost:
                status_parts.append("reported lost")
            status = f" ({', '.join(status_parts)})" if status_parts else ""

            description = (
                f"{card.type} ending in {card.last_four} - "
                f"Balance: ${card.balance_due:.2f}, "
                f"Due: {card.due_date}{status}"
            )
            card_descriptions.append(description)

        cards_list = "\n\n".join(card_descriptions)
        return [
            skill_scoped_slot("cards_list", cards_list, SKILL_CARDS),
            skill_scoped_slot("cards_raw", json.dumps(cards_raw), SKILL_CARDS),
        ]
