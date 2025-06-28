# Gradio MCP UI

A modern, user-friendly interface for interacting with multiple MCP (Model Context Protocol) servers using Gradio.

## Features

- 🚀 Connect to multiple MCP servers simultaneously
- 💬 Interactive chat interface with streaming responses
- 📊 Real-time server log viewer
- 🔧 Support for tools, resources, and prompts
- 🔐 Authentication support (Bearer tokens, OAuth)
- 📁 Session persistence and history

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd gradio-mcp-ui

# Install using uv
uv sync
```

## Quick Start

1. Configure your MCP servers in `servers/config.yaml`
2. Run the application:
   ```bash
   uv run python src/main.py
   ```
3. Open your browser to the displayed URL

## Configuration

Create a `servers/config.yaml` file:

```yaml
mcpServers:
  assistant:
    command: python
    args: ["./servers/example_server.py"]
  
  weather:
    url: https://weather-api.example.com/mcp
    transport: http
```

## Development

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint code
uv run ruff check src/
```

## License

MIT