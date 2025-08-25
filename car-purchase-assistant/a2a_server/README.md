# A2A Car Shopping Server

A standalone A2A (Agent-to-Agent) server that provides car shopping capabilities
using a mock car database to help users find vehicles based on their preferences.

## What This A2A Server Does

This A2A server acts as a **car shopping assistant** that helps users find vehicles by:

- **Searching through a mock car database** containing various vehicle models and specifications
- **Filtering cars based on user criteria** including type, price range, new/used preference, and model name
- **Providing car recommendations** with detailed information about matching vehicles
- **Managing search sessions** to maintain context and improve user experience
- **Returning structured data** about found vehicles including pricing, features, and dealer locations

## Tools and Capabilities

### `search_cars_tool`
Searches for cars based on user criteria using the mock car search API.

**Parameters:**
- `car_type` (string, optional): The type of car (e.g., "compact SUV", "sedan", "EV")
- `min_price` (int, optional): Minimum price range (default: 10000)
- `max_price` (int, optional): Maximum price range (default: 60000)
- `new_or_used` (string, optional): Whether the car is "new" or "used"
- `model_name` (string, optional): Specific model name to search for (e.g., "Tucson", "CR-V")

**Returns:**
JSON formatted response containing car details including:
- `chosen_car_model`: The matching car model
- `chosen_car_price`: The car's price
- `dealer_location`: Location where the car is available
- `features`: List of car features
- `car_type`: Type of vehicle
- `condition`: Whether new or used
- `year`: Model year

## Environment Variables

- `GOOGLE_API_KEY`: Required. API key for Google's Gemini AI model.
- `GOOGLE_GENAI_USE_VERTEXAI`: Optional. Set to "TRUE" to use Vertex AI instead of direct API.

## Server Configuration

- **Default Host**: localhost
- **Default Port**: 10002
- **Model**: gemini-2.0-flash-001
- **Transport**: HTTP via A2A protocol


## Setup Instructions

Follow these steps to get the MCP server up and running:

### Requirements

- **Python 3.10 or higher** is required.

### Create and Activate a Virtual Environment

```bash
python -m venv a2a-server-venv
source activate a2a-server-venv/bin/activate
```

### Install FastMCP & Tavily Python

```bash
pip install -r requirements.txt
```

### Start the server

Make sure your `GOOGLE_API_KEY` is set.

```bash
python car_shopping_server.py
```

Keep the terminal open.


