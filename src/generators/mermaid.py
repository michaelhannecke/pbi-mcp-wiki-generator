"""
Mermaid diagram generation for Power BI models.

This module generates Mermaid.js diagrams from Power BI model metadata,
including ER diagrams for relationships and data lineage visualizations.
"""
import re
from ..mcp_client.pbixray_tools import Relationship, Table


def sanitize_mermaid_name(name: str) -> str:
    """
    Sanitize a name for use in Mermaid diagrams.
    
    Mermaid has specific requirements for identifiers:
    - No spaces (replaced with underscores)
    - No special characters
    - Must start with a letter
    
    Args:
        name: Original name
        
    Returns:
        Sanitized name safe for Mermaid
    """
    # Replace spaces and hyphens with underscores
    sanitized = re.sub(r'[\s\-]+', '_', name)
    # Remove other special characters
    sanitized = re.sub(r'[^\w]', '', sanitized)
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'T_' + sanitized
    return sanitized or 'Unknown'


def generate_er_diagram(
    relationships: list[Relationship],
    tables: list[Table],
    include_orphans: bool = True,
    show_columns: bool = False
) -> str:
    """
    Generate Mermaid ER diagram from model relationships.
    
    Args:
        relationships: List of model relationships
        tables: List of all tables in the model
        include_orphans: Whether to include tables with no relationships
        show_columns: Whether to show column details in table boxes
        
    Returns:
        Mermaid ER diagram code
    """
    lines = ["erDiagram"]
    
    # Track connected tables
    connected_tables: set[str] = set()
    
    # Generate relationship lines
    for rel in relationships:
        connected_tables.add(rel.from_table)
        connected_tables.add(rel.to_table)
        
        from_name = sanitize_mermaid_name(rel.from_table)
        to_name = sanitize_mermaid_name(rel.to_table)
        
        # Determine cardinality notation
        # Power BI typically uses many-to-one relationships
        if rel.cardinality == "OneToOne":
            cardinality = "||--||"
        elif rel.cardinality == "OneToMany":
            cardinality = "||--o{"
        elif rel.cardinality == "ManyToMany":
            cardinality = "}o--o{"
        else:  # ManyToOne (default)
            cardinality = "}o--||"
        
        # Use dotted line for inactive relationships
        if not rel.is_active:
            cardinality = cardinality.replace("-", ".")
        
        # Add relationship line with both column names as label
        lines.append(
            f'    {to_name} {cardinality} {from_name} : "{rel.to_column} = {rel.from_column}"'
        )
    
    # Add table details if requested
    if show_columns:
        for table in tables:
            if table.name in connected_tables or include_orphans:
                table_name = sanitize_mermaid_name(table.name)
                lines.append(f'    {table_name} {{')
                for col in table.columns[:10]:  # Limit to 10 columns for readability
                    col_type = _map_data_type(col.data_type)
                    col_name = sanitize_mermaid_name(col.name)
                    lines.append(f'        {col_type} {col_name}')
                if len(table.columns) > 10:
                    lines.append(f'        string _more_{len(table.columns) - 10}_columns')
                lines.append('    }')
    
    # Add orphan tables (tables with no relationships)
    if include_orphans:
        orphan_tables = [t for t in tables if t.name not in connected_tables]
        for table in orphan_tables:
            table_name = sanitize_mermaid_name(table.name)
            if show_columns and table.columns:
                lines.append(f'    {table_name} {{')
                lines.append(f'        string disconnected_table')
                lines.append('    }')
            else:
                # Just reference the table so it appears
                lines.append(f'    {table_name}')
    
    return '\n'.join(lines)


def generate_data_flow_diagram(
    tables: list[Table],
    relationships: list[Relationship]
) -> str:
    """
    Generate a flowchart showing data flow through the model.
    
    Args:
        tables: List of tables
        relationships: List of relationships
        
    Returns:
        Mermaid flowchart code
    """
    lines = ["flowchart LR"]
    
    # Identify dimension vs fact tables (heuristic: tables that are "to" in relationships are dimensions)
    dimension_tables: set[str] = set()
    fact_tables: set[str] = set()
    
    for rel in relationships:
        dimension_tables.add(rel.to_table)
        fact_tables.add(rel.from_table)
    
    # Pure dimension tables (not also fact tables)
    pure_dimensions = dimension_tables - fact_tables
    pure_facts = fact_tables - dimension_tables
    bridge_tables = dimension_tables & fact_tables
    
    # Style definitions
    lines.append('    classDef dimension fill:#e1f5fe,stroke:#01579b')
    lines.append('    classDef fact fill:#fff3e0,stroke:#e65100')
    lines.append('    classDef bridge fill:#f3e5f5,stroke:#7b1fa2')
    
    # Add nodes
    for table in tables:
        safe_name = sanitize_mermaid_name(table.name)
        display_name = table.name.replace('"', "'")
        
        if table.name in pure_dimensions:
            lines.append(f'    {safe_name}["{display_name}"]:::dimension')
        elif table.name in pure_facts:
            lines.append(f'    {safe_name}["{display_name}"]:::fact')
        elif table.name in bridge_tables:
            lines.append(f'    {safe_name}["{display_name}"]:::bridge')
        else:
            lines.append(f'    {safe_name}["{display_name}"]')
    
    # Add edges
    for rel in relationships:
        from_name = sanitize_mermaid_name(rel.from_table)
        to_name = sanitize_mermaid_name(rel.to_table)
        
        if rel.is_active:
            lines.append(f'    {from_name} --> {to_name}')
        else:
            lines.append(f'    {from_name} -.-> {to_name}')
    
    return '\n'.join(lines)


def generate_measure_dependency_diagram(
    measures: list,
    max_measures: int = 30
) -> str:
    """
    Generate a diagram showing measure dependencies.
    
    This is a simplified version that groups measures by table.
    Full dependency analysis would require DAX parsing.
    
    Args:
        measures: List of Measure objects
        max_measures: Maximum measures to include
        
    Returns:
        Mermaid mindmap code
    """
    lines = ["mindmap"]
    lines.append("    root((Measures))")
    
    # Group by table
    by_table: dict[str, list] = {}
    for m in measures[:max_measures]:
        by_table.setdefault(m.table, []).append(m)
    
    for table, table_measures in by_table.items():
        safe_table = sanitize_mermaid_name(table)
        lines.append(f'        {safe_table}')
        for measure in table_measures[:10]:
            safe_measure = sanitize_mermaid_name(measure.name)
            lines.append(f'            {safe_measure}')
    
    return '\n'.join(lines)


def _map_data_type(pbi_type: str) -> str:
    """Map Power BI data types to simple Mermaid-friendly types."""
    type_map = {
        'Int64': 'int',
        'Double': 'decimal',
        'Decimal': 'decimal', 
        'String': 'string',
        'DateTime': 'datetime',
        'Boolean': 'boolean',
        'Binary': 'binary',
    }
    return type_map.get(pbi_type, 'string')
