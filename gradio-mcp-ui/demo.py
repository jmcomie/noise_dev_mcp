#!/usr/bin/env python3
"""
Demo script showing MCP server capabilities.
"""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_manager import MCPManager
from src.utils.logging import setup_logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


async def demo():
    """Run a demo of MCP server capabilities."""
    console.print(Panel.fit("🚀 [bold cyan]Gradio MCP UI Demo[/bold cyan]", border_style="cyan"))
    
    # Set up logging
    setup_logging(log_level="WARNING")  # Quiet for demo
    
    # Create and configure manager
    mcp_manager = MCPManager()
    config = {
        "mcpServers": {
            "example": {
                "command": "python",
                "args": ["./servers/example_server.py"]
            }
        }
    }
    mcp_manager.load_config_dict(config)
    
    # Connect to server
    console.print("\n📡 Connecting to example server...")
    success = await mcp_manager.connect_server("example")
    
    if not success:
        console.print("[red]Failed to connect![/red]")
        return
    
    console.print("[green]✅ Connected successfully![/green]")
    
    # Get server info
    server = mcp_manager.get_server("example")
    
    # Display capabilities
    console.print("\n[bold]Server Capabilities:[/bold]")
    
    # Tools table
    tools_table = Table(title="🔧 Available Tools", show_header=True, header_style="bold magenta")
    tools_table.add_column("Tool Name", style="cyan")
    tools_table.add_column("Description", style="white")
    
    for tool in server.tools:
        tools_table.add_row(tool.name, tool.description or "No description")
    
    console.print(tools_table)
    
    # Resources table
    resources_table = Table(title="📄 Available Resources", show_header=True, header_style="bold magenta")
    resources_table.add_column("Resource URI", style="cyan")
    resources_table.add_column("Name", style="white")
    
    for resource in server.resources:
        resources_table.add_row(str(resource.uri), resource.name or "No name")
    
    console.print(resources_table)
    
    # Demo tool calls
    console.print("\n[bold]Tool Demonstrations:[/bold]")
    
    # Math operations
    console.print("\n1️⃣  [cyan]Math Operations[/cyan]")
    result = await mcp_manager.call_tool("example", "add", {"a": 42, "b": 17})
    console.print(f"   add(42, 17) = {result[0].text}")
    
    result = await mcp_manager.call_tool("example", "multiply", {"a": 7.5, "b": 4})
    console.print(f"   multiply(7.5, 4) = {result[0].text}")
    
    # Dice rolling
    console.print("\n2️⃣  [cyan]Dice Rolling[/cyan]")
    result = await mcp_manager.call_tool("example", "roll_dice", {"sides": 20, "count": 3})
    dice_data = json.loads(result[0].text)
    console.print(f"   Rolling 3d20: {dice_data['rolls']} = {dice_data['total']}")
    
    # Echo
    console.print("\n3️⃣  [cyan]Echo Service[/cyan]")
    result = await mcp_manager.call_tool("example", "echo", {"message": "Hello MCP!", "uppercase": True})
    console.print(f"   echo('Hello MCP!', uppercase=True) = '{result[0].text}'")
    
    # Demo resource reading
    console.print("\n[bold]Resource Access:[/bold]")
    
    result = await mcp_manager.read_resource("example", "resource://server/info")
    info = json.loads(result[0].text)
    console.print(f"\n📋 Server Info: {json.dumps(info, indent=2)}")
    
    # Disconnect
    await mcp_manager.disconnect_server("example")
    console.print("\n[green]✅ Demo completed![/green]")
    
    console.print("\n[bold]To launch the full UI:[/bold]")
    console.print("  ./run.sh")
    console.print("  or")
    console.print("  uv run python src/main.py")


if __name__ == "__main__":
    asyncio.run(demo())