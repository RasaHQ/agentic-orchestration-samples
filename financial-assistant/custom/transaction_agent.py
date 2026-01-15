"""Transaction Agent for viewing and disputing credit card transactions."""

import json
from typing import Any, Dict, List, Optional

from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import AgentToolResult

from actions.db import (
    dispute_transactions,
    get_card_by_last_four,
    get_transactions_by_card,
    get_transactions_by_date,
    get_transactions_by_merchant,
)


class TransactionAgent(MCPOpenAgent):
    """Agent for handling transaction viewing and disputes with contextual understanding."""

    def get_custom_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define the tools available to this agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_transactions",
                    "description": "Fetch recent transactions for a credit card",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "card_last_four": {
                                "type": "string",
                                "description": "Last 4 digits of the credit card",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of transactions to return (default: 5)",
                            },
                        },
                        "required": ["card_last_four", "limit"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.get_transactions,
            },
            {
                "type": "function",
                "function": {
                    "name": "get_transactions_by_merchant",
                    "description": "Find transactions by merchant name (partial match)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "merchant": {
                                "type": "string",
                                "description": "Merchant name to search for",
                            },
                            "card_last_four": {
                                "type": ["string", "null"],
                                "description": "Filter by card last 4 digits, or null to search all cards",
                            },
                        },
                        "required": ["merchant", "card_last_four"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.search_by_merchant,
            },
            {
                "type": "function",
                "function": {
                    "name": "get_transactions_by_date",
                    "description": "Find transactions by date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format",
                            },
                            "card_last_four": {
                                "type": ["string", "null"],
                                "description": "Filter by card last 4 digits, or null to search all cards",
                            },
                        },
                        "required": ["date", "card_last_four"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self.search_by_date,
            },
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

    def _format_transaction(self, txn: Any) -> Dict[str, Any]:
        """Format a transaction for display."""
        return {
            "id": txn.id,
            "date": txn.timestamp[:10],
            "time": txn.timestamp[11:16],
            "merchant": txn.merchant,
            "category": txn.category,
            "amount": f"${txn.amount:.2f}",
            "location": txn.location,
            "disputed": txn.is_disputed,
        }

    async def get_transactions(self, arguments: Dict[str, Any]) -> AgentToolResult:
        """Fetch recent transactions for a card."""
        session_id = self._get_session_id()
        card_last_four = arguments["card_last_four"]
        limit = arguments.get("limit", 5)

        card = get_card_by_last_four(session_id, card_last_four)
        if not card:
            return AgentToolResult(
                tool_name="get_transactions",
                result=json.dumps({"error": f"No card found ending in {card_last_four}"}),
            )

        transactions = get_transactions_by_card(session_id, card.id, limit=limit)
        formatted = [self._format_transaction(t) for t in transactions]

        return AgentToolResult(
            tool_name="get_transactions",
            result=json.dumps({
                "card": f"****{card_last_four}",
                "card_type": card.type,
                "transaction_count": len(formatted),
                "transactions": formatted,
            }),
        )

    async def search_by_merchant(self, arguments: Dict[str, Any]) -> AgentToolResult:
        """Search transactions by merchant name."""
        session_id = self._get_session_id()
        merchant = arguments["merchant"]
        card_last_four = arguments.get("card_last_four")

        card_id = None
        if card_last_four:
            card = get_card_by_last_four(session_id, card_last_four)
            if card:
                card_id = card.id

        transactions = get_transactions_by_merchant(session_id, merchant, card_id)
        formatted = [self._format_transaction(t) for t in transactions]

        return AgentToolResult(
            tool_name="get_transactions_by_merchant",
            result=json.dumps({
                "search_term": merchant,
                "match_count": len(formatted),
                "transactions": formatted,
            }),
        )

    async def search_by_date(self, arguments: Dict[str, Any]) -> AgentToolResult:
        """Search transactions by date."""
        session_id = self._get_session_id()
        date_str = arguments["date"]
        card_last_four = arguments.get("card_last_four")

        card_id = None
        if card_last_four:
            card = get_card_by_last_four(session_id, card_last_four)
            if card:
                card_id = card.id

        transactions = get_transactions_by_date(session_id, date_str, card_id)
        formatted = [self._format_transaction(t) for t in transactions]

        return AgentToolResult(
            tool_name="get_transactions_by_date",
            result=json.dumps({
                "date": date_str,
                "match_count": len(formatted),
                "transactions": formatted,
            }),
        )

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
