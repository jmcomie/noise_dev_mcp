#!/usr/bin/env python3
"""Verify that the Gradio UI can be created successfully."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_manager import MCPManager
from src.ui.chat_interface import ChatInterface
from src.utils.logging import setup_logging


def verify_ui():
    """Verify UI creation without launching."""
    print("🔍 Verifying Gradio MCP UI...\n")
    
    # Set up logging
    setup_logging(log_level="INFO")
    
    # Create MCP manager with config
    mcp_manager = MCPManager()
    default_config = {
        "mcpServers": {
            "example": {
                "command": "python",
                "args": ["./servers/example_server.py"]
            }
        }
    }
    mcp_manager.load_config_dict(default_config)
    
    # Create chat interface
    chat_interface = ChatInterface(mcp_manager)
    interface = chat_interface.create_interface()
    
    print("✅ Gradio interface created successfully!")
    print("\nInterface components:")
    print(f"  - Title: {interface.title}")
    print(f"  - Theme: {interface.theme.name if interface.theme else 'Default'}")
    print(f"  - Components: {len(interface.blocks)} blocks")
    
    print("\n✅ All verifications passed!")
    print("\nTo launch the full UI, run:")
    print("  ./run.sh")
    print("or")
    print("  uv run python src/main.py")


if __name__ == "__main__":
    verify_ui()