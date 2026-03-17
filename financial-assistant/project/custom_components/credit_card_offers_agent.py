"""Credit Card Offers Agent for personalized recommendations."""

import json
from typing import Any, Dict, List

from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import AgentToolResult, AgentToolContext

from project.actions.db import get_loyalty_memberships, get_user_profile, has_loyalty_membership


# Available credit card offers
CREDIT_CARD_OFFERS = [
    {
        "id": "star_alliance_platinum",
        "name": "Star Alliance Platinum Card",
        "annual_fee": 0,
        "annual_fee_note": "Free for Star Alliance Gold members, $195 otherwise",
        "rewards": "5x points on travel purchases",
        "benefits": [
            "Airport lounge access",
            "No foreign transaction fees",
            "Priority boarding on Star Alliance flights",
            "Travel insurance included",
        ],
        "best_for": ["Star Alliance Gold members", "Frequent international travelers"],
        "eligibility": {"loyalty_program": "Star Alliance", "tier": "Gold"},
    },
    {
        "id": "travel_elite",
        "name": "Travel Elite Card",
        "annual_fee": 95,
        "annual_fee_note": "Waived first year",
        "rewards": "3x points on travel and dining",
        "benefits": [
            "$200 annual travel credit",
            "Priority boarding with partner airlines",
            "Global Entry/TSA PreCheck credit",
        ],
        "best_for": ["Travel enthusiasts", "Dining lovers"],
        "eligibility": None,
    },
    {
        "id": "cash_back_rewards",
        "name": "Cash Back Rewards Card",
        "annual_fee": 0,
        "annual_fee_note": "No annual fee ever",
        "rewards": "2% cash back on all purchases, 5% on rotating categories",
        "benefits": [
            "No minimum redemption",
            "Cash back never expires",
            "Cell phone protection",
        ],
        "best_for": ["Everyday spenders", "Those who prefer cash back"],
        "eligibility": None,
    },
    {
        "id": "premium_rewards",
        "name": "Premium Rewards Card",
        "annual_fee": 250,
        "annual_fee_note": None,
        "rewards": "4x points on dining and entertainment",
        "benefits": [
            "Concierge service",
            "Comprehensive travel insurance",
            "Purchase protection",
            "Extended warranty",
        ],
        "best_for": ["High spenders", "Entertainment lovers"],
        "eligibility": None,
    },
]


