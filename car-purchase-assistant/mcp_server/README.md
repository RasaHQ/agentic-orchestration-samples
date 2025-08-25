# MCP Web Search Server

A standalone MCP (Model Context Protocol) server that provides web search capabilities
via the [Tavily API](https://www.tavily.com/).

## What This MCP Server Does

This MCP server acts as a bridge between AI agents and real-time web search functionality. It:

- **Exposes web search as a tool** that agents can call to get current information
- **Handles API communication** with Tavily's search service
- **Formats search results** in a structured way that agents can easily process
- **Manages rate limiting and error handling** for the search API
- **Provides a standardized interface** for agents to access web search capabilities

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


## Setup Instructions

Follow these steps to get the MCP server up and running:

### Requirements

- **Python 3.10 or higher** is required.

### Create and Activate a Virtual Environment

```bash
python -m venv mcp-server-venv
source activate mcp-server-venv/bin/activate
```

### Install FastMCP

```bash
pip install fastmcp==2.11.3
pip install tavily-python==0.7.11
```

### Start the server

Make sure your `TAVILY_API_KEY` is set.

```bash
python tavily_search_server.py
```

Keep the terminal open.


