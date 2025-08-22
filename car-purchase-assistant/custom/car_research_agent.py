from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import (
    AgentInput,
    AgentOutput,
    AgentToolResult,
    AgentToolSchema,
)
import json, os

from typing import List, Dict, Any, Optional
from rasa.shared.core.events import SlotSet


class CarResearchAgent(MCPOpenAgent):
    @staticmethod
    def get_custom_tool_definitions() -> List[Dict[str, Any]]:
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
            "tool_executor": recommend_cars,
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

    async def recommend_cars(
        self, search_results: str, max_recommendations: int
    ) -> AgentToolResult:
        """Analyze search results and return structured car recommendations."""
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
      "features": ["adaptive cruise control", "LED headlights", "..."]
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

    async def process_output(self, output: AgentOutput) -> AgentOutput:
        """Post-process the output before returning it to Rasa."""
        tool_results = output.tool_results
        slot_events = []
        for index in range(len(tool_results)):
            iteration_results = tool_results[index]
            for result in iteration_results:
                if result["tool_name"] == "recommend_cars":
                    try:
                        recommendations_data = json.loads(result["result"])
                        recommendations = recommendations_data.get(
                            "recommendations", []
                        )
                        if recommendations:
                            car_models = [rec["model"] for rec in recommendations]
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
                if result["tool_name"] == "tavily_search":
                    slot_events.append(SlotSet("search_results", result["result"]))
        output.events = (
            slot_events if not output.events else output.events.extend(slot_events)
        )
        return output
