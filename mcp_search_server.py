#!/usr/bin/env python3
"""
FastMCP server for Tavily Search.

Supports three transport modes:
  - stdio            (default) — for local use with Claude Desktop
  - sse              — legacy remote/cloud deployment over HTTP
  - streamable-http  — recommended remote/cloud deployment over HTTP


Usage:
  python mcp_search_server.py                            # stdio mode
  python mcp_search_server.py --transport streamable-http # HTTP mode on 0.0.0.0:8000
  python mcp_search_server.py --transport sse             # SSE mode (legacy)
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from tavily import TavilyClient
import argparse
import os

# Initialize Tavily Client lazily
# It will look for TAVILY_API_KEY in environment variables.
_tavily = None

def get_tavily() -> TavilyClient:
    global _tavily
    if _tavily is None:
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY not set. Set it via environment variable.")
        _tavily = TavilyClient(api_key=api_key)
    return _tavily


def create_mcp(host: str = "127.0.0.1", port: int = 8000, remote: bool = False) -> FastMCP:
    """Create a FastMCP instance with the appropriate settings."""
    if remote:
        # Disable DNS rebinding protection for remote/cloud deployment
        # so that external clients can connect via the VM's public IP.
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )
        mcp = FastMCP(
            "mcp-search-agent",
            host=host,
            port=port,
            transport_security=security,
            stateless_http=True,
        )
    else:
        mcp = FastMCP("mcp-search-agent")
    return mcp


# Create a default instance for tool registration
mcp = create_mcp()


@mcp.tool()
def tavily_search(query: str, search_depth: str = "advanced") -> str:
    """Search the web using Tavily. Pass the search term as the 'query' parameter.

    Args:
        query: The search query string to look up on the web.
        search_depth: The depth of search - either "basic" or "advanced" (default: "advanced").

    Returns:
        Search results from Tavily as a string.
    """
    response = get_tavily().search(query=query, search_depth=search_depth)
    print(f"[mcp-search-agent] tavily_search called with query='{query}'")

    return str(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Search Agent Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport mode: stdio (local), sse, or streamable-http (remote/cloud). Default: stdio",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="Host to bind to in HTTP mode. Default: 0.0.0.0",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port to listen on in HTTP mode. Default: 8000",
    )
    args = parser.parse_args()

    if args.transport in ("sse", "streamable-http"):
        # Recreate with remote settings (DNS rebinding protection disabled)
        mcp = create_mcp(host=args.host, port=args.port, remote=True)

        # Re-register the tool on the new instance
        mcp.tool()(tavily_search)

        print(f"[mcp-search-agent] Starting {args.transport} server on {args.host}:{args.port}")

    mcp.run(transport=args.transport)
