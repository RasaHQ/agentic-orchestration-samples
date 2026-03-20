"""Finalize credit card application after offers agent (demo stub)."""

import json
import uuid
from typing import Any, Dict, List

from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import AgentToolContext, AgentToolResult


class CardApplicationAgent(MCPOpenAgent):
    """ReAct agent: confirm choice from offers memory, then fake-start application."""

    def get_custom_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define tools for the application handoff demo."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "start_application",
                    "description": (
                        "Start the card application after the user explicitly confirmed "
                        "the offer (name, fees, and any eligibility notes). Demo only—"
                        "records intent and returns a reference id."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "offer_id": {
                                "type": "string",
                                "description": "Offer id from the recommendations (e.g. travel_elite)",
                            },
                            "offer_name": {
                                "type": "string",
                                "description": "Human-readable product name",
                            },
                            "annual_fee_summary": {
                                "type": "string",
                                "description": (
                                    "Short fee summary echoed to the user (e.g. "
                                    "'$95, first year waived' or 'Free for Star Alliance Gold')"
                                ),
                            },
                        },
                        "required": ["offer_id", "offer_name", "annual_fee_summary"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.start_application,
            },
        ]

    async def start_application(
        self, arguments: Dict[str, Any], context: AgentToolContext
    ) -> AgentToolResult:
        """Return a fake application reference (no external API)."""
        ref = f"APP-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "success": True,
            "application_reference": ref,
            "offer_id": arguments["offer_id"],
            "offer_name": arguments["offer_name"],
            "annual_fee_summary": arguments["annual_fee_summary"],
            "message": (
                "Application started. The user will receive email with next steps "
                "(demo)."
            ),
        }
        return AgentToolResult(
            tool_name="start_application",
            result=json.dumps(payload),
        )
