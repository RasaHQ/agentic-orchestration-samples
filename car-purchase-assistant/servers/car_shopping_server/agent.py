import json
from typing import Any, AsyncIterable, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event, EventActions
from google.genai import types

# Import the mock car search API
from mock_car_api import MockCarSearchAPI


def check_car_availability_tool(
    model_name: str,
    dealer_name: Optional[str] = None,
    new_or_used: Optional[str] = None,
    car_type: Optional[str] = None,
) -> str:
    """
    Check if a specific car model is available at a specific dealer.

    Args:
        model_name (str): Specific model name to search for (e.g., "Tucson", "CR-V", "Camry")
        dealer_name (str, optional): Specific dealer name to check
        new_or_used (str, optional): Whether the car is "new" or "used"
        car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV")

    Returns:
        str: JSON string containing availability results
    """
    try:
        car_api = MockCarSearchAPI()

        # Convert empty strings to None for optional parameters
        dealer_name = dealer_name if dealer_name else None
        new_or_used = new_or_used if new_or_used else None
        car_type = car_type if car_type else None

        result = car_api.check_availability(
            model_name=model_name,
            dealer_name=dealer_name,
            new_or_used=new_or_used,
            car_type=car_type,
        )
        return result
    except Exception as e:
        return json.dumps({"error": f"Availability check failed: {str(e)}"})


def find_similar_cars_tool(
    model_name: str,
    dealer_name: Optional[str] = None,
    new_or_used: Optional[str] = None,
    car_type: Optional[str] = None,
) -> str:
    """
    Find similar cars at a specific dealer when the requested model is not available.

    Args:
        model_name (str): The original model name that was requested
        dealer_name (str, optional): Specific dealer name to search at
        new_or_used (str, optional): Whether the car is "new" or "used"
        car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV")

    Returns:
        str: JSON string containing similar car recommendations
    """
    try:
        car_api = MockCarSearchAPI()

        # Convert empty strings to None for optional parameters
        dealer_name = dealer_name if dealer_name else None
        new_or_used = new_or_used if new_or_used else None
        car_type = car_type if car_type else None

        result = car_api.find_similar_cars(
            model_name=model_name,
            dealer_name=dealer_name,
            new_or_used=new_or_used,
            car_type=car_type,
        )
        return result
    except Exception as e:
        return json.dumps({"error": f"Similar cars search failed: {str(e)}"})


def get_dealer_recommendations_tool(
    model_name: str,
    new_or_used: Optional[str] = None,
    car_type: Optional[str] = None,
) -> str:
    """
    Get dealer recommendations for a specific car model.

    Args:
        model_name (str): Specific model name to search for
        new_or_used (str, optional): Whether the car is "new" or "used"
        car_type (str, optional): The type of car (e.g., "compact SUV", "sedan", "EV")

    Returns:
        str: JSON string containing dealer recommendations
    """
    try:
        car_api = MockCarSearchAPI()

        # Convert empty strings to None for optional parameters
        new_or_used = new_or_used if new_or_used else None
        car_type = car_type if car_type else None

        result = car_api.get_dealer_recommendations(
            model_name=model_name,
            new_or_used=new_or_used,
            car_type=car_type,
        )
        return result
    except Exception as e:
        return json.dumps({"error": f"Dealer recommendations failed: {str(e)}"})


