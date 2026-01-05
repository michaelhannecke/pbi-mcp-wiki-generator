# 📊 Power BI Wiki Generator

**Automatically generate GitHub wiki documentation from Power BI PBIX files using the Model Context Protocol (MCP).**

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Ready-2088FF?logo=github-actions&logoColor=white)](#github-actions-integration)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#requirements)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Overview

Stop maintaining Power BI documentation manually. This tool extracts metadata from your PBIX files and generates a complete, navigable GitHub wiki — automatically.

### What Gets Documented

- **📋 Tables** — Columns, data types, descriptions
- **📐 DAX Measures** — Expressions, format strings, business logic
- **🔗 Relationships** — Interactive ER diagrams via Mermaid.js
- **💾 Data Sources** — Power Query/M code with source detection
- **📈 Calculated Columns** — DAX expressions and metadata

### Example Output

```
wiki/
├── Home.md              # Model overview with statistics
├── Table-Sales.md       # Individual table documentation
├── Table-Products.md
├── Measures.md          # All DAX measures by table
├── Relationships.md     # ER diagram + relationship details
├── Data-Sources.md      # Power Query documentation
└── _Sidebar.md          # Navigation menu
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- A Power BI PBIX file
- (For CI/CD) GitHub repository with wiki enabled

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/pbi-wiki-generator.git
cd pbi-wiki-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Generate wiki from PBIX file
python generate_wiki.py ./path/to/your/model.pbix

# Custom output directory and model name
python generate_wiki.py ./model.pbix -o ./docs/wiki -n "Sales Analytics"

# Include hidden items
python generate_wiki.py ./model.pbix --include-hidden

# Skip Power Query documentation
python generate_wiki.py ./model.pbix --no-power-query
```

### CLI Options

```
usage: generate_wiki.py [-h] [-o OUTPUT] [-n NAME] [--include-hidden]
                        [--no-power-query] [--no-diagrams] [--server-command CMD]
                        [-v] [--version] pbix_file

Arguments:
  pbix_file             Path to the Power BI PBIX file

Options:
  -o, --output          Output directory (default: ./wiki)
  -n, --name            Model display name (default: filename)
  --include-hidden      Include hidden tables/measures
  --no-power-query      Exclude Power Query/M code
  --no-diagrams         Skip Mermaid diagram generation
  --server-command      Custom MCP server command (default: python -m pbixray_server)
  -v, --verbose         Enable verbose logging
  --version             Show version and exit
```

---

## 🔧 GitHub Actions Integration

Automate documentation on every PBIX change.

### Setup

1. **Enable wiki** in your repository (Settings → Features → Wikis)
2. **Create one page** manually to initialize the wiki repo
3. **Copy the workflow** to `.github/workflows/generate-wiki.yml`

### Workflow Features

- **Auto-trigger** on PBIX file push to main/master
- **Manual trigger** via workflow_dispatch
- **Job summary** with links to generated docs
- **Concurrency control** to prevent conflicts

### Manual Trigger

Navigate to Actions → Generate Power BI Documentation → Run workflow

Input parameters:
- `pbix_path`: Path to PBIX file
- `model_name`: Display name (optional)
- `include_hidden`: Include hidden items (checkbox)

---

## 📖 How It Works

This tool uses the **Model Context Protocol (MCP)** to extract metadata from PBIX files.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PBIX File     │────▶│ PBIXRay Server  │────▶│  Python Client  │
│                 │     │    (MCP)        │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌─────────────────┐     ┌────────▼────────┐
                        │  GitHub Wiki    │◀────│ Wiki Generator  │
                        │   (Markdown)    │     │ (Mermaid/MD)    │
                        └─────────────────┘     └─────────────────┘
```

### Components

1. **MCP Client** (`src/mcp_client/`) — Communicates with PBIXRay via JSON-RPC
2. **PBIXRay Server** — Extracts model metadata from PBIX files
3. **Wiki Generator** (`src/generators/`) — Transforms metadata into Markdown
4. **GitHub Action** — Orchestrates CI/CD automation

---

## 🎨 Customization

### Wiki Templates

Modify `src/generators/pages.py` to customize page layouts:

```python
# Example: Add custom header to all pages
def generate_home_page(...):
    content = "<!-- Custom header -->\n"
    content += f"# {model_name}\n\n"
    # ...
```

### Mermaid Diagrams

Configure diagram options in `src/generators/mermaid.py`:

```python
# Show column details in ER diagram
er_diagram = generate_er_diagram(
    relationships,
    tables,
    include_orphans=True,
    show_columns=True  # Enable column display
)
```

### Add Custom Pages

Extend `WikiGenerator._generate_pages()`:

```python
# Add custom page
self._write_page("Custom-Page", generate_custom_page(metadata))
```

---

## 🔍 Troubleshooting

### "MCP server not found"

Ensure pbixray is installed:
```bash
pip install pbixray
```

### "Wiki push failed"

1. Verify wiki is enabled in repo settings
2. Create at least one wiki page manually first
3. Check GITHUB_TOKEN permissions

### "No measures/tables found"

The PBIX file may:
- Use DirectQuery (limited metadata)
- Be password protected
- Have an incompatible format version

### Verbose Logging

```bash
python generate_wiki.py model.pbix -v
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### Development Setup

```bash
pip install -e ".[dev]"
pytest tests/
```

---

## 📚 Related Resources

- [Microsoft Power BI Modeling MCP Server](https://github.com/microsoft/powerbi-modeling-mcp)
- [PBIXRay MCP Server](https://github.com/jonaolden/pbixray-mcp-server)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Mermaid.js Documentation](https://mermaid.js.org/)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Hugo Berry](https://github.com/Hugoberry) — PBIXRay library
- [Anthropic](https://anthropic.com) — Model Context Protocol
- [Microsoft](https://microsoft.com) — Power BI Modeling MCP Server

---

*Built for the Power BI community by developers who got tired of stale documentation.*
