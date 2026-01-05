#!/usr/bin/env python3
"""
Power BI Wiki Generator - CLI Entry Point

Generate GitHub wiki documentation from Power BI PBIX files.

Usage:
    python generate_wiki.py ./models/Sales.pbix -o ./wiki -n "Sales Analytics"
    
For help:
    python generate_wiki.py --help
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from src.generators import WikiGenerator, WikiGeneratorError


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate GitHub wiki documentation from Power BI PBIX files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./models/Sales.pbix
      Generate wiki in ./wiki directory
      
  %(prog)s ./models/Sales.pbix -o ./docs/wiki -n "Sales Analytics Model"
      Generate wiki with custom output and name
      
  %(prog)s ./models/Sales.pbix --include-hidden --no-power-query
      Include hidden items, exclude Power Query code

For CI/CD usage, see the GitHub Action workflow in .github/workflows/
        """
    )
    
    parser.add_argument(
        "pbix_file",
        type=Path,
        help="Path to the Power BI PBIX file"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("./wiki"),
        help="Output directory for wiki pages (default: ./wiki)"
    )
    
    parser.add_argument(
        "-n", "--name",
        type=str,
        default=None,
        help="Model name for documentation (default: PBIX filename)"
    )
    
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden tables and measures in documentation"
    )
    
    parser.add_argument(
        "--no-power-query",
        action="store_true",
        help="Exclude Power Query/M code from documentation"
    )
    
    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Skip Mermaid diagram generation"
    )
    
    parser.add_argument(
        "--server-command",
        type=str,
        default=None,
        help="Custom MCP server command (default: python -m pbixray_server)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser.parse_args()


async def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    # Validate input file
    if not args.pbix_file.exists():
        logger.error(f"PBIX file not found: {args.pbix_file}")
        return 1
    
    if not args.pbix_file.suffix.lower() == ".pbix":
        logger.warning(f"File does not have .pbix extension: {args.pbix_file}")
    
    # Parse server command if provided
    server_command = None
    if args.server_command:
        server_command = args.server_command.split()
    
    try:
        generator = WikiGenerator(
            output_dir=args.output,
            server_command=server_command,
            include_hidden=args.include_hidden,
            include_power_query=not args.no_power_query,
            generate_diagrams=not args.no_diagrams
        )
        
        stats = await generator.generate(
            pbix_path=args.pbix_file,
            model_name=args.name
        )
        
        print("\n" + "=" * 50)
        print("Wiki Generation Complete!")
        print("=" * 50)
        print(f"Output directory: {args.output.resolve()}")
        print(f"Pages generated:  {stats['pages_generated']}")
        print(f"Tables:           {stats['tables']}")
        print(f"Measures:         {stats['measures']}")
        print(f"Relationships:    {stats['relationships']}")
        print("=" * 50)
        
        return 0
        
    except WikiGeneratorError as e:
        logger.error(f"Generation failed: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


def run():
    """Synchronous wrapper for main."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    run()
