import json
from typing import Any, AsyncIterable
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.adk.events import Event, EventActions
from google.genai import types

# Import the mock car search API
from mock_car_api import MockCarSearchAPI


def search_cars_tool(
    tool_context: ToolContext,
    car_type: str = "",
    min_price: int = 10000,
    max_price: int = 60000,
    new_or_used: str = "",
    model_name: str = "",
) -> str:
    """
    Search for cars based on user criteria using the mock car search API.

    Args:
        tool_context (ToolContext): The context in which the tool operates
        car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV")
        min_price (int, optional): Minimum price range
        max_price (int, optional): Maximum price range
        new_or_used (str, optional): Whether the car is "new" or "used"
        model_name (str, optional): Specific model name to search for (e.g., "Tucson", "CR-V")

    Returns:
        str: JSON string containing car search results
    """
    try:
        car_api = MockCarSearchAPI()

        # Convert empty strings to None for optional parameters
        car_type = car_type if car_type else None
        new_or_used = new_or_used if new_or_used else None
        model_name = model_name if model_name else None

        # Use provided price range
        price_range = (min_price, max_price)

        result = car_api.search_cars(
            car_type=car_type,
            price_range=price_range,
            new_or_used=new_or_used,
            model_name=model_name,
        )
        return result
    except Exception as e:
        return json.dumps({"error": f"Car search failed: {str(e)}"})


class CarSearchAgent:
    """An agent that handles car search requests."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "car_search_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the car search agent."""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="car_search_agent",
            description=(
                "This agent helps users find cars based on their preferences "
                "including car type, price range, and whether they want new or used vehicles."
            ),
            instruction="""
You are a helpful car search assistant that helps users find vehicles based on their preferences.

When a user asks to search for cars, follow these steps:

1. **Analyze the Request**: Look at what information the user has already provided:
   - If they mention a SPECIFIC CAR MODEL (like "Tucson", "CR-V", "Camry"), you can proceed without asking for price range
   - If they only mention general preferences, gather missing information

2. **Smart Information Gathering**: Only ask for information that's truly missing:
   - Car type (sedan, SUV, compact SUV, EV, truck, etc.) - if not specified
   - New or used preference - if not specified  
   - Price range - ONLY ask if user hasn't specified a model and wants budget guidance

3. **Search with Reasonable Defaults**: When user specifies a model:
   - Use a reasonable price range for that model (e.g., $15,000-$50,000 for most models)
   - Focus on finding that specific model at local dealers
   - Don't ask for budget unless they specifically want to set limits

4. **Present Results**: Present search results clearly and ask if they want to see other options.

Guidelines:
- Be conversational and helpful
- Don't ask redundant questions if the user has been specific
- For specific models, prioritize finding that model over gathering budget details
- Present search results clearly with car details
- Help users refine their search if needed
- Do not ask any follow-up questions once you have provided search results

Example conversations:
- User: "I want a car" → You: "I'd be happy to help! What type of car are you looking for?"
- User: "Find me a Tucson" → You: [search with reasonable range] "I found several Tucson options for you..."
- User: "SUV under $30,000" → You: [search] "I found a Honda CR-V for $28,000..."
            """,
            tools=[search_cars_tool],
        )

    async def stream(
        self, query: str, session_id: str, structured_data: dict = None
    ) -> AsyncIterable[dict[str, Any]]:
        """Stream responses from the car search agent."""
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        # Enhance query with structured data context if available
        enhanced_query = query
        if structured_data:
            context_parts = []
            if structured_data.get("chosen_car_model"):
                context_parts.append(
                    f"User wants: {structured_data['chosen_car_model']}"
                )
            if structured_data.get("new_or_used"):
                context_parts.append(f"Condition: {structured_data['new_or_used']}")
            if structured_data.get("recommended_car_models"):
                context_parts.append(
                    f"Previously recommended: {', '.join(structured_data['recommended_car_models'])}"
                )
            if structured_data.get("recommended_car_details"):
                for model, details in structured_data["recommended_car_details"].items():
                    text = f"Details for recommended car '{model}': "
                    text += ", ".join(f"{k}={v}" for k, v in details.items() if k != "model" and k != "reason")
                    context_parts.append(text)

            if context_parts:
                enhanced_query = f"{query}\n\nContext: {'; '.join(context_parts)}"

        content = types.Content(
            role="user", parts=[types.Part.from_text(text=enhanced_query)]
        )

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        searching_message_sent = False

        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            # # Send searching message only once at the start
            # if not searching_message_sent:
            #     searching_message_sent = True
            #     yield {
            #         'is_task_complete': False,
            #         'updates': 'Searching for cars that match your criteria...',
            #     }

            # Handle tool results and save structured car data to state
            if event.get_function_responses():
                tool_responses = event.get_function_responses()
                for response in tool_responses:
                    if response.name == "search_cars_tool":
                        try:
                            # response.response is a dict like {"result": "JSON_STRING"}
                            tool_result = response.response

                            # Extract the JSON string from the result field
                            if (
                                isinstance(tool_result, dict)
                                and "result" in tool_result
                            ):
                                car_data_str = tool_result["result"]
                                car_data = (
                                    json.loads(car_data_str)
                                    if isinstance(car_data_str, str)
                                    else car_data_str
                                )
                            else:
                                car_data = tool_result

                            if (
                                "chosen_car_model" in car_data
                                and "chosen_car_price" in car_data
                            ):
                                structured_car_data = {
                                    "car_model": car_data.get("chosen_car_model"),
                                    "price": car_data.get("chosen_car_price"),
                                    "dealer": car_data.get("dealer_location"),
                                    "car_type": car_data.get("car_type", "EV"),
                                    "condition": car_data.get("condition", "new"),
                                    "features": car_data.get("features", []),
                                    "year": car_data.get("year"),
                                    "has_recommendation": True,
                                }

                                print(
                                    f"Saving car data to state: {structured_car_data}"
                                )

                                # Create event to save structured data to state
                                state_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "current_car_recommendation": structured_car_data
                                        }
                                    ),
                                )
                                # Let the runner process this state update
                                await self._runner.session_service.append_event(
                                    session, state_event
                                )
                            else:
                                print(f"No car recommendation found in: {car_data}")
                                # No recommendation found
                                no_rec_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "current_car_recommendation": {
                                                "has_recommendation": False
                                            }
                                        }
                                    ),
                                )
                                await self._runner.session_service.append_event(
                                    session, no_rec_event
                                )
                        except (json.JSONDecodeError, TypeError) as e:
                            print(
                                f"Error processing tool response: {e}, response: {response.response}"
                            )
                            pass

            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )

                yield {
                    "is_task_complete": True,
                    "content": response,
                    "session_id": session.id,
                }
