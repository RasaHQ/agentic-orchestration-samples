# Appointment Booking Assistant

This appointment booking assistant demonstrates key agentic orchestration patterns:

**Primary Use Case**: Shows how to use an agent to intelligently fill appointment slots
based on user preferences and constraints, leveraging an MCP server for appointment
scheduling.

**Direct Tool Integration**: Demonstrates calling tools directly within flows to book a
certain appointment slot.

**Supporting Features**: Contact management (add, list, remove) is included to simulate
realistic digressions from the main booking flow, showcasing how agents can handle
context switching and multi-task conversations.

## MCP Server

The appointment booking assistant includes an MCP (Model Context Protocol) server that
provides intelligent appointment scheduling capabilities. The MCP server can query
available appointment slots based on user preferences, automatically handle business
hours and scheduling constraints, and generate realistic appointment options.

For detailed information about the MCP server's capabilities, configuration, and
technical implementation, see the [MCP Server README](mcp_server/README.md).

## Setup

### Prerequisites
- Python 3.11 or 3.12
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

The OPENAI_API_KEY is required as we are using `gpt-4o` as the default LLM within
Rasa. If you switch to a different LLM (see
[documentation](https://rasa.com/docs/reference/config/components/llm-configuratio)),
the key might not be needed.

Make sure to save the `.env` file in the root of the `appointment-booking-assistant`
directory.

### Running the Assistant

To run the appointment booking assistant, follow these steps in order:

1. **Start the MCP server**

To start the MCP server, follow the instructions provided in the `mcp_server/README.md`
file located in the `mcp_server` directory.

2. **Start the action server**
   In a new terminal window (from the project root directory), run:
   ```bash
   rasa run actions
   ```

3. **Train the Rasa model**
   In another terminal (from the project root), train the assistant:
   ```bash
   rasa train
   ```

4. **Run the assistant in interactive mode**
   Still in the project root, start the assistant:
   ```bash
   rasa inspect
   ```
   This will launch an interactive shell where you can chat with the assistant.

**Note:**
- Make sure your `.env` file is set up with the required API keys before starting.
- The first two step should be run in a separate terminal so all services remain active.
