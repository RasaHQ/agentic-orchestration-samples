import os
import json
from typing import Dict, Any, List
from tavily import TavilyClient


class TavilySearchTool:
    """Tavily web search tool for MCP server"""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        self.client = TavilyClient(api_key=api_key)

    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return "Search the web using Tavily to get current information"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                },
                "include_answer": {
                    "type": "boolean",
                    "description": "Whether to include a direct answer",
                    "default": True,
                },
            },
            "required": ["query", "max_results", "include_answer"],
            "additionalProperties": False,
        }

    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the Tavily search"""
        try:
            query = arguments["query"]
            max_results = arguments.get("max_results", 3)
            include_answer = arguments.get("include_answer", True)

            # Perform Tavily search
            response = self.client.search(
                query=query, max_results=max_results, include_answer=include_answer
            )

            # Format results for the LLM
            result = {"query": query, "results": []}

            # Add direct answer if available
            if include_answer and response.get("answer"):
                result["answer"] = response["answer"]

            # Add search results
            for item in response.get("results", []):
                result["results"].append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                    }
                )

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Error performing search: {str(e)}"
