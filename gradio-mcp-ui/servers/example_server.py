#!/usr/bin/env python3
"""
Example MCP server using FastMCP demonstrating various capabilities.
"""

from fastmcp import FastMCP
import random
import datetime
from typing import Dict, List
import json

# Create the server instance
mcp = FastMCP(
    name="Example Server",
    instructions="""
    This is an example MCP server demonstrating various capabilities:
    - Tools for calculations and utilities
    - Resources for data access
    - Prompts for guided interactions
    """
)

# Tool examples
@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integer numbers together."""
    return a + b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

@mcp.tool
def roll_dice(sides: int = 6, count: int = 1) -> Dict[str, any]:
    """Roll dice with specified number of sides.
    
    Args:
        sides: Number of sides on each die (default: 6)
        count: Number of dice to roll (default: 1)
    
    Returns:
        Dictionary with individual rolls and total
    """
    rolls = [random.randint(1, sides) for _ in range(count)]
    return {
        "rolls": rolls,
        "total": sum(rolls),
        "sides": sides,
        "count": count
    }

@mcp.tool
def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in the specified timezone.
    
    Args:
        timezone: Timezone name (default: UTC)
    
    Returns:
        ISO format timestamp
    """
    # For simplicity, just return UTC time
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

@mcp.tool 
def echo(message: str, uppercase: bool = False) -> str:
    """Echo back the provided message.
    
    Args:
        message: The message to echo
        uppercase: Whether to convert to uppercase
    
    Returns:
        The echoed message
    """
    return message.upper() if uppercase else message

# Resource examples
@mcp.resource("resource://server/info")
def get_server_info() -> dict:
    """Get information about this server."""
    return {
        "name": "Example MCP Server",
        "version": "1.0.0",
        "capabilities": ["tools", "resources", "prompts"],
        "author": "Gradio MCP UI Demo"
    }

@mcp.resource("resource://data/sample")
def get_sample_data() -> dict:
    """Get sample data for testing."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
            {"id": 3, "name": "Charlie", "role": "user"}
        ],
        "timestamp": datetime.datetime.now().isoformat()
    }

@mcp.resource("resource://config/settings")
def get_settings() -> dict:
    """Get server configuration settings."""
    return {
        "debug": False,
        "max_connections": 10,
        "timeout": 30,
        "features": {
            "logging": True,
            "caching": False,
            "authentication": False
        }
    }

# Dynamic resource with parameters
@mcp.resource("data://random/{count}")
def get_random_numbers(count: str) -> dict:
    """Generate random numbers.
    
    Args:
        count: Number of random values to generate
    """
    try:
        n = int(count)
        if n < 1 or n > 100:
            return {"error": "Count must be between 1 and 100"}
        
        return {
            "count": n,
            "values": [random.random() for _ in range(n)],
            "generated_at": datetime.datetime.now().isoformat()
        }
    except ValueError:
        return {"error": "Invalid count parameter"}

# Prompt examples
@mcp.prompt
def calculation_prompt(operation: str) -> List[dict]:
    """Generate a calculation prompt based on operation."""
    if operation == "add":
        return [{
            "role": "user",
            "content": "I need to add two numbers. First number is 15 and second is 27. What's the result?"
        }]
    elif operation == "multiply":
        return [{
            "role": "user", 
            "content": "Please multiply 12 by 8 and tell me the result."
        }]
    else:
        return [{
            "role": "user",
            "content": f"Help me perform a {operation} calculation."
        }]

@mcp.prompt
def greeting_prompt(name: str = "friend") -> List[dict]:
    """Generate a personalized greeting."""
    return [{
        "role": "system",
        "content": "You are a friendly assistant."
    }, {
        "role": "user",
        "content": f"Please greet {name} warmly and ask how you can help them today."
    }]

# Run the server
if __name__ == "__main__":
    # Server can be run with different transports
    # Default is stdio for use with clients
    mcp.run()