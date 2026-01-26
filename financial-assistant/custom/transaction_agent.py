"""Transaction Agent for disputing credit card transactions."""

import json
from typing import Any, Dict, List

from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import AgentToolResult

from actions.db import dispute_transactions


class TransactionAgent(MCPOpenAgent):
    """Agent for handling transaction disputes."""

    def get_custom_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define the tools available to this agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "dispute_transactions",
                    "description": "Mark transactions as disputed for fraud investigation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transaction_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of transaction IDs to dispute",
                            },
                        },
                        "required": ["transaction_ids"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.dispute_txns,
            },
        ]

    def _get_session_id(self) -> str:
        """Get the session ID from the agent context."""
        # Try to get from metadata or use a default
        if hasattr(self, "_current_input") and self._current_input:
            metadata = getattr(self._current_input, "metadata", {}) or {}
            return metadata.get("sender_id", "default_session")
        return "default_session"

    async def dispute_txns(self, arguments: Dict[str, Any]) -> AgentToolResult:
        """Dispute specified transactions."""
        session_id = self._get_session_id()
        txn_ids = arguments["transaction_ids"]

        result = dispute_transactions(session_id, txn_ids)

        return AgentToolResult(
            tool_name="dispute_transactions",
            result=json.dumps({
                "success": result["success"],
                "disputed_count": result["disputed_count"],
                "message": f"Successfully disputed {result['disputed_count']} transaction(s)"
                if result["success"]
                else "No transactions were disputed",
            }),
        )
