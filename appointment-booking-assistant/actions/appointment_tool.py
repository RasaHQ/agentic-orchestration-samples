from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import json
from openai import OpenAI
import os
from datetime import datetime, timedelta
import re
import logging

# Import the existing appointment action
from actions.schedule_appointment import ActionQueryAvailableAppointments

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Defensive import check
try:
    from rasa_sdk.events import SlotSet
    logger.info(f"SlotSet imported successfully: {SlotSet}")
except Exception as e:
    logger.error(f"Failed to import SlotSet: {e}")
    SlotSet = None


class AppointmentTool:
    """
    Wrapper that converts ActionQueryAvailableAppointments into a callable tool
    """

    def __init__(self):
        self.appointment_action = ActionQueryAvailableAppointments()

    def call(self, appointment_params: Dict[str, Any], tracker: Tracker, dispatcher: CollectingDispatcher, domain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the appointment query action with extracted parameters using real tracker and domain
        """
        try:
            # Create a tracker wrapper that overlays LLM-extracted values over real tracker
            tracker_wrapper = TrackerWrapper(tracker, appointment_params)

            # Run the appointment action with real domain
            events = self.appointment_action.run(dispatcher, tracker_wrapper, domain)
            # Extract available slots from the returned events
            available_slots = []
            for event in events:
                if isinstance(event, dict) and event.get("name") == "available_appointment_slots":
                    available_slots = event.get("value") or []  # ✅ Only extracts from correct event
                    break  # ✅ Stops when found

            return {
                "success": True,
                "available_slots": available_slots,
                "total_slots": len(available_slots),
                "used_params": appointment_params
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "available_slots": []
            }


class TrackerWrapper:
    """
    Wrapper that overlays LLM-extracted slot values over the real Rasa tracker
    """

    def __init__(self, real_tracker: Tracker, extracted_slot_values: Dict[str, Any]):
        self.real_tracker = real_tracker
        self.extracted_values = extracted_slot_values

    def get_slot(self, slot_name: str) -> Any:
        # First check if we have an LLM-extracted value for this slot
        if slot_name in self.extracted_values:
            return self.extracted_values[slot_name]
        # Fall back to the real tracker
        return self.real_tracker.get_slot(slot_name)

    def __getattr__(self, name):
        # Delegate all other attributes to the real tracker
        return getattr(self.real_tracker, name)


class LLMAppointmentAgent:
    """
    LLM-powered agent that:
    1. Extracts appointment preferences from natural language
    2. Calls the appointment tool with structured data
    3. Handles user selection from presented options
    4. Returns the selected appointment slot
    5. Maintains conversation history for preference changes and negotiation
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

        self.appointment_tool = AppointmentTool()
        self.current_available_slots = []  # Store current options

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """
        Define the appointment tool function for the LLM
        """
        return [
            {
                "name": "query_available_appointments",
                "description": "Query available appointment slots using extracted user preferences. All dates must be in dd/mm/yyyy format, times in HH:MM format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_availability_start_date": {
                            "type": "string",
                            "description": "Start date for availability in dd/mm/yyyy format. Use 'any' if not specified."
                        },
                        "user_availability_end_date": {
                            "type": "string",
                            "description": "End date for availability in dd/mm/yyyy format. Use 'any' if not specified."
                        },
                        "user_availability_start_time": {
                            "type": "string",
                            "description": "Start time for availability in HH:MM format (24-hour). Use 'any' if not specified."
                        },
                        "user_availability_end_time": {
                            "type": "string",
                            "description": "End time for availability in HH:MM format (24-hour). Use 'any' if not specified."
                        },
                        "preferred_doctor": {
                            "type": "string",
                            "description": "Name of preferred doctor. Use 'any' if not specified."
                        },
                        "non_available_days": {
                            "type": "string",
                            "description": "Dates user is NOT available, separated by ';' in dd/mm/yyyy format. Use 'any' if none specified."
                        }
                    },
                    "required": ["user_availability_start_date", "user_availability_end_date", "user_availability_start_time", "user_availability_end_time", "preferred_doctor", "non_available_days"]
                }
            },
            {
                "name": "select_appointment_slot",
                "description": "Select a specific appointment slot from the currently available options. IMPORTANT: You can ONLY select from the exact slots listed in the current available options. Do not create or suggest new appointment times.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selected_slot": {
                            "type": "string",
                            "description": "The exact appointment slot string (in format dd/mm/yyyy ; HH:MM) that the user selected from the available options. Must match exactly one of the currently available slots."
                        }
                    },
                    "required": ["selected_slot"]
                }
            }
        ]

    def select_appointment_slot(self, selected_slot: str) -> Dict[str, Any]:
        """
        Validate the LLM's selected appointment slot
        """
        logger.info(f"VALIDATING SLOT SELECTION: {selected_slot}")
        logger.info(f"CURRENT AVAILABLE SLOTS: {self.current_available_slots}")

        if not self.current_available_slots:
            return {
                "success": False,
                "error": "No appointment options are currently available to select from",
                "selected_slot": None
            }

        # Simply validate that the LLM selected a valid slot
        if selected_slot in self.current_available_slots:
            logger.info(f"SLOT SELECTION VALID: {selected_slot}")
            return {
                "success": True,
                "selected_slot": selected_slot,
                "message": f"Successfully selected appointment: {selected_slot}"
            }
        else:
            logger.error(f"SLOT SELECTION INVALID: {selected_slot}")
            logger.error(f"AVAILABLE OPTIONS WERE: {self.current_available_slots}")
            return {
                "success": False,
                "error": f"Invalid slot selection: {selected_slot}. Available options are: {', '.join(self.current_available_slots)}",
                "selected_slot": None
            }

    def _extract_conversation_history(self, tracker: Tracker) -> List[Dict[str, str]]:
        """
        Extract conversation history from Rasa tracker and format for LLM
        """
        history = []

        try:
            # Get all events from tracker
            events = tracker.events

            logger.info(f"TOTAL TRACKER EVENTS: {len(events)}")

            for i, event in enumerate(events):
                # logger.info(f"EVENT {i}: {event}")
                # logger.info(f"EVENT {i} TYPE: {type(event)}")
                # if hasattr(event, '__dict__'):
                    # logger.info(f"EVENT {i} DICT: {event.__dict__}")

                # Try different approaches to extract user messages
                event_type = None
                event_text = None

                # Method 1: Check if it's a dictionary
                if isinstance(event, dict):
                    event_type = event.get('event')
                    event_text = event.get('text')
                    # logger.info(f"DICT EVENT {i}: type={event_type}, text={event_text}")

                # Method 2: Check if it has attributes
                elif hasattr(event, 'event'):
                    event_type = getattr(event, 'event', None)
                    event_text = getattr(event, 'text', None)
                    # logger.info(f"ATTR EVENT {i}: type={event_type}, text={event_text}")

                # Method 3: Check specific event types
                elif hasattr(event, 'type_name'):
                    event_type = getattr(event, 'type_name', None)
                    event_text = getattr(event, 'text', None)
                    # logger.info(f"TYPE_NAME EVENT {i}: type={event_type}, text={event_text}")

                # Extract messages based on event type
                if event_type == 'user' and event_text and event_text.strip():
                    # Skip the current message as it will be added separately
                    if event_text != tracker.latest_message.get('text', ''):
                        history.append({"role": "user", "content": event_text})
                        # logger.info(f"ADDED USER MESSAGE: {event_text}")

                elif event_type == 'bot' and event_text and event_text.strip():
                    history.append({"role": "assistant", "content": event_text})
                    # logger.info(f"ADDED BOT MESSAGE: {event_text}")

                # Also try to extract from action events or other message types
                elif hasattr(event, 'text') and getattr(event, 'text'):
                    text = getattr(event, 'text')
                    # Try to determine if this is a bot message based on context
                    if text and text.strip() and text != tracker.latest_message.get('text', ''):
                        # If we can't determine type, assume it's a bot message if it's not the current user message
                        history.append({"role": "assistant", "content": text})
                        # logger.info(f"ADDED GENERIC MESSAGE: {text}")

        except Exception as e:
            # logger.error(f"Error extracting conversation history: {e}")
            import traceback
            logger.error(f"TRACEBACK: {traceback.format_exc()}")
            logger.info("Continuing without conversation history")

        logger.info(f"EXTRACTED CONVERSATION HISTORY: {len(history)} messages")
        for i, msg in enumerate(history):
            logger.info(f"HISTORY {i}: {msg['role']}: {msg['content'][:100]}...")

        return history

    def process_message(self, user_message: str, tracker: Tracker, dispatcher: CollectingDispatcher, domain: Dict[str, Any], current_slots: List[str] = None) -> Dict[str, Any]:
        """
        Process user message and return response with any selected appointment slot
        Returns: {
            "response": str,
            "selected_slot": str or None,
            "conversation_complete": bool
        }
        """
        if not self.client:
            return {
                "response": "Sorry, I need an OpenAI API key to help you. Please configure OPENAI_API_KEY.",
                "selected_slot": None,
                "conversation_complete": True
            }

        # Update current available slots if provided
        if current_slots:
            logger.info(f"UPDATING CURRENT AVAILABLE SLOTS FROM: {self.current_available_slots}")
            logger.info(f"UPDATING CURRENT AVAILABLE SLOTS TO: {current_slots}")
            self.current_available_slots = current_slots
        else:
            logger.info(f"NO CURRENT SLOTS PROVIDED, KEEPING: {self.current_available_slots}")

        current_date = datetime.now().strftime("%d/%m/%Y")
        current_time = datetime.now().strftime("%H:%M")

        # Build context about available slots for the LLM
        slots_context = ""
        if self.current_available_slots:
            slots_context = f"\n\nCurrently available appointment options:\n"
            for i, slot in enumerate(self.current_available_slots, 1):
                slots_context += f"{i}. {slot}\n"
            slots_context += "\nIMPORTANT: You can ONLY select from these exact slots listed above. Do not suggest or select any other appointment times."
            slots_context += "\nIf user is selecting from these options, use the select_appointment_slot function with the EXACT slot string."

        system_prompt = f"""You are a medical appointment booking assistant. Your job is to:

1. Extract appointment preferences from user's natural language and query available slots
2. When appointment options are available, help users select one
3. Present results clearly and handle the conversation flow
4. Handle preference changes and negotiation - users can modify their requirements

Current date: {current_date}
Current time: {current_time}

CRITICAL RULES:
- You can ONLY book appointments that are in the currently available slots list
- Never suggest or book appointment times that are not in the available options
- Always use the EXACT slot string format when selecting appointments
- If no suitable slots are available, suggest querying for different criteria
- Always show the earliest 3 available appointment slots from all the available slots. Don't show any more. Once the user updates their preference, you can use the available slots to find the best ones matching.

IMPORTANT FORMAT REQUIREMENTS:
- Dates: dd/mm/yyyy format (e.g., 15/07/2025)
- Times: HH:MM format in 24-hour time (e.g., 14:30 for 2:30 PM)  
- Use "any" for unspecified preferences

Date conversion examples:
- "tomorrow" → calculate and use dd/mm/yyyy
- "next Tuesday" → find next Tuesday's date in dd/mm/yyyy
- "this week" → use current date to end of week
- "afternoon" → 12:00 to 17:00
- "morning" → 09:00 to 12:00

When user mentions appointment needs, extract preferences and call query_available_appointments.
When user is choosing from presented options, call select_appointment_slot with EXACT slot string.
When user changes search preferences, query new appointments with updated criteria.{slots_context}"""

        # Build conversation history from tracker
        messages = [{"role": "system", "content": system_prompt}]

        # Extract conversation history from Rasa tracker
        conversation_history = self._extract_conversation_history(tracker)
        messages.extend(conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        logger.info("=== LLM CALL 1: Initial Request ===")
        logger.info(f"USER MESSAGE: {user_message}")
        logger.info(f"CONVERSATION HISTORY LENGTH: {len(conversation_history)} messages")
        logger.info(f"FULL MESSAGES: {json.dumps(messages, indent=2)}")

        try:
            # First LLM call with function calling capability
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                functions=self.get_function_definitions(),
                function_call="auto",
                temperature=0.3,
                max_tokens=400
            )

            message = response.choices[0].message

            logger.info("=== LLM RESPONSE 1 ===")
            logger.info(f"MESSAGE CONTENT: {message.content}")
            logger.info(f"HAS FUNCTION CALL: {bool(message.function_call)}")
            if message.function_call:
                logger.info(f"FUNCTION NAME: {message.function_call.name}")
                logger.info(f"FUNCTION ARGUMENTS: {message.function_call.arguments}")

            # Check if LLM wants to call a function
            if message.function_call:
                function_name = message.function_call.name

                try:
                    function_args = json.loads(message.function_call.arguments)
                    logger.info(f"PARSED FUNCTION ARGS: {json.dumps(function_args, indent=2)}")
                except json.JSONDecodeError as e:
                    logger.error(f"FAILED TO PARSE FUNCTION ARGUMENTS: {e}")
                    return {
                        "response": "Sorry, I had trouble understanding your request. Could you please rephrase?",
                        "selected_slot": None,
                        "conversation_complete": False
                    }

                if function_name == "query_available_appointments":
                    logger.info("=== CALLING APPOINTMENT TOOL ===")
                    logger.info(f"TOOL INPUT: {json.dumps(function_args, indent=2)}")

                    # Call appointment tool with extracted parameters, real tracker and domain
                    tool_result = self.appointment_tool.call(function_args, tracker, dispatcher, domain)

                    logger.info(f"TOOL RESULT: {json.dumps(tool_result, indent=2)}")

                    # Store the available slots
                    self.current_available_slots = tool_result.get("available_slots", [])

                    # Add function call and result to conversation
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": message.function_call.name,
                            "arguments": message.function_call.arguments
                        }
                    })
                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(tool_result)
                    })

                    logger.info("=== LLM CALL 2: Follow-up after tool call ===")
                    logger.info(f"UPDATED MESSAGES COUNT: {len(messages)}")

                    # Get LLM's response after seeing the tool results
                    follow_up_response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=400
                    )

                    logger.info("=== LLM RESPONSE 2 ===")
                    logger.info(f"FINAL RESPONSE CONTENT: {follow_up_response.choices[0].message.content}")

                    return {
                        "response": follow_up_response.choices[0].message.content,
                        "selected_slot": None,
                        "conversation_complete": False
                    }

                elif function_name == "select_appointment_slot":
                    logger.info("=== CALLING SELECTION TOOL ===")
                    logger.info(f"SELECTION INPUT: {json.dumps(function_args, indent=2)}")
                    logger.info(f"AVAILABLE SLOTS: {self.current_available_slots}")

                    # Handle appointment selection - LLM already parsed the selection
                    selected_slot = function_args["selected_slot"]
                    selection_result = self.select_appointment_slot(selected_slot)

                    logger.info(f"SELECTION RESULT: {json.dumps(selection_result, indent=2)}")

                    # Add function call and result to conversation
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": message.function_call.name,
                            "arguments": message.function_call.arguments
                        }
                    })
                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(selection_result)
                    })

                    logger.info("=== LLM CALL 3: Follow-up after selection ===")
                    logger.info(f"UPDATED MESSAGES COUNT: {len(messages)}")

                    # Get LLM's final response
                    follow_up_response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=400
                    )

                    logger.info("=== LLM RESPONSE 3 ===")
                    logger.info(f"FINAL SELECTION RESPONSE: {follow_up_response.choices[0].message.content}")
                    logger.info(f"SELECTED SLOT: {selection_result.get('selected_slot')}")
                    logger.info(f"CONVERSATION COMPLETE: {bool(selection_result.get('selected_slot'))}")

                    return {
                        "response": follow_up_response.choices[0].message.content,
                        "selected_slot": selection_result.get("selected_slot"),
                        "conversation_complete": bool(selection_result.get("selected_slot"))
                    }

            # Return direct response if no function call needed
            logger.info("=== DIRECT RESPONSE (No Function Call) ===")
            logger.info(f"DIRECT RESPONSE CONTENT: {message.content}")

            return {
                "response": message.content,
                "selected_slot": None,
                "conversation_complete": False
            }

        except Exception as e:
            logger.error(f"=== LLM ERROR ===")
            logger.error(f"ERROR: {str(e)}")
            logger.error(f"ERROR TYPE: {type(e).__name__}")

            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "selected_slot": None,
                "conversation_complete": True
            }


