"""
PBIXRay MCP Server tool wrappers.

This module provides typed wrappers around the PBIXRay MCP server tools,
converting raw JSON responses into structured Python objects.
"""
from dataclasses import dataclass, field
from typing import Any
import logging

from .client import MCPClient

logger = logging.getLogger(__name__)


@dataclass
class Column:
    """Represents a column in a Power BI table."""
    name: str
    data_type: str
    is_hidden: bool = False
    description: str | None = None
    format_string: str | None = None
    sort_by_column: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Column":
        return cls(
            name=data.get("name", ""),
            data_type=data.get("data_type", data.get("dataType", "Unknown")),
            is_hidden=data.get("is_hidden", data.get("isHidden", False)),
            description=data.get("description"),
            format_string=data.get("format_string", data.get("formatString")),
            sort_by_column=data.get("sort_by_column", data.get("sortByColumn"))
        )


@dataclass
class Table:
    """Represents a table in a Power BI model."""
    name: str
    columns: list[Column] = field(default_factory=list)
    row_count: int | None = None
    is_hidden: bool = False
    description: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Table":
        columns = [Column.from_dict(c) for c in data.get("columns", [])]
        return cls(
            name=data.get("name", ""),
            columns=columns,
            row_count=data.get("row_count", data.get("rowCount")),
            is_hidden=data.get("is_hidden", data.get("isHidden", False)),
            description=data.get("description")
        )


@dataclass
class Measure:
    """Represents a DAX measure in a Power BI model."""
    name: str
    table: str
    expression: str
    description: str | None = None
    format_string: str | None = None
    is_hidden: bool = False
    display_folder: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Measure":
        return cls(
            name=data.get("name", ""),
            table=data.get("table", data.get("tableName", "")),
            expression=data.get("expression", data.get("dax", "")),
            description=data.get("description"),
            format_string=data.get("format_string", data.get("formatString")),
            is_hidden=data.get("is_hidden", data.get("isHidden", False)),
            display_folder=data.get("display_folder", data.get("displayFolder"))
        )


@dataclass
class CalculatedColumn:
    """Represents a DAX calculated column."""
    name: str
    table: str
    expression: str
    data_type: str | None = None
    description: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "CalculatedColumn":
        return cls(
            name=data.get("name", ""),
            table=data.get("table", data.get("tableName", "")),
            expression=data.get("expression", data.get("dax", "")),
            data_type=data.get("data_type", data.get("dataType")),
            description=data.get("description")
        )


@dataclass
class Relationship:
    """Represents a relationship between tables."""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    is_active: bool = True
    cross_filter_direction: str = "Single"
    cardinality: str = "ManyToOne"
    
    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        return cls(
            from_table=data.get("from_table", data.get("fromTable", "")),
            from_column=data.get("from_column", data.get("fromColumn", "")),
            to_table=data.get("to_table", data.get("toTable", "")),
            to_column=data.get("to_column", data.get("toColumn", "")),
            is_active=data.get("is_active", data.get("isActive", True)),
            cross_filter_direction=data.get(
                "cross_filter_direction", 
                data.get("crossFilteringBehavior", "Single")
            ),
            cardinality=data.get("cardinality", "ManyToOne")
        )


@dataclass
class ModelSummary:
    """Summary statistics for a Power BI model."""
    table_count: int = 0
    column_count: int = 0
    measure_count: int = 0
    relationship_count: int = 0
    size_bytes: int | None = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "ModelSummary":
        return cls(
            table_count=data.get("table_count", data.get("tableCount", 0)),
            column_count=data.get("column_count", data.get("columnCount", 0)),
            measure_count=data.get("measure_count", data.get("measureCount", 0)),
            relationship_count=data.get("relationship_count", data.get("relationshipCount", 0)),
            size_bytes=data.get("size_bytes", data.get("sizeBytes"))
        )


