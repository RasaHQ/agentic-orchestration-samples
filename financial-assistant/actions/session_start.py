"""Session start action to load user profile into memory."""

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_user_profile


class ActionSessionStart(Action):
    """Load user profile into memory at conversation start."""

    def name(self) -> Text:
        return "action_session_start"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        events = []

        try:
            profile = get_user_profile(user_id)

            # Store loyalty memberships in memory-ready format
            if profile.loyalty_memberships:
                memberships = [
                    f"{m.program} {m.tier}" for m in profile.loyalty_memberships
                ]
                events.append(
                    SlotSet("user_loyalty_memberships", memberships)
                )

            # Store user preferences
            if profile.preferences.travel_heavy:
                events.append(
                    SlotSet("user_is_travel_heavy", True)
                )

            if profile.preferences.preferred_airlines:
                events.append(
                    SlotSet("user_preferred_airlines", profile.preferences.preferred_airlines)
                )

            # Store user name for personalization
            events.append(SlotSet("user_name", profile.name))

        except Exception:
            # If profile loading fails, continue without it
            pass

        return events