def finalize_purchase_tool(
    car_model: str,
    dealer_name: str,
    price: int,
    decision: str,
    user_response: str = "",
) -> str:
    """
    Finalize a car reservation decision when the user has made a choice.

    Args:
        car_model (str): The specific car model the user chose
        dealer_name (str): The dealer where the car is located
        price (int): The price of the car
        decision (str): User's decision - "reserve" or "decline"
        user_response (str, optional): The user's actual response text

    Returns:
        str: JSON string confirming the final decision
    """
    try:
        result = {
            "final_decision": decision,
            "car_model": car_model,
            "dealer_name": dealer_name,
            "price": price,
            "user_response": user_response,
            "decision_timestamp": "2024-01-01T00:00:00Z",  # In real implementation, use actual timestamp
            "task_complete": True,
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Purchase finalization failed: {str(e)}"})


class CarShoppingAgent:
    """An agent that handles car shopping requests with dealer availability and recommendations."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "car_shopping_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the car shopping agent."""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="car_shopping_agent",
            description=(
                "This agent helps users find specific cars at dealers, check availability, "
                "and provides recommendations for similar cars when the exact model isn't available. "
                "The agent can help users reserve cars at dealers."
            ),
            instruction="""
You are a car shopping assistant whose ultimate goal is to help users find and decide on a specific car at a specific dealer.

Your primary objective is to guide the user to make a final decision about reserving a specific car at a specific dealer.

## Workflow:

### 1. **Initial Request Analysis**
- Identify the specific car model the user wants
- Note if they mentioned a specific dealer
- Check if they specified new/used preference

### 2. **Search and Present Options**
- Use `check_car_availability_tool` to see if the exact car is available at their preferred dealer
- If they didn't specify a dealer, use `get_dealer_recommendations_tool` to find dealers with the car
- If the exact car isn't available, use `find_similar_cars_tool` to find alternatives

### 3. **Present Clear Options**
When you find cars, present them clearly with:
- Specific car model and year
- Exact dealer location
- Price
- Key features
- Condition (new/used)

### 4. **Guide to Decision**
After presenting options, you MUST ask the user to make a choice:
- "Which of these cars would you like to reserve?"
- "Would you like to proceed with reserving [specific car] at [specific dealer]?"
- "Are you interested in any of these options, or would you like me to look for something else?"

### 5. **Task Completion**
Your task is ONLY complete when:
- ✅ User decides to reserve a specific car at a specific dealer
- ✅ User explicitly decides not to reserve any car
- ❌ NOT complete when you just provide information or recommendations

### 6. **Finalizing the Decision**
When the user makes a clear decision, use the `finalize_purchase_tool`:
- **For Reservation**: Call `finalize_purchase_tool` with decision="reserve", car details, and user's response
- **For Decline**: Call `finalize_purchase_tool` with decision="decline" and user's response
- This tool signals that the task is complete and captures the final decision

## Guidelines:
- Always present specific cars at specific dealers with clear details
- After showing options, ask the user to choose one
- If user shows interest in multiple options, ask them to pick one
- If user wants to see more options, continue searching
- Be persistent in guiding them to a final decision
- Don't end the conversation just by providing information

## Example Conversations:
- User: "Do you have a 2024 Hyundai Tucson at Auto City Motors?"
  → Check availability, show results, then ask: "Would you like to reserve this 2024 Hyundai Tucson at Auto City Motors for $32,000?"

- User: "I want a Honda CR-V"
  → Get dealer recommendations, show options, then ask: "Which of these Honda CR-V options would you like to reserve?"

- User: "I'm looking for a compact SUV at Family Auto Hub"
  → Find similar cars, show options, then ask: "Are you interested in any of these compact SUVs at Family Auto Hub?"

Remember: Your goal is to help them make a final reservation decision, not just provide information.
            """,
            tools=[check_car_availability_tool, find_similar_cars_tool, get_dealer_recommendations_tool, finalize_purchase_tool],
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
            if structured_data.get("current_car_recommendation"):
                car_rec = structured_data["current_car_recommendation"]
                if car_rec.get("has_recommendation"):
                    context_parts.append(
                        f"Current recommendation: {car_rec.get('car_model')} at {car_rec.get('dealer')} for ${car_rec.get('price')}"
                    )
            if structured_data.get("similar_cars_recommendations"):
                similar = structured_data["similar_cars_recommendations"]
                if similar.get("has_alternatives"):
                    context_parts.append(
                        f"Similar cars available: {similar.get('similar_cars_count', 0)} alternatives found"
                    )
            if structured_data.get("dealer_recommendations"):
                dealers = structured_data["dealer_recommendations"]
                if dealers.get("has_dealer_recommendations"):
                    context_parts.append(
                        f"Dealer recommendations: {dealers.get('dealer_count', 0)} dealers found"
                    )

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


        # Track if the finalize_purchase_tool was called to determine true completion
        finalize_tool_called = False

        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            # Handle tool results and save structured car data to state
            if event.get_function_responses():
                tool_responses = event.get_function_responses()
                for response in tool_responses:
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

                        # Handle different tool responses
                        if response.name == "check_car_availability_tool":
                            if car_data.get("available") and car_data.get("cars"):
                                # Save the first available car as the primary recommendation
                                first_car = car_data["cars"][0]
                                structured_car_data = {
                                    "car_model": first_car.get("model"),
                                    "price": first_car.get("price"),
                                    "dealer": first_car.get("dealer_location"),
                                    "car_type": first_car.get("type"),
                                    "condition": first_car.get("new_or_used"),
                                    "features": first_car.get("features", []),
                                    "availability_status": "available",
                                    "total_available": car_data.get("count", 0),
                                    "has_recommendation": True,
                                }

                                print(f"Saving availability data to state: {structured_car_data}")

                                state_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "current_car_recommendation": structured_car_data
                                        }
                                    ),
                                )
                                await self._runner.session_service.append_event(
                                    session, state_event
                                )
                            else:
                                # Car not available
                                no_availability_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "current_car_recommendation": {
                                                "has_recommendation": False,
                                                "availability_status": "not_available",
                                                "message": car_data.get("message", "Car not available")
                                            }
                                        }
                                    ),
                                )
                                await self._runner.session_service.append_event(
                                    session, no_availability_event
                                )

                        elif response.name == "find_similar_cars_tool":
                            if car_data.get("similar_cars_available") and car_data.get("cars"):
                                # Save similar cars as alternatives
                                similar_cars_data = {
                                    "similar_cars": car_data["cars"],
                                    "similar_cars_count": car_data.get("count", 0),
                                    "has_alternatives": True,
                                }

                                print(f"Saving similar cars data to state: {similar_cars_data}")

                                state_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "similar_cars_recommendations": similar_cars_data
                                        }
                                    ),
                                )
                                await self._runner.session_service.append_event(
                                    session, state_event
                                )

                        elif response.name == "get_dealer_recommendations_tool":
                            if car_data.get("dealers_available") and car_data.get("dealers"):
                                # Save dealer recommendations
                                dealer_data = {
                                    "recommended_dealers": car_data["dealers"],
                                    "dealer_count": car_data.get("count", 0),
                                    "has_dealer_recommendations": True,
                                }

                                print(f"Saving dealer recommendations to state: {dealer_data}")

                                state_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "dealer_recommendations": dealer_data
                                        }
                                    ),
                                )
                                await self._runner.session_service.append_event(
                                    session, state_event
                                )

                        elif response.name == "finalize_purchase_tool":
                            if car_data.get("task_complete"):
                                # Mark that the finalize tool was called
                                finalize_tool_called = True

                                # Save final purchase decision
                                final_decision_data = {
                                    "final_decision": car_data.get("final_decision"),
                                    "car_model": car_data.get("car_model"),
                                    "dealer_name": car_data.get("dealer_name"),
                                    "price": car_data.get("price"),
                                    "user_response": car_data.get("user_response"),
                                    "decision_timestamp": car_data.get("decision_timestamp"),
                                    "task_complete": True,
                                }

                                print(f"Saving final decision to state: {final_decision_data}")

                                state_event = Event(
                                    author=self._agent.name,
                                    actions=EventActions(
                                        state_delta={
                                            "final_purchase_decision": final_decision_data
                                        }
                                    ),
                                )
                                await self._runner.session_service.append_event(
                                    session, state_event
                                )

                    except (json.JSONDecodeError, TypeError) as e:
                        print(
                            f"Error processing tool response: {e}, response: {response.response}"
                        )
                        pass

            response = ""
            if (
                event.content
                and event.content.parts
                and event.content.parts[0].text
            ):
                response = "\n".join(
                    [p.text for p in event.content.parts if p.text]
                )

            if event.is_final_response():
                yield {
                    "is_task_complete": True,
                    "finalize_tool_called": finalize_tool_called,
                    "content": response,
                    "session_id": session.id,
                }