class CreditCardOffersAgent(MCPOpenAgent):
    """Agent for personalized credit card recommendations using memory."""

    def get_custom_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define the tools available to this agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_user_profile",
                    "description": "Fetch the user's profile including preferences and loyalty memberships",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.fetch_user_profile,
            },
            {
                "type": "function",
                "function": {
                    "name": "get_loyalty_memberships",
                    "description": "Get the user's loyalty program memberships",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.fetch_loyalty_memberships,
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_offers",
                    "description": "Get all available credit card offers",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.get_all_offers,
            },
            {
                "type": "function",
                "function": {
                    "name": "get_personalized_recommendations",
                    "description": "Get credit card recommendations based on user profile",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.get_personalized_recommendations,
            },
            {
                "type": "function",
                "function": {
                    "name": "check_offer_eligibility",
                    "description": "Check if user is eligible for a specific offer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "offer_id": {
                                "type": "string",
                                "description": "The ID of the credit card offer",
                            },
                        },
                        "required": ["offer_id"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.check_eligibility,
            },
        ]

    def _get_session_id(self) -> str:
        """Get the session ID from the agent context."""
        if hasattr(self, "_current_input") and self._current_input:
            metadata = getattr(self._current_input, "metadata", {}) or {}
            return metadata.get("sender_id", "default_session")
        return "default_session"

    async def fetch_user_profile(self, arguments: Dict[str, Any], context: AgentToolContext) -> AgentToolResult:
        """Fetch the user's profile."""
        session_id = self._get_session_id()

        try:
            profile = get_user_profile(session_id)
            return AgentToolResult(
                tool_name="get_user_profile",
                result=json.dumps({
                    "name": profile.name,
                    "loyalty_memberships": [
                        {"program": m.program, "tier": m.tier}
                        for m in profile.loyalty_memberships
                    ],
                    "preferences": {
                        "travel_heavy": profile.preferences.travel_heavy,
                        "preferred_airlines": profile.preferences.preferred_airlines,
                    },
                }),
            )
        except Exception as e:
            return AgentToolResult(
                tool_name="get_user_profile",
                result=json.dumps({"error": str(e)}),
            )

    async def fetch_loyalty_memberships(
        self, arguments: Dict[str, Any], context: AgentToolContext
    ) -> AgentToolResult:
        """Fetch the user's loyalty memberships."""
        session_id = self._get_session_id()

        try:
            memberships = get_loyalty_memberships(session_id)
            return AgentToolResult(
                tool_name="get_loyalty_memberships",
                result=json.dumps({
                    "memberships": [
                        {
                            "program": m.program,
                            "tier": m.tier,
                            "member_since": m.member_since,
                        }
                        for m in memberships
                    ]
                }),
            )
        except Exception as e:
            return AgentToolResult(
                tool_name="get_loyalty_memberships",
                result=json.dumps({"error": str(e)}),
            )

    async def get_all_offers(self, arguments: Dict[str, Any], context: AgentToolContext) -> AgentToolResult:
        """Get all available credit card offers."""
        offers = [
            {
                "id": o["id"],
                "name": o["name"],
                "annual_fee": o["annual_fee"],
                "rewards": o["rewards"],
                "best_for": o["best_for"],
            }
            for o in CREDIT_CARD_OFFERS
        ]
        return AgentToolResult(
            tool_name="get_all_offers",
            result=json.dumps({"offers": offers}),
        )

    async def get_personalized_recommendations(
        self, arguments: Dict[str, Any], context: AgentToolContext
    ) -> AgentToolResult:
        """Get personalized credit card recommendations."""
        session_id = self._get_session_id()

        try:
            profile = get_user_profile(session_id)
            recommendations = []

            for offer in CREDIT_CARD_OFFERS:
                score = 0
                reasons = []

                # Check eligibility-based offers
                if offer.get("eligibility"):
                    eligibility = offer["eligibility"]
                    membership = has_loyalty_membership(
                        session_id, eligibility["loyalty_program"]
                    )
                    if membership and membership.tier == eligibility["tier"]:
                        score += 100
                        reasons.append(
                            f"You're a {membership.program} {membership.tier} member - "
                            f"this card is FREE for you!"
                        )

                # Check travel preferences
                if profile.preferences.travel_heavy:
                    if "travel" in offer["rewards"].lower():
                        score += 50
                        reasons.append("Great for your travel-heavy lifestyle")

                # Add to recommendations if score > 0 or no special eligibility
                if score > 0 or not offer.get("eligibility"):
                    recommendations.append({
                        "offer": {
                            "id": offer["id"],
                            "name": offer["name"],
                            "annual_fee": offer["annual_fee"],
                            "annual_fee_note": offer.get("annual_fee_note"),
                            "rewards": offer["rewards"],
                            "benefits": offer["benefits"],
                        },
                        "match_score": score,
                        "personalized_reasons": reasons,
                    })

            # Sort by score descending
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)

            return AgentToolResult(
                tool_name="get_personalized_recommendations",
                result=json.dumps({
                    "user_name": profile.name,
                    "recommendations": recommendations[:3],
                }),
            )
        except Exception as e:
            return AgentToolResult(
                tool_name="get_personalized_recommendations",
                result=json.dumps({"error": str(e)}),
            )

    async def check_eligibility(self, arguments: Dict[str, Any], context: AgentToolContext) -> AgentToolResult:
        """Check if user is eligible for a specific offer."""
        session_id = self._get_session_id()
        offer_id = arguments["offer_id"]

        offer = next((o for o in CREDIT_CARD_OFFERS if o["id"] == offer_id), None)
        if not offer:
            return AgentToolResult(
                tool_name="check_offer_eligibility",
                result=json.dumps({"error": f"Offer {offer_id} not found"}),
            )

        if not offer.get("eligibility"):
            return AgentToolResult(
                tool_name="check_offer_eligibility",
                result=json.dumps({
                    "offer_name": offer["name"],
                    "eligible": True,
                    "message": "This card is available to all applicants",
                }),
            )

        eligibility = offer["eligibility"]
        membership = has_loyalty_membership(session_id, eligibility["loyalty_program"])

        if membership and membership.tier == eligibility["tier"]:
            return AgentToolResult(
                tool_name="check_offer_eligibility",
                result=json.dumps({
                    "offer_name": offer["name"],
                    "eligible": True,
                    "special_benefit": True,
                    "message": f"As a {membership.program} {membership.tier} member, "
                    f"you qualify for the FREE annual fee!",
                }),
            )
        else:
            return AgentToolResult(
                tool_name="check_offer_eligibility",
                result=json.dumps({
                    "offer_name": offer["name"],
                    "eligible": True,
                    "special_benefit": False,
                    "message": f"You can apply for this card. Note: {eligibility['loyalty_program']} "
                    f"{eligibility['tier']} members get the annual fee waived.",
                }),
            )
