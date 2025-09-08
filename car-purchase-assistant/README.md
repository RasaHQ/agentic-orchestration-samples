# Car Purchase Assistant

This car purchase assistant demonstrates advanced agentic orchestration patterns for
complex, multi-phase workflows:

**Primary Use Case**: Shows how to orchestrate specialized agents (research, shopping, appointment booking)
through a single conversational interface, demonstrating end-to-end workflow management.

**Context-Aware Orchestration**: Demonstrates how to maintain context across different
phases, with structured data flow between research results, shopping decisions, financing options, and appointment scheduling.

**Comprehensive Workflow**: The assistant handles the complete car purchase journey from initial research to final appointment booking, including financial assessment and loan calculations.

## Architecture Overview

The car purchase assistant uses multiple specialized servers and agents to provide a comprehensive car buying experience:

### MCP Servers

**Web Search Server**: Provides real-time car research capabilities by connecting to external search APIs, allowing the assistant to retrieve up-to-date information for car research and decision-making.

**Appointment Booking Server**: Handles appointment scheduling with dealers, providing flexible scheduling options and availability management.

For setup and technical details, see:
- [Web Search MCP Server README](servers/tavily_search_server/README.md)
- [Appointment Booking MCP Server README](servers/appointment_booking_server/README.md)

### A2A Server

**Car Shopping Server**: Powers the car shopping and purchase workflow. This server provides structured car search and recommendation capabilities, enabling the assistant to help users find vehicles, check availability at dealers, and facilitate car reservations.

For more details on its features and configuration, see the [Car Shopping A2A Server README](servers/car_shopping_server/README.md).

### Sub-Agents

The assistant includes several specialized sub-agents:

- **Research Agent**: Handles web-based car research using the Tavily search API using the *Web Search Server*.
- **Shopping Agent**: Manages car shopping workflows through the A2A car shopping server using the *Car Shopping Server*.
- **Appointment Selector**: Facilitates appointment booking with dealers using the *Appointment Booking Server*.

## Workflow Capabilities

The car purchase assistant provides a comprehensive end-to-end car buying experience with the following capabilities:

### 1. Car Research
- **Web-based research**: Uses the Tavily search API to find current information about car models, reviews, and specifications
- **Intelligent recommendations**: Provides personalized car suggestions based on user preferences
- **Real-time data**: Accesses up-to-date pricing, features, and availability information

### 2. Car Shopping
- **Dealer availability**: Checks if specific cars are available at specific dealers
- **Similar car recommendations**: Suggests alternatives when the exact model isn't available
- **Dealer recommendations**: Finds dealers that stock the desired car models
- **Car reservations**: Facilitates the reservation of cars at dealers (not purchases)

### 3. Financial Assessment
- **Credit score checking**: Validates user identity and retrieves credit scores
- **Loan affordability**: Calculates debt-to-income ratios and determines loan affordability
- **Existing loan analysis**: Reviews current loan obligations
- **Account balance checking**: Verifies available funds
- **Loan calculations**: Provides detailed financing options with different terms and down payments

### 4. Appointment Scheduling
- **Flexible scheduling**: Books appointments with dealers based on user preferences
- **Availability management**: Handles date and time constraints with intelligent defaults
- **Confirmation workflow**: Provides confirmation and cancellation options

## Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Installation

**Install dependencies** from the `pyproject.toml`:
```bash
pip install -e .
```

### Create .env file

Copy the example environment file and fill in your API keys:

1. **Copy the example file to create your own `.env` file:**
   ```bash
   cp .env_example .env
   ```

2. **Open the `.env` file** in a text editor and fill in the required values:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `RASA_PRO_LICENSE`: Your Rasa Pro license key
   - `TAVILY_API_KEY`: Your Tavily API key for web search functionality
   - `GOOGLE_API_KEY`: Your Google API key for Gemini integration

The OPENAI_API_KEY is required as we are using `gpt-4o` as the default LLM within
Rasa. If you switch to a different LLM (see
[documentation](https://rasa.com/docs/reference/config/components/llm-configuratio)),
the key might not be needed.

Make sure to save the `.env` file in the root of the `car-purchase-assistant`
directory.

### Running the Assistant

To run the car purchase assistant, follow these steps in order:

1. **Start the Web Search MCP server**

   To start the web search MCP server, follow the instructions provided in the [Web Search MCP Server README](servers/tavily_search_server/README.md).

2. **Start the Appointment Booking MCP server**

   To start the appointment booking MCP server, follow the instructions provided in the [Appointment Booking MCP Server README](servers/appointment_booking_server/README.md).

3. **Start the Car Shopping A2A server**

   To start the car shopping A2A server, follow the instructions provided in the [Car Shopping A2A Server README](servers/car_shopping_server/README.md).

4. **Train the Rasa model**
   In another terminal (from the project root), train the assistant:
   ```bash
   rasa train
   ```

5. **Run the assistant in interactive mode**
   Still in the project root, start the assistant:
   ```bash
   rasa inspect
   ```
   This will launch an interactive shell where you can chat with the assistant.

**Note:**
Make sure your `.env` file is set up with the required API keys before starting. You'll need:
- `TAVILY_API_KEY` for web search functionality
- `GOOGLE_API_KEY` for the car shopping A2A server
- `OPENAI_API_KEY` for the main Rasa assistant
- `RASA_PRO_LICENSE` for Rasa Pro
