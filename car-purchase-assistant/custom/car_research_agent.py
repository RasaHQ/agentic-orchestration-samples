from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import (
    AgentToolResult,
)
import json, os

from typing import List, Dict, Any, Optional
from rasa.shared.core.events import Event, SlotSet
from rasa.core.channels.channel import OutputChannel
from rasa.agents.constants import (
    TOOL_ADDITIONAL_PROPERTIES_KEY,
    TOOL_DESCRIPTION_KEY,
    TOOL_NAME_KEY,
    TOOL_PARAMETERS_KEY,
    TOOL_PROPERTIES_KEY,
    TOOL_REQUIRED_KEY,
    TOOL_STRICT_KEY,
    TOOL_TYPE_FUNCTION_KEY,
    TOOL_TYPE_KEY,
)

KEY_TASK_COMPLETED = "task_completed"

TASK_COMPLETED_TOOL = {
    TOOL_TYPE_KEY: TOOL_TYPE_FUNCTION_KEY,
    TOOL_TYPE_FUNCTION_KEY: {
        TOOL_NAME_KEY: KEY_TASK_COMPLETED,
        TOOL_DESCRIPTION_KEY: "Signal that the MCP agent has FULLY completed its "
        "primary task. Once you have presented your findings, follow-up with "
        "a message that offers any other assistance that the user might want. "
        "Ensure that this tool is called only when the findings have been presented. "
        "Don't present your findings as part of this tool.",
        TOOL_PARAMETERS_KEY: {
            TOOL_TYPE_KEY: "object",
            TOOL_PROPERTIES_KEY: {
                "message": {
                    TOOL_TYPE_KEY: "string",
                    TOOL_DESCRIPTION_KEY: "A follow up message that acknowledges user's last message and offers any further assistance. Do not add any of your internal thought process here.",
                }
            },
            TOOL_REQUIRED_KEY: ["message"],
            TOOL_ADDITIONAL_PROPERTIES_KEY: False,
        },
        TOOL_STRICT_KEY: True,
    },
}

class CarResearchAgent(MCPOpenAgent):

    @staticmethod
    def get_task_completed_tool() -> Dict[str, Any]:
        """Get the task completed tool for MCP. Override to customize/disable."""
        return TASK_COMPLETED_TOOL

    def get_custom_tool_definitions(self) -> List[Dict[str, Any]]:
        car_recommend_tool = {
            "type": "function",
            "function": {
                "name": "recommend_cars",
                "description": "Analyze search results and return structured car recommendations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_results": {
                            "type": "string",
                            "description": "The search results to analyze for car recommendations",
                        },
                        "max_recommendations": {
                            "type": "integer",
                            "description": "Maximum number of recommendations to return",
                            "default": 3,
                        },
                    },
                    "required": ["search_results", "max_recommendations"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
            "tool_executor": self.recommend_cars,
        }
        return [car_recommend_tool]

    def get_llm_client(self):
        """
        Get the LLM client instance (override for custom LLM providers).

        Returns:
            LLM client instance
        """
        from openai import AsyncOpenAI

        return AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            # Model will be specified in chat.completions.create calls
        )

    async def recommend_cars(self, arguments: Dict[str, Any]) -> AgentToolResult:
        """Analyze search results and return structured car recommendations."""
        search_results = arguments["search_results"]
        max_recommendations = arguments["max_recommendations"]

        try:
            llm_client = self.get_llm_client()
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Analyze the search results and extract up to {max_recommendations} car recommendations with SPECIFIC MODEL NAMES.

Return a JSON object with this exact structure:
{{
  "recommendations": [
    {{
      "model": "Honda CR-V (exact brand and model name)",
      "type": "hatchback (type of car, e.g., sedan, SUV, hatchback)",
      "price_range": "25000-30000",
                              "features": ["adaptive cruise control", "LED headlights", "safety features"]
      "reason": "why this specific car model is recommended based on search results"
    }}
  ]
}}

CRITICAL: The "model" field must contain the exact car brand and model name (like "Honda CR-V", "Toyota RAV4", "Kia Soul") found in the search results. Do not use generic descriptions.

Extract recommendations based on what specific car models are mentioned, discussed, or highlighted in the search results.""",
                    },
                    {
                        "role": "user",
                        "content": f"Search results to analyze:\n\n{search_results}",
                    },
                ],
                response_format={"type": "json_object"},
            )

            return AgentToolResult(
                tool_name="recommend_cars", result=response.choices[0].message.content
            )

        except Exception as e:
            return AgentToolResult(
                tool_name="recommend_cars",
                result=json.dumps(
                    {
                        "recommendations": [],
                        "error": f"Failed to generate recommendations: {str(e)}",
                    }
                ),
            )

    async def process_tool_output(
        self,
        current_iteration_tool_results: Dict[str, AgentToolResult],
        cumulative_tool_results: Dict[str, AgentToolResult],
        output_channel: Optional[OutputChannel] = None,
    ) -> List[Event]:
        """Post-process MCP tool results for the current LLM iteration."""
        slot_events: List[Event] = []

        for tool_result in current_iteration_tool_results.values():
            if tool_result.tool_name == "recommend_cars":
                try:
                    recommendations_data = json.loads(tool_result.result)
                    recommendations = recommendations_data.get(
                        "recommendations", []
                    )
                    if recommendations:
                        car_models = [
                            rec["model"] for rec in recommendations if "model" in rec
                        ]
                        car_details = {
                            rec["model"]: rec
                            for rec in recommendations
                            if "model" in rec
                        }
                        slot_events.append(
                            SlotSet("recommended_car_models", car_models)
                        )
                        slot_events.append(
                            SlotSet("recommended_car_details", car_details)
                        )
                except json.JSONDecodeError:
                    pass
            if tool_result.tool_name == "tavily_search":
                slot_events.append(SlotSet("search_results", tool_result.result))

        return slot_events
