# Car Purchase Assistant

This car purchase assistant demonstrates advanced agentic orchestration patterns for
complex, multi-phase workflows:

**Primary Use Case**: Shows how to orchestrate a specialized agent (research) through
a single conversational interface, demonstrating end-to-end workflow management.

**Context-Aware Orchestration**: Demonstrates how to maintain context across different
phases, with structured data flow between research results, shopping decisions, and
financing options.

**Supporting Features**: Contact management capabilities are included to simulate
realistic digressions.

## MCP Server

The car purchase assistant uses an MCP (Model Context Protocol) server to provide
real-time car research capabilities. The MCP server connects the assistant to external
search APIs, allowing it to retrieve up-to-date information for car research and
decision-making.

For setup and technical details, see the [MCP Server README](mcp_server/README.md).

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

1. **Start the MCP server**
   Open a terminal and start the MCP server.

   ```bash
   python -m mcp_server
   ```
   Leave this terminal open, as the MCP server must keep running.

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
- The first two steps should be run in separate terminals so all services remain active.