class PBIXRayClient:
    """
    High-level client for PBIXRay MCP server.
    
    Provides typed methods for all PBIXRay tools, converting raw
    JSON responses into structured Python dataclasses.
    
    Example:
        async with MCPClient(["python", "-m", "pbixray_server"]).connect() as mcp:
            client = PBIXRayClient(mcp)
            await client.load_pbix("/path/to/model.pbix")
            tables = await client.get_tables()
    """
    
    def __init__(self, client: MCPClient):
        """
        Initialize PBIXRay client.
        
        Args:
            client: Connected MCPClient instance
        """
        self.client = client
        self._loaded_file: str | None = None
    
    async def load_pbix(self, file_path: str) -> dict[str, Any]:
        """
        Load a PBIX file for analysis.
        
        Args:
            file_path: Path to the PBIX file
            
        Returns:
            Load confirmation with basic file info
        """
        logger.info(f"Loading PBIX file: {file_path}")
        result = await self.client.call_tool(
            "load_pbix_file",
            {"file_path": file_path}
        )
        self._loaded_file = file_path
        return result
    
    async def get_tables(self) -> list[Table]:
        """
        Get all tables in the model.
        
        Returns:
            List of Table objects
        """
        result = await self.client.call_tool("get_tables")
        tables_data = result.get("tables", result.get("result", []))
        
        if isinstance(tables_data, list):
            return [Table.from_dict(t) if isinstance(t, dict) else Table(name=str(t)) 
                    for t in tables_data]
        return []
    
    async def get_measures(self, table_name: str | None = None) -> list[Measure]:
        """
        Get DAX measures, optionally filtered by table.
        
        Args:
            table_name: Optional table name to filter measures
            
        Returns:
            List of Measure objects
        """
        args = {}
        if table_name:
            args["table_name"] = table_name
            
        result = await self.client.call_tool("get_dax_measures", args)
        measures_data = result.get("measures", result.get("result", []))
        
        if isinstance(measures_data, list):
            return [Measure.from_dict(m) for m in measures_data if isinstance(m, dict)]
        return []
    
    async def get_calculated_columns(
        self, 
        table_name: str | None = None
    ) -> list[CalculatedColumn]:
        """
        Get DAX calculated columns.
        
        Args:
            table_name: Optional table name to filter
            
        Returns:
            List of CalculatedColumn objects
        """
        args = {}
        if table_name:
            args["table_name"] = table_name
            
        result = await self.client.call_tool("get_dax_columns", args)
        columns_data = result.get("columns", result.get("result", []))
        
        if isinstance(columns_data, list):
            return [CalculatedColumn.from_dict(c) for c in columns_data if isinstance(c, dict)]
        return []
    
    async def get_relationships(self) -> list[Relationship]:
        """
        Get all model relationships.
        
        Returns:
            List of Relationship objects
        """
        result = await self.client.call_tool("get_relationships")
        rels_data = result.get("relationships", result.get("result", []))
        
        if isinstance(rels_data, list):
            return [Relationship.from_dict(r) for r in rels_data if isinstance(r, dict)]
        return []
    
    async def get_schema(self, table_name: str | None = None) -> dict[str, Any]:
        """
        Get schema information for tables.
        
        Args:
            table_name: Optional specific table name
            
        Returns:
            Schema dictionary with column details
        """
        args = {}
        if table_name:
            args["table_name"] = table_name
            
        return await self.client.call_tool("get_schema", args)
    
    async def get_power_query(self) -> dict[str, str]:
        """
        Get Power Query/M code for all tables.
        
        Returns:
            Dictionary mapping table names to M expressions
        """
        result = await self.client.call_tool("get_power_query")
        
        # Handle different response formats
        if isinstance(result, dict):
            if "queries" in result:
                return result["queries"]
            elif "result" in result:
                return result["result"]
            else:
                # Filter out non-query keys
                return {k: v for k, v in result.items() 
                        if isinstance(v, str) and not k.startswith("_")}
        return {}
    
    async def get_model_summary(self) -> ModelSummary:
        """
        Get comprehensive model summary.
        
        Returns:
            ModelSummary object with statistics
        """
        result = await self.client.call_tool("get_model_summary")
        return ModelSummary.from_dict(result)
    
    async def get_model_size(self) -> int | None:
        """
        Get model size in bytes.
        
        Returns:
            Size in bytes or None if unavailable
        """
        result = await self.client.call_tool("get_model_size")
        return result.get("size_bytes", result.get("size"))
    
    async def get_statistics(self) -> dict[str, Any]:
        """
        Get detailed model statistics.
        
        Returns:
            Statistics dictionary
        """
        return await self.client.call_tool("get_statistics")
    
    async def get_metadata(self) -> dict[str, Any]:
        """
        Get model metadata.
        
        Returns:
            Metadata dictionary
        """
        return await self.client.call_tool("get_metadata")
