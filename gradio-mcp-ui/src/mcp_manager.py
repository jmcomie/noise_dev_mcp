"""
MCP Manager - Handles connections to multiple MCP servers using FastMCP.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

from fastmcp import Client
from mcp.types import Tool, Resource, Prompt
from pydantic import BaseModel
import yaml

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    transport: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    auth: Optional[str] = None


class MCPConfig(BaseModel):
    """Configuration for all MCP servers."""
    mcpServers: Dict[str, ServerConfig]


class ServerConnection:
    """Represents a connection to a single MCP server."""
    
    def __init__(self, name: str, config: ServerConfig, client: Client):
        self.name = name
        self.config = config
        self.client = client
        self.connected = False
        self.last_error: Optional[str] = None
        self.tools: List[Tool] = []
        self.resources: List[Resource] = []
        self.prompts: List[Prompt] = []
        self.last_ping: Optional[datetime] = None
    
    async def connect(self) -> bool:
        """Connect to the server."""
        try:
            await self.client.__aenter__()
            self.connected = True
            self.last_error = None
            
            # Load available capabilities
            self.tools = await self.client.list_tools()
            self.resources = await self.client.list_resources()
            self.prompts = await self.client.list_prompts()
            
            self.last_ping = datetime.now()
            logger.info(f"Connected to server '{self.name}'")
            return True
            
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            logger.error(f"Failed to connect to server '{self.name}': {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.connected:
            try:
                await self.client.__aexit__(None, None, None)
                self.connected = False
                logger.info(f"Disconnected from server '{self.name}'")
            except Exception as e:
                logger.error(f"Error disconnecting from server '{self.name}': {e}")
    
    async def ping(self) -> bool:
        """Ping the server to check connection."""
        if not self.connected:
            return False
        
        try:
            await self.client.ping()
            self.last_ping = datetime.now()
            return True
        except Exception as e:
            logger.warning(f"Ping failed for server '{self.name}': {e}")
            return False


class MCPManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self):
        self.servers: Dict[str, ServerConnection] = {}
        self.config: Optional[MCPConfig] = None
        self._log_handlers: List[Any] = []
    
    async def load_config(self, config_path: Path) -> None:
        """Load server configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            self.config = MCPConfig(**config_data)
            logger.info(f"Loaded configuration with {len(self.config.mcpServers)} servers")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def load_config_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load server configuration from dictionary."""
        self.config = MCPConfig(**config_dict)
        logger.info(f"Loaded configuration with {len(self.config.mcpServers)} servers")
    
    async def connect_server(self, name: str) -> bool:
        """Connect to a specific server."""
        if not self.config or name not in self.config.mcpServers:
            logger.error(f"Server '{name}' not found in configuration")
            return False
        
        # Disconnect if already connected
        if name in self.servers:
            await self.disconnect_server(name)
        
        server_config = self.config.mcpServers[name]
        
        # Create client based on configuration
        try:
            # Build transport configuration
            if server_config.command:
                # Local stdio server
                # For FastMCP Client, we can pass the command and args directly
                # FastMCP will infer the correct transport
                if server_config.command == "python" and server_config.args:
                    # Pass the Python script path directly
                    client = Client(server_config.args[0])
                else:
                    # Build full command
                    transport_config = {
                        "command": server_config.command,
                        "args": server_config.args or [],
                        "env": server_config.env,
                        "cwd": server_config.cwd
                    }
                    client = Client(transport_config)
            elif server_config.url:
                # Remote HTTP/SSE server
                client = Client(server_config.url)
            else:
                raise ValueError(f"Server '{name}' has no command or URL specified")
            
            # Create server connection
            connection = ServerConnection(name, server_config, client)
            
            # Set up log handler
            async def log_handler(message):
                logger.debug(f"[{name}] {message}")
                for handler in self._log_handlers:
                    await handler(name, message)
            
            # Configure client handlers
            if hasattr(client, 'log_handler'):
                client.log_handler = log_handler
            
            # Connect
            success = await connection.connect()
            if success:
                self.servers[name] = connection
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create client for server '{name}': {e}")
            return False
    
    async def disconnect_server(self, name: str) -> None:
        """Disconnect from a specific server."""
        if name in self.servers:
            await self.servers[name].disconnect()
            del self.servers[name]
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all configured servers."""
        if not self.config:
            logger.error("No configuration loaded")
            return {}
        
        results = {}
        for name in self.config.mcpServers:
            results[name] = await self.connect_server(name)
        
        return results
    
    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for name in list(self.servers.keys()):
            await self.disconnect_server(name)
    
    def get_server(self, name: str) -> Optional[ServerConnection]:
        """Get a connected server by name."""
        return self.servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all configured server names."""
        if not self.config:
            return []
        return list(self.config.mcpServers.keys())
    
    def list_connected_servers(self) -> List[str]:
        """List all connected server names."""
        return [name for name, conn in self.servers.items() if conn.connected]
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a specific server."""
        server = self.get_server(server_name)
        if not server or not server.connected:
            raise ValueError(f"Server '{server_name}' is not connected")
        
        return await server.client.call_tool(tool_name, arguments)
    
    async def read_resource(self, server_name: str, uri: str) -> Any:
        """Read a resource from a specific server."""
        server = self.get_server(server_name)
        if not server or not server.connected:
            raise ValueError(f"Server '{server_name}' is not connected")
        
        return await server.client.read_resource(uri)
    
    async def get_prompt(self, server_name: str, prompt_name: str, arguments: Dict[str, Any]) -> Any:
        """Get a prompt from a specific server."""
        server = self.get_server(server_name)
        if not server or not server.connected:
            raise ValueError(f"Server '{server_name}' is not connected")
        
        return await server.client.get_prompt(prompt_name, arguments)
    
    def add_log_handler(self, handler) -> None:
        """Add a log handler function that receives (server_name, message)."""
        self._log_handlers.append(handler)
    
    def remove_log_handler(self, handler) -> None:
        """Remove a log handler."""
        if handler in self._log_handlers:
            self._log_handlers.remove(handler)
    
    async def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers."""
        status = {}
        
        for name in self.list_servers():
            if name in self.servers:
                conn = self.servers[name]
                status[name] = {
                    "connected": conn.connected,
                    "last_error": conn.last_error,
                    "last_ping": conn.last_ping.isoformat() if conn.last_ping else None,
                    "tools_count": len(conn.tools),
                    "resources_count": len(conn.resources),
                    "prompts_count": len(conn.prompts)
                }
            else:
                status[name] = {
                    "connected": False,
                    "last_error": "Not connected",
                    "last_ping": None,
                    "tools_count": 0,
                    "resources_count": 0,
                    "prompts_count": 0
                }
        
        return status