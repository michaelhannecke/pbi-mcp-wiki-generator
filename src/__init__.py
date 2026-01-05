"""
Power BI Wiki Generator

Automatically generate GitHub wiki documentation from Power BI PBIX files
using the Model Context Protocol (MCP).
"""
__version__ = "0.1.0"

from .mcp_client import MCPClient, PBIXRayClient
from .generators import WikiGenerator, generate_wiki

__all__ = [
    "__version__",
    "MCPClient",
    "PBIXRayClient",
    "WikiGenerator",
    "generate_wiki",
]
