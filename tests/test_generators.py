"""
Tests for Power BI Wiki Generator

These tests verify the core functionality without requiring
an actual MCP server connection.
"""
import pytest
from pathlib import Path

from src.generators.mermaid import (
    sanitize_mermaid_name,
    generate_er_diagram,
)
from src.generators.pages import (
    slugify,
    escape_markdown,
    generate_sidebar,
)
from src.mcp_client.pbixray_tools import (
    Table,
    Column,
    Measure,
    Relationship,
    ModelSummary,
)


class TestMermaidHelpers:
    """Test Mermaid diagram generation utilities."""
    
    def test_sanitize_simple_name(self):
        assert sanitize_mermaid_name("Sales") == "Sales"
    
    def test_sanitize_name_with_spaces(self):
        assert sanitize_mermaid_name("Sales Data") == "Sales_Data"
    
    def test_sanitize_name_with_special_chars(self):
        assert sanitize_mermaid_name("Sales-2024!") == "Sales_2024"
    
    def test_sanitize_name_starting_with_number(self):
        result = sanitize_mermaid_name("123Sales")
        assert result.startswith("T_")


class TestPageHelpers:
    """Test page generation utilities."""
    
    def test_slugify_basic(self):
        assert slugify("Sales Data") == "sales-data"
    
    def test_slugify_special_chars(self):
        assert slugify("Sales & Revenue!") == "sales-revenue"
    
    def test_escape_markdown_pipe(self):
        assert escape_markdown("col|name") == "col\\|name"
    
    def test_escape_markdown_empty(self):
        assert escape_markdown("") == ""
    
    def test_escape_markdown_none(self):
        assert escape_markdown(None) == ""


class TestDataClasses:
    """Test data class creation from dictionaries."""
    
    def test_table_from_dict(self):
        data = {
            "name": "Sales",
            "columns": [{"name": "Amount", "data_type": "Decimal"}],
            "rowCount": 1000
        }
        table = Table.from_dict(data)
        assert table.name == "Sales"
        assert table.row_count == 1000
        assert len(table.columns) == 1
    
    def test_measure_from_dict(self):
        data = {
            "name": "Total Sales",
            "table": "Sales",
            "expression": "SUM(Sales[Amount])",
            "formatString": "$#,##0"
        }
        measure = Measure.from_dict(data)
        assert measure.name == "Total Sales"
        assert measure.table == "Sales"
        assert measure.format_string == "$#,##0"
    
    def test_relationship_from_dict(self):
        data = {
            "fromTable": "Sales",
            "fromColumn": "ProductKey",
            "toTable": "Products",
            "toColumn": "ProductKey",
            "isActive": True
        }
        rel = Relationship.from_dict(data)
        assert rel.from_table == "Sales"
        assert rel.to_table == "Products"
        assert rel.is_active is True


class TestERDiagramGeneration:
    """Test ER diagram generation."""
    
    def test_empty_relationships(self):
        diagram = generate_er_diagram([], [])
        assert diagram == "erDiagram"
    
    def test_single_relationship(self):
        relationships = [
            Relationship(
                from_table="Sales",
                from_column="ProductKey",
                to_table="Products",
                to_column="ProductKey",
                is_active=True,
                cross_filter_direction="Single"
            )
        ]
        tables = [
            Table(name="Sales", columns=[]),
            Table(name="Products", columns=[])
        ]
        diagram = generate_er_diagram(relationships, tables)
        
        assert "erDiagram" in diagram
        assert "Sales" in diagram
        assert "Products" in diagram
        assert "ProductKey" in diagram


class TestSidebarGeneration:
    """Test sidebar generation."""
    
    def test_sidebar_with_tables(self):
        tables = [
            Table(name="Sales", columns=[]),
            Table(name="Products", columns=[], is_hidden=True),
            Table(name="Customers", columns=[])
        ]
        sidebar = generate_sidebar(tables)
        
        assert "Home" in sidebar
        assert "Measures" in sidebar
        assert "Sales" in sidebar
        assert "Customers" in sidebar
        # Hidden table should be excluded
        assert "Products" not in sidebar


# Integration test placeholder
class TestWikiGenerator:
    """Integration tests for WikiGenerator (require MCP server)."""
    
    @pytest.mark.skip(reason="Requires MCP server")
    async def test_generate_from_pbix(self, tmp_path):
        """Test full generation from PBIX file."""
        # This would require an actual PBIX file and MCP server
        pass
