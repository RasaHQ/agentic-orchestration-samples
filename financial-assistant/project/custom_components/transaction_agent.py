"""Transaction Agent for disputing credit card transactions."""

import json
from typing import Any, Dict, List

from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import AgentToolResult

from project.actions.db import (
    dispute_transactions,
    get_card_by_last_four,
    get_transactions_by_card,
)


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
                                "description": "List of transaction IDs to dispute. Format: 'txn_XXX' where XXX is a zero-padded number (e.g., 'txn_001', 'txn_002')",
                            },
                        },
                        "required": ["transaction_ids"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.dispute_txns,
            },
            {
                "type": "function",
                "function": {
                    "name": "get_transactions",
                    "description": "Fetch credit card transactions for a specific card. Returns recent transactions with details like date, merchant, amount, and location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "card_last_four": {
                                "type": "string",
                                "description": "The last 4 digits of the credit card to fetch transactions for",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of transactions to return (default is 5)",
                            },
                        },
                        "required": ["card_last_four", "limit"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.get_txns,
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

    async def get_txns(self, arguments: Dict[str, Any]) -> AgentToolResult:
        """Fetch transactions for a specific card."""
        session_id = self._get_session_id()
        card_last_four = arguments["card_last_four"]
        limit = arguments.get("limit", 5)

        card = get_card_by_last_four(session_id, card_last_four)
        if not card:
            return AgentToolResult(
                tool_name="get_transactions",
                result=json.dumps({
                    "success": False,
                    "error": "card_not_found",
                    "message": f"Card ending in {card_last_four} not found",
                }),
            )

        transactions = get_transactions_by_card(session_id, card.id, limit=limit)

        if not transactions:
            return AgentToolResult(
                tool_name="get_transactions",
                result=json.dumps({
                    "success": False,
                    "error": "no_transactions",
                    "message": f"No transactions found for card ending in {card_last_four}",
                }),
            )

        # Format transactions for display
        formatted_transactions = []
        for txn in transactions:
            formatted_txn = {
                "id": txn.id,
                "date": txn.timestamp[:10],
                "time": txn.timestamp[11:16],
                "merchant": txn.merchant,
                "category": txn.category,
                "amount": f"${txn.amount:.2f}",
                "location": txn.location,
                "disputed": txn.is_disputed,
            }
            formatted_transactions.append(formatted_txn)

        # Create a readable transaction list with explicit dispute status so the
        # agent does not confuse intent with current state (e.g. say "already
        # disputed" when the tool says Not disputed).
        transaction_lines = []
        for txn in formatted_transactions:
            dispute_status = "DISPUTED" if txn["disputed"] else "Not disputed"
            line = (
                f"• {txn['date']} {txn['time']} - {txn['merchant']} "
                f"({txn['category']}) - {txn['amount']} - {txn['location']} "
                f"[{dispute_status}]"
            )
            transaction_lines.append(line)

        transactions_text = "\n".join(transaction_lines)

        return AgentToolResult(
            tool_name="get_transactions",
            result=json.dumps({
                "success": True,
                "card_last_four": card_last_four,
                "card_type": card.type,
                "transaction_count": len(formatted_transactions),
                "transactions": formatted_transactions,
                "transaction_list": transactions_text,
            }),
        )
