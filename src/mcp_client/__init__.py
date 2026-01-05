"""MCP Client module for Power BI documentation generation."""
from .client import MCPClient, MCPClientError
from .pbixray_tools import (
    PBIXRayClient,
    Table,
    Column,
    Measure,
    CalculatedColumn,
    Relationship,
    ModelSummary,
)

__all__ = [
    "MCPClient",
    "MCPClientError",
    "PBIXRayClient",
    "Table",
    "Column",
    "Measure",
    "CalculatedColumn",
    "Relationship",
    "ModelSummary",
]
