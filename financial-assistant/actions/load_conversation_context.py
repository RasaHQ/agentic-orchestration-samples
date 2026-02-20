"""Override load conversation context: user profile from DB.

This action replaces the default action_load_conversation_context so that
the session-start flow loads the user profile from the financial assistant DB
instead of from channel metadata. Action context from metadata is still
merged in when present.
"""

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.db import get_user_profile, UserProfile


def _profile_to_context_dict(profile: UserProfile) -> Dict[str, Any]:
    """Convert UserProfile to a dict for the user_profile slot."""
    return {
        "user_id": profile.user_id,
        "name": profile.name,
        "email": profile.email,
        "loyalty_memberships": [
            {
                "program": m.program,
                "tier": m.tier,
                "member_since": m.member_since,
            }
            for m in profile.loyalty_memberships
        ],
        "linked_cards": profile.linked_cards,
    }


class ActionLoadConversationContext(Action):
    """Load conversation context with user profile from DB.

    Called by the session-start flow (action_load_conversation_context).
    Fetches the user profile from the financial assistant DB and sets the
    user_profile slot. Optionally sets action_context from session metadata
    when available.
    """

    def name(self) -> Text:
        return "action_load_conversation_context"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Any]:
        user_id = tracker.sender_id
        events: List[Any] = []

        # User profile from DB
        try:
            profile = get_user_profile(user_id)
            user_profile_dict = _profile_to_context_dict(profile)
            events.append(SlotSet("user_profile", user_profile_dict))
        except Exception:
            # No profile or DB error: leave slot unset or clear
            events.append(SlotSet("user_profile", None))

        # Action context from session-start metadata if present
        metadata = tracker.get_slot("session_started_metadata") or {}
        if isinstance(metadata, dict):
            conversation_context = metadata.get("conversation_context")
            if isinstance(conversation_context, dict):
                action_context = conversation_context.get("action_context")
            else:
                action_context = metadata.get("action_context")
            if action_context is not None and isinstance(action_context, dict):
                events.append(SlotSet("action_context", action_context))

        return events
