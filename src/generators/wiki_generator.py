"""
Main wiki generator orchestrator.

This module coordinates the extraction of metadata from Power BI files
and generates a complete GitHub wiki structure.
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from ..mcp_client import MCPClient, PBIXRayClient
from .mermaid import generate_er_diagram, generate_data_flow_diagram
from .pages import (
    generate_home_page,
    generate_table_page,
    generate_measures_page,
    generate_relationships_page,
    generate_data_sources_page,
    generate_sidebar,
    slugify,
)

logger = logging.getLogger(__name__)


class WikiGeneratorError(Exception):
    """Exception raised for wiki generation errors."""
    pass


class WikiGenerator:
    """
    Generates GitHub wiki pages from Power BI model files.
    
    This class orchestrates the complete documentation generation process:
    1. Connects to the PBIXRay MCP server
    2. Extracts all model metadata
    3. Generates structured Markdown pages
    4. Outputs files ready for GitHub wiki
    
    Example:
        generator = WikiGenerator("./wiki-output")
        await generator.generate("./models/Sales.pbix", "Sales Analytics")
    """
    
    def __init__(
        self,
        output_dir: str | Path,
        server_command: list[str] | None = None,
        include_hidden: bool = False,
        include_power_query: bool = True,
        generate_diagrams: bool = True
    ):
        """
        Initialize wiki generator.
        
        Args:
            output_dir: Directory for output wiki pages
            server_command: MCP server command (default: python pbixray server)
            include_hidden: Include hidden tables/measures in docs
            include_power_query: Include Power Query/M code in docs
            generate_diagrams: Generate Mermaid diagrams
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.server_command = server_command or self._default_server_command()
        self.include_hidden = include_hidden
        self.include_power_query = include_power_query
        self.generate_diagrams = generate_diagrams
        
        self._generated_at = datetime.now(timezone.utc)
    
    @staticmethod
    def _default_server_command() -> list[str]:
        """Get default MCP server command."""
        return [sys.executable, "-m", "pbixray_server"]
    
    async def generate(
        self,
        pbix_path: str | Path,
        model_name: str | None = None
    ) -> dict[str, Any]:
        """
        Generate complete wiki from PBIX file.
        
        Args:
            pbix_path: Path to the PBIX file
            model_name: Display name for the model (default: filename)
            
        Returns:
            Dictionary with generation statistics
            
        Raises:
            WikiGeneratorError: If generation fails
        """
        pbix_path = Path(pbix_path).resolve()
        
        if not pbix_path.exists():
            raise WikiGeneratorError(f"PBIX file not found: {pbix_path}")
        
        if not model_name:
            model_name = pbix_path.stem
        
        logger.info(f"Starting wiki generation for: {model_name}")
        logger.info(f"PBIX file: {pbix_path}")
        logger.info(f"Output directory: {self.output_dir}")
        
        try:
            # Extract metadata via MCP
            metadata = await self._extract_metadata(str(pbix_path))
            
            # Generate all pages
            stats = self._generate_pages(model_name, metadata)
            
            logger.info(f"Wiki generation complete. Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Wiki generation failed: {e}")
            raise WikiGeneratorError(f"Generation failed: {e}") from e
    
    async def _extract_metadata(self, pbix_path: str) -> dict[str, Any]:
        """Extract all metadata from PBIX file via MCP."""
        logger.info("Connecting to MCP server...")
        
        async with MCPClient(self.server_command).connect() as client:
            pbi = PBIXRayClient(client)
            
            # Load the model
            logger.info("Loading PBIX file...")
            await pbi.load_pbix(pbix_path)
            
            # Extract all metadata
            logger.info("Extracting tables...")
            tables = await pbi.get_tables()
            
            logger.info("Extracting measures...")
            measures = await pbi.get_measures()
            
            logger.info("Extracting relationships...")
            relationships = await pbi.get_relationships()
            
            logger.info("Extracting model summary...")
            summary = await pbi.get_model_summary()
            
            # Get schema for each table
            logger.info("Extracting table schemas...")
            schemas = {}
            for table in tables:
                try:
                    schemas[table.name] = await pbi.get_schema(table.name)
                except Exception as e:
                    logger.warning(f"Failed to get schema for {table.name}: {e}")
                    schemas[table.name] = {"columns": []}
            
            # Get calculated columns
            logger.info("Extracting calculated columns...")
            try:
                calc_columns = await pbi.get_calculated_columns()
            except Exception as e:
                logger.warning(f"Failed to get calculated columns: {e}")
                calc_columns = []
            
            # Get Power Query if requested
            power_query = {}
            if self.include_power_query:
                logger.info("Extracting Power Query expressions...")
                try:
                    power_query = await pbi.get_power_query()
                except Exception as e:
                    logger.warning(f"Failed to get Power Query: {e}")
            
            return {
                "tables": tables,
                "measures": measures,
                "relationships": relationships,
                "summary": summary,
                "schemas": schemas,
                "calculated_columns": calc_columns,
                "power_query": power_query,
            }
    
    def _generate_pages(
        self,
        model_name: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate all wiki pages from extracted metadata."""
        tables = metadata["tables"]
        measures = metadata["measures"]
        relationships = metadata["relationships"]
        summary = metadata["summary"]
        schemas = metadata["schemas"]
        calc_columns = metadata["calculated_columns"]
        power_query = metadata["power_query"]

        # Filter hidden items if requested
        if not self.include_hidden:
            tables = [t for t in tables if not t.is_hidden]
            measures = [m for m in measures if not m.is_hidden]

        stats = {
            "pages_generated": 0,
            "tables": len(tables),
            "measures": len(measures),
            "relationships": len(relationships),
        }
        
        # Generate ER diagram
        er_diagram = ""
        data_flow_diagram = None
        if self.generate_diagrams:
            logger.info("Generating diagrams...")
            er_diagram = generate_er_diagram(
                relationships,
                tables,
                include_orphans=True,
                show_columns=False
            )
            data_flow_diagram = generate_data_flow_diagram(tables, relationships)
        
        # Generate Home page
        logger.info("Generating Home page...")
        self._write_page("Home", generate_home_page(
            model_name,
            summary,
            tables,
            measures,
            self._generated_at
        ))
        stats["pages_generated"] += 1
        
        # Generate individual table pages
        logger.info(f"Generating {len(tables)} table pages...")
        for table in tables:
            page_name = f"Table-{slugify(table.name)}"
            table_pq = power_query.get(table.name, "")
            
            self._write_page(page_name, generate_table_page(
                table,
                schemas.get(table.name, {}),
                measures,
                calc_columns,
                table_pq if self.include_power_query else None
            ))
            stats["pages_generated"] += 1
        
        # Generate Measures page
        logger.info("Generating Measures page...")
        self._write_page("Measures", generate_measures_page(
            measures,
            include_hidden=self.include_hidden
        ))
        stats["pages_generated"] += 1
        
        # Generate Relationships page
        logger.info("Generating Relationships page...")
        self._write_page("Relationships", generate_relationships_page(
            relationships,
            er_diagram,
            data_flow_diagram
        ))
        stats["pages_generated"] += 1
        
        # Generate Data Sources page
        logger.info("Generating Data Sources page...")
        self._write_page("Data-Sources", generate_data_sources_page(
            power_query,
            tables
        ))
        stats["pages_generated"] += 1
        
        # Generate Sidebar
        logger.info("Generating sidebar...")
        self._write_page("_Sidebar", generate_sidebar(tables))
        stats["pages_generated"] += 1
        
        return stats
    
    def _write_page(self, name: str, content: str) -> None:
        """Write a wiki page to the output directory."""
        path = self.output_dir / f"{name}.md"
        path.write_text(content, encoding="utf-8")
        logger.debug(f"Written: {path}")


async def generate_wiki(
    pbix_path: str,
    output_dir: str,
    model_name: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Convenience function to generate wiki from PBIX file.
    
    Args:
        pbix_path: Path to PBIX file
        output_dir: Output directory for wiki pages
        model_name: Optional model display name
        **kwargs: Additional options passed to WikiGenerator
        
    Returns:
        Generation statistics
    """
    generator = WikiGenerator(output_dir, **kwargs)
    return await generator.generate(pbix_path, model_name)
