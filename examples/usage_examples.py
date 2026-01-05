#!/usr/bin/env python3
"""
Example: Generate Wiki Documentation for Power BI Model

This script demonstrates how to use the pbi-wiki-generator
programmatically in your own Python code.
"""
import asyncio
from pathlib import Path

from src.generators import WikiGenerator
from src.mcp_client import MCPClient, PBIXRayClient


async def basic_generation():
    """Basic example: Generate wiki from PBIX file."""
    
    generator = WikiGenerator(
        output_dir="./wiki-output",
        include_hidden=False,
        include_power_query=True,
        generate_diagrams=True
    )
    
    stats = await generator.generate(
        pbix_path="./models/SalesModel.pbix",
        model_name="Sales Analytics Model"
    )
    
    print(f"Generated {stats['pages_generated']} pages")
    print(f"Tables: {stats['tables']}")
    print(f"Measures: {stats['measures']}")


async def custom_extraction():
    """Advanced example: Custom metadata extraction."""
    
    server_command = ["python", "-m", "pbixray_server"]
    
    async with MCPClient(server_command).connect() as client:
        pbi = PBIXRayClient(client)
        
        # Load model
        await pbi.load_pbix("./models/SalesModel.pbix")
        
        # Get specific data
        tables = await pbi.get_tables()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table.name}: {len(table.columns)} columns")
        
        # Get measures for a specific table
        sales_measures = await pbi.get_measures(table_name="Sales")
        print(f"\nMeasures in Sales table:")
        for m in sales_measures:
            print(f"  - {m.name}")
        
        # Get relationships
        relationships = await pbi.get_relationships()
        print(f"\nFound {len(relationships)} relationships")


async def batch_processing():
    """Example: Process multiple PBIX files."""
    
    models_dir = Path("./models")
    output_base = Path("./wikis")
    
    for pbix_file in models_dir.glob("*.pbix"):
        print(f"\nProcessing: {pbix_file.name}")
        
        output_dir = output_base / pbix_file.stem
        generator = WikiGenerator(output_dir)
        
        try:
            stats = await generator.generate(pbix_file)
            print(f"  ✓ Generated {stats['pages_generated']} pages")
        except Exception as e:
            print(f"  ✗ Failed: {e}")


if __name__ == "__main__":
    # Run the basic example
    asyncio.run(basic_generation())
    
    # Uncomment to run other examples:
    # asyncio.run(custom_extraction())
    # asyncio.run(batch_processing())
