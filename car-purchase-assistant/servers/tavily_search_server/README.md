# MCP Web Search Server

A standalone MCP (Model Context Protocol) server that can provide:
- (Default mode) Either, web search capabilities via the [Tavily API](https://www.tavily.com/).
- Or, static mock car search results via a [mock dataset](./tools/mock_data.json).

## What This MCP Server Does

This MCP server acts as a bridge between AI agents and real-time or mock web search functionality. It:

- **Exposes web search as a tool** that agents can call to get information
- **Handles API communication*** with Tavily's search service
- **Formats search results** in a structured way that agents can easily process
- **Manages rate limiting and error handling*** for the search API
- **Provides a standardized interface** for agents to access web search capabilities

*Not applicable if using mock dataset.

## Tools

### `tavily_search`

Search the web using Tavily to get current information.

**Parameters:**
- `query` (string, required): The search query
- `max_results` (integer, optional): Maximum number of results (1-10, default: 3)
- `include_answer` (boolean, optional): Whether to include a direct answer (default: true)

**Returns:**
JSON formatted search results including titles, URLs, content snippets, and optionally a direct answer.

## Testing with Mock Data

The Tavily search server includes a mock mode for testing and development purposes. This feature allows you to test the assistant's orchestration logic without requiring external API access.

### Purpose

The mock mode serves several important purposes:

- **Development Testing**: Test the assistant's flow management and conversation patterns without API dependencies
- **CI/CD Pipelines**: Enable automated testing in environments without API keys
- **Cost Control**: Avoid API usage costs during development and testing
- **More Consistent Results**: Ensure more reproducible test outcomes across different environments

### Mock Data Structure

The mock data is stored in [`mock_data.json`](./tools/mock_data.json) and contains static car research results that simulate real web search responses. The dataset includes:

- **Car Reviews**: Detailed reviews of popular car models (Tesla Model 3, Honda Civic, etc.)
- **Comparisons**: Side-by-side comparisons of competing vehicles
- **Market Information**: Pricing, features, and availability data
- **Technical Specifications**: Performance metrics, fuel efficiency, and safety ratings

Each mock entry follows the same structure as real Tavily search results, ensuring seamless integration with the assistant's processing logic.

### Configuration

To enable mock mode, set the environment variable:

```bash
export MOCK_TAVILY_SEARCH=true
```

When mock mode is enabled:
- The server will use `mock_data.json` instead of making API calls to Tavily
- No `TAVILY_API_KEY` is required
- All search queries will return results from the static dataset
- The response format remains identical to real API responses

### When to Use Mock vs Real API

**Use Mock Mode For:**
- Development and testing of assistant logic
- E2E testing of conversation flows
- CI/CD pipeline execution
- Demonstrating assistant capabilities without Tavily API costs

**Use Real API For:**
- Production deployments
- Testing with live, up-to-date data
- Validating search result quality
- Performance testing with real Tavily API responses

### E2E Test Examples

The mock data is used in comprehensive E2E tests located in `e2e/car_research/`:

- **Happy Path Tests**: Verify successful car research workflows
- **Cancellation Tests**: Test user cancellation scenarios
- **Digression Tests**: Validate handling of topic changes during research

These tests ensure the assistant properly orchestrates the research flow using mock search results, validating the core orchestration logic without external dependencies.

## Usage

This server is designed to be used with MCP clients. It communicates via http using the MCP protocol.

## Environment Variables

- `TAVILY_API_KEY`: Required. Your Tavily API key for web search functionality.

Or
- `MOCK_TAVILY_SEARCH`: Required. If `MOCK_TAVILY_SEARCH=true`, then static mock dataset is used instead.


## Setup Instructions

Follow these steps to get the MCP server up and running:

### Requirements

- **Python 3.10 or higher** is required.

### Create and Activate a Virtual Environment

```bash
python -m venv mcp-server-venv
source mcp-server-venv/bin/activate
```

### Install FastMCP & Tavily Python

```bash
pip install -r requirements.txt
```

### Start the server

Make sure either `TAVILY_API_KEY` or `MOCK_TAVILY_SEARCH=true` is set.

```bash
python tavily_search_server.py
```

Keep the terminal open.
