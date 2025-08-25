#!/usr/bin/env python3
import sys
from fastmcp import FastMCP
from tools.tavily import TavilySearchTool

# Create FastMCP server as global variable for CLI discovery
mcp = FastMCP("Web Search Server")

# Initialize tools
tavily_tool = TavilySearchTool()


@mcp.tool()
async def tavily_search(
    query: str, max_results: int = 3, include_answer: bool = True
) -> str:
    """Search the web using Tavily to get current information

    Args:
        query: The search query
        max_results: Maximum number of results to return
        include_answer: Whether to include a direct answer
    """
    arguments = {
        "query": query,
        "max_results": max_results,
        "include_answer": include_answer,
    }
    return await tavily_tool.execute(arguments)


def main():
    # Parse port from command line args
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default 8000", file=sys.stderr)

    print(f"Starting Web Search MCP server on http://localhost:{port}", file=sys.stderr)

    # Run with streamable HTTP transport (newer, more reliable)
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")


if __name__ == "__main__":
    main()
