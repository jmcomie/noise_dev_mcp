#!/usr/bin/env python3
"""Quick test of the Gradio MCP UI"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_manager import MCPManager
from src.ui.chat_interface import ChatInterface
from src.utils.logging import setup_logging


async def test_basic_functionality():
    """Test basic functionality without launching the full UI."""
    print("=== Testing Gradio MCP UI ===\n")
    
    # Set up logging
    log_collector = setup_logging(log_level="INFO")
    print("✅ Logging system initialized")
    
    # Create MCP manager
    mcp_manager = MCPManager()
    print("✅ MCP Manager created")
    
    # Load default configuration
    default_config = {
        "mcpServers": {
            "example": {
                "command": "python",
                "args": ["./servers/example_server.py"]
            }
        }
    }
    mcp_manager.load_config_dict(default_config)
    print("✅ Configuration loaded")
    
    # List servers
    servers = mcp_manager.list_servers()
    print(f"✅ Available servers: {servers}")
    
    # Test connection to example server
    print("\n📡 Testing server connection...")
    success = await mcp_manager.connect_server("example")
    if success:
        print("✅ Successfully connected to example server")
        
        # Get server info
        server = mcp_manager.get_server("example")
        print(f"  - Tools: {len(server.tools)} available")
        print(f"  - Resources: {len(server.resources)} available")
        print(f"  - Prompts: {len(server.prompts)} available")
        
        # Test a tool call
        print("\n🔧 Testing tool execution...")
        try:
            result = await mcp_manager.call_tool("example", "add", {"a": 5, "b": 3})
            print(f"✅ Tool 'add' result: {result}")
        except Exception as e:
            print(f"❌ Tool execution failed: {e}")
        
        # Test resource reading
        print("\n📄 Testing resource access...")
        try:
            result = await mcp_manager.read_resource("example", "resource://server/info")
            print(f"✅ Resource read successful: {result}")
        except Exception as e:
            print(f"❌ Resource read failed: {e}")
        
        # Disconnect
        await mcp_manager.disconnect_server("example")
        print("\n✅ Disconnected from server")
    else:
        print("❌ Failed to connect to example server")
    
    # Test UI creation
    print("\n🎨 Testing UI creation...")
    try:
        chat_interface = ChatInterface(mcp_manager)
        interface = chat_interface.create_interface()
        print("✅ Gradio interface created successfully")
    except Exception as e:
        print(f"❌ UI creation failed: {e}")
    
    print("\n=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())