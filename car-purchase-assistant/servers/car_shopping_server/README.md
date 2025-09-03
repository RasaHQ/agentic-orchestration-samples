# A2A Car Shopping Server

A standalone A2A (Agent-to-Agent) server that provides car shopping capabilities
using a mock car database to help users find vehicles based on their preferences.

## What This A2A Server Does

This A2A server acts as a **car shopping assistant** that helps users find and reserve vehicles by:

- **Checking car availability** at specific dealers for exact model matches
- **Finding similar cars** when the requested model isn't available at a preferred dealer
- **Getting dealer recommendations** for specific car models across multiple dealers
- **Facilitating car reservations** (not purchases) at dealers
- **Guiding users to final decisions** about which car to reserve at which dealer
- **Managing search sessions** to maintain context and improve user experience
- **Returning structured data** about found vehicles including pricing, features, and dealer locations

## Tools and Capabilities

### `check_car_availability_tool`
Checks if a specific car model is available at a specific dealer.

**Parameters:**
- `model_name` (string, required): Specific model name to search for (e.g., "Tucson", "CR-V", "Camry")
- `dealer_name` (string, optional): Specific dealer name to check
- `new_or_used` (string, optional): Whether the car is "new" or "used"
- `car_type` (string, optional): The type of car (e.g., "compact SUV", "sedan", "EV")

**Returns:**
JSON formatted response containing availability results including:
- `available`: Boolean indicating if the car is available
- `cars`: Array of matching cars with details
- `count`: Number of available cars found

### `find_similar_cars_tool`
Finds similar cars at a specific dealer when the requested model is not available.

**Parameters:**
- `model_name` (string, required): The original model name that was requested
- `dealer_name` (string, optional): Specific dealer name to search at
- `new_or_used` (string, optional): Whether the car is "new" or "used"
- `car_type` (string, optional): The type of car (e.g., "compact SUV", "sedan", "EV")

**Returns:**
JSON formatted response containing similar car recommendations including:
- `similar_cars_available`: Boolean indicating if similar cars were found
- `cars`: Array of similar cars with details
- `count`: Number of similar cars found

### `get_dealer_recommendations_tool`
Gets dealer recommendations for a specific car model.

**Parameters:**
- `model_name` (string, required): Specific model name to search for
- `new_or_used` (string, optional): Whether the car is "new" or "used"
- `car_type` (string, optional): The type of car (e.g., "compact SUV", "sedan", "EV")

**Returns:**
JSON formatted response containing dealer recommendations including:
- `dealers_available`: Boolean indicating if dealers were found
- `dealers`: Array of dealers with the requested car
- `count`: Number of dealers found

### `finalize_purchase_tool`
Finalizes a car reservation decision when the user has made a choice.

**Parameters:**
- `car_model` (string, required): The specific car model the user chose
- `dealer_name` (string, required): The dealer where the car is located
- `price` (int, required): The price of the car
- `decision` (string, required): User's decision - "reserve" or "decline"
- `user_response` (string, optional): The user's actual response text

**Returns:**
JSON formatted response confirming the final decision including:
- `final_decision`: The user's decision ("reserve" or "decline")
- `car_model`: The chosen car model
- `dealer_name`: The selected dealer
- `price`: The car price
- `task_complete`: Boolean indicating the task is complete

## Agent Workflow

The car shopping agent follows a structured workflow to help users find and reserve cars:

### 1. **Initial Request Analysis**
- Identifies the specific car model the user wants
- Notes if they mentioned a specific dealer
- Checks if they specified new/used preference

### 2. **Search and Present Options**
- Uses `check_car_availability_tool` to see if the exact car is available at their preferred dealer
- If they didn't specify a dealer, uses `get_dealer_recommendations_tool` to find dealers with the car
- If the exact car isn't available, uses `find_similar_cars_tool` to find alternatives

### 3. **Present Clear Options**
When cars are found, presents them clearly with:
- Specific car model and year
- Exact dealer location
- Price
- Key features
- Condition (new/used)

### 4. **Guide to Decision**
After presenting options, asks the user to make a choice:
- "Which of these cars would you like to reserve?"
- "Would you like to proceed with reserving [specific car] at [specific dealer]?"
- "Are you interested in any of these options, or would you like me to look for something else?"

### 5. **Task Completion**
The task is only complete when:
- ✅ User decides to reserve a specific car at a specific dealer
- ✅ User explicitly decides not to reserve any car
- ❌ NOT complete when just providing information or recommendations

### 6. **Finalizing the Decision**
When the user makes a clear decision, uses the `finalize_purchase_tool`:
- **For Reservation**: Calls `finalize_purchase_tool` with decision="reserve", car details, and user's response
- **For Decline**: Calls `finalize_purchase_tool` with decision="decline" and user's response
- This tool signals that the task is complete and captures the final decision

## Environment Variables

- `GOOGLE_API_KEY`: Required. API key for Google's Gemini AI model.
- `GOOGLE_GENAI_USE_VERTEXAI`: Optional. Set to "TRUE" to use Vertex AI instead of direct API.

## Server Configuration

- **Default Host**: localhost
- **Default Port**: 10002
- **Model**: gemini-2.0-flash-001
- **Transport**: HTTP via A2A protocol


## Setup Instructions

Follow these steps to get the A2A server up and running:

### Requirements

- **Python 3.10 or higher** is required.

### Create and Activate a Virtual Environment

```bash
python -m venv a2a-server-venv
source a2a-server-venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start the server

Make sure your `GOOGLE_API_KEY` is set.

```bash
python car_shopping_server.py
```

Keep the terminal open.


