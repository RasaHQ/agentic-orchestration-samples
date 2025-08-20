#!/usr/bin/env python3
import asyncio
import sys
from mcp.server.fastmcp import FastMCP
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

    # Run with uvicorn directly for custom port
    import uvicorn

    uvicorn.run(mcp.streamable_http_app(), host="localhost", port=port)


if __name__ == "__main__":
    main()
