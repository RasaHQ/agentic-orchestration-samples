# MCP Web Search Server

A standalone MCP (Model Context Protocol) server that provides web search capabilities via the Tavily API.

## What This MCP Server Does

This MCP server acts as a bridge between AI agents and real-time web search functionality. It:

- **Exposes web search as a tool** that agents can call to get current information
- **Handles API communication** with Tavily's search service
- **Formats search results** in a structured way that agents can easily process
- **Manages rate limiting and error handling** for the search API
- **Provides a standardized interface** for agents to access web search capabilities

## Setup

### Option 1: Using uv (Recommended)

1. Install dependencies:
```bash
uv sync
```

2. Set your Tavily API key:
```bash
export TAVILY_API_KEY=your_api_key_here
```

3. Run the server:
```bash
uv run .
```

### Option 2: Using pip (Alternative)

1. Install dependencies:
```bash
pip install -e .
```

2. Set your Tavily API key:
```bash
export TAVILY_API_KEY=your_api_key_here
```

3. Run the server:
```bash
python -m mcp_server
```

## Tools

### `tavily_search`

Search the web using Tavily to get current information.

**Parameters:**
- `query` (string, required): The search query
- `max_results` (integer, optional): Maximum number of results (1-10, default: 3)
- `include_answer` (boolean, optional): Whether to include a direct answer (default: true)

**Returns:**
JSON formatted search results including titles, URLs, content snippets, and optionally a direct answer.

## Usage

This server is designed to be used with MCP clients. It communicates via stdio using the MCP protocol.

## Environment Variables

- `TAVILY_API_KEY`: Required. Your Tavily API key for web search functionality.
