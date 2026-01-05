"""
MCP Client for Power BI documentation generation.

This module provides a Python client for communicating with MCP servers
using the Model Context Protocol over stdio.
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Exception raised for MCP client errors."""
    pass


class MCPClient:
    """
    Async client for communicating with MCP servers.
    
    This client handles the JSON-RPC communication protocol used by MCP,
    spawning the server as a subprocess and managing the stdio streams.
    
    Example:
        async with MCPClient(["python", "-m", "pbixray_server"]).connect() as client:
            result = await client.call_tool("get_tables")
    """
    
    def __init__(
        self, 
        server_command: list[str],
        env: dict[str, str] | None = None,
        timeout: float = 30.0
    ):
        """
        Initialize MCP client.
        
        Args:
            server_command: Command to start the MCP server (e.g., ["python", "server.py"])
            env: Optional environment variables for the server process
            timeout: Default timeout for tool calls in seconds
        """
        self.server_params = StdioServerParameters(
            command=server_command[0],
            args=server_command[1:] if len(server_command) > 1 else [],
            env=env
        )
        self.timeout = timeout
        self.session: ClientSession | None = None
        self._tools_cache: list[str] | None = None
    
    @asynccontextmanager
    async def connect(self):
        """
        Establish connection to MCP server.
        
        Yields:
            MCPClient: Connected client instance
            
        Example:
            async with MCPClient(cmd).connect() as client:
                await client.call_tool("some_tool")
        """
        logger.info(f"Connecting to MCP server: {self.server_params.command}")
        
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
                    logger.info("MCP session initialized successfully")
                    yield self
                    self.session = None
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPClientError(f"Connection failed: {e}") from e
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: dict[str, Any] | None = None,
        timeout: float | None = None
    ) -> dict[str, Any]:
        """
        Invoke an MCP tool and return the result.
        
        Args:
            tool_name: Name of the tool to invoke
            arguments: Optional arguments to pass to the tool
            timeout: Optional timeout override for this call
            
        Returns:
            Parsed JSON response from the tool
            
        Raises:
            MCPClientError: If not connected or tool call fails
        """
        if not self.session:
            raise MCPClientError("Not connected to MCP server")
        
        logger.debug(f"Calling tool: {tool_name} with args: {arguments}")
        
        try:
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments=arguments or {}),
                timeout=timeout or self.timeout
            )
            
            # Extract text content from response
            for content in result.content:
                if content.type == "text":
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        # Return raw text if not JSON
                        return {"raw_text": content.text}
            
            return {}
            
        except asyncio.TimeoutError:
            raise MCPClientError(f"Tool call '{tool_name}' timed out after {timeout or self.timeout}s")
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name} - {e}")
            raise MCPClientError(f"Tool call failed: {e}") from e
    
    async def list_tools(self) -> list[str]:
        """
        List available tools on the server.
        
        Returns:
            List of tool names
        """
        if not self.session:
            raise MCPClientError("Not connected to MCP server")
        
        if self._tools_cache is None:
            result = await self.session.list_tools()
            self._tools_cache = [tool.name for tool in result.tools]
            logger.info(f"Available tools: {self._tools_cache}")
        
        return self._tools_cache
    
    async def has_tool(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        tools = await self.list_tools()
        return tool_name in tools
