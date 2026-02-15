#!/usr/bin/env python3
"""
FastMCP server for Tavily Search.

Supports two transport modes:
  - stdio  (default) — for local use with Claude Desktop
  - sse    — for remote/cloud deployment over HTTP


Usage:
  python mcp_search_server.py              # stdio mode
  python mcp_search_server.py --transport sse   # SSE mode on 0.0.0.0:8000
"""

from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import argparse
import os

# Initialize FastMCP
mcp = FastMCP("mcp-search-agent")

# Initialize Tavily Client
# It will look for TAVILY_API_KEY in environment variables.
# Fallback to the key provided in the original script if not found, for convenience.
# DEFAULT_API_KEY = "tvly-XXX"
api_key = os.environ.get("TAVILY_API_KEY", DEFAULT_API_KEY)
tavily = TavilyClient(api_key=api_key)

@mcp.tool()
def tavily_search(query: str, search_depth: str = "advanced") -> str:
    """Search the web using Tavily. Pass the search term as the 'query' parameter.

    Args:
        query: The search query string to look up on the web.
        search_depth: The depth of search - either "basic" or "advanced" (default: "advanced").

    Returns:
        Search results from Tavily as a string.
    """
    response = tavily.search(query=query, search_depth=search_depth)
    print(f"[mcp-search-agent] tavily_search called with query='{query}'")
    
    return str(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Search Agent Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport mode: stdio (local) or sse (remote/cloud). Default: stdio",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="Host to bind to in SSE mode. Default: 0.0.0.0",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port to listen on in SSE mode. Default: 8000",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        print(f"[mcp-search-agent] Starting SSE server on {args.host}:{args.port}")

    mcp.run(transport=args.transport)