class ActionLLMAppointmentWrapper(Action):
    """
    Rasa action that uses LLM to:
    1. Extract appointment preferences from natural language
    2. Query available slots
    3. Handle user selection from options
    4. Store the final selected appointment slot
    5. Maintain conversation history for preference changes
    """

    def name(self) -> Text:
        return "llm_appointment_wrapper"

    def __init__(self):
        self.llm_agent = LLMAppointmentAgent()

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        logger.info("=== RASA ACTION STARTED ===")

        # Get user's latest message
        user_message = tracker.latest_message.get("text", "")
        logger.info(f"USER MESSAGE: {user_message}")

        if not user_message:
            logger.info("No user message provided, sending help prompt")
            dispatcher.utter_message(text="How can I help you book an appointment?")
            return []

        # Get current available slots from tracker if any
        current_slots = tracker.get_slot("available_appointment_slots") or []
        logger.info(f"CURRENT AVAILABLE SLOTS FROM TRACKER: {current_slots}")

        # Process through LLM agent with real tracker and domain
        logger.info("=== CALLING LLM AGENT ===")
        result = self.llm_agent.process_message(user_message, tracker, dispatcher, domain, current_slots)

        logger.info("=== LLM AGENT RESULT ===")
        logger.info(f"RESPONSE: {result['response']}")
        logger.info(f"SELECTED SLOT: {result['selected_slot']}")
        logger.info(f"CONVERSATION COMPLETE: {result['conversation_complete']}")

        # Send response to user
        dispatcher.utter_message(text=result["response"])

        # Prepare events to return
        events = []

        # Update available slots if we have new ones
        if self.llm_agent.current_available_slots:
            logger.info(f"UPDATING AVAILABLE SLOTS: {self.llm_agent.current_available_slots}")
            if SlotSet:
                events.append(SlotSet("available_appointment_slots", self.llm_agent.current_available_slots))
            else:
                logger.error("SlotSet not available, cannot update slots")

        # If user selected an appointment, store it
        if result["selected_slot"]:
            logger.info(f"STORING SELECTED APPOINTMENT: {result['selected_slot']}")
            if SlotSet:
                events.append(SlotSet("selected_appointment_slot", result["selected_slot"]))
                events.append(SlotSet("booking_complete", True))
                # Clear available slots since user has made selection
                events.append(SlotSet("available_appointment_slots", []))
            else:
                logger.error("SlotSet not available, cannot update slots")

        event_descriptions = []
        for e in events:
            if hasattr(e, 'name'):
                event_descriptions.append(f'{type(e).__name__}({getattr(e, "name", "no_name")}: {getattr(e, "value", "no_value")})')
            else:
                event_descriptions.append(str(e))

        logger.info(f"RETURNING EVENTS: {event_descriptions}")
        logger.info("=== RASA ACTION COMPLETED ===")

        return events
