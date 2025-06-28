"""
MCP Manager - Handles connections to multiple MCP servers using FastMCP.
"""

import asyncio
import json
import aiohttp
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


class HTTPMCPClient:
    """HTTP client for MCP servers."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _request(self, method: str, endpoint: str, data: Any = None) -> Any:
        """Make HTTP request to the MCP server."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(
                method, url, 
                json=data if data else None,
                headers={'Content-Type': 'application/json'} if data else None
            ) as response:
                response.raise_for_status()
                
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return await response.text()
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
    
    async def list_tools(self) -> List[Tool]:
        """List available tools."""
        try:
            response = await self._request('GET', '/capabilities')
            tools_data = response.get('tools', [])
            
            tools = []
            for tool_data in tools_data:
                # Create Tool object from response
                tool = Tool(
                    name=tool_data.get('name', ''),
                    description=tool_data.get('description', ''),
                    inputSchema=tool_data.get('inputSchema', {})
                )
                tools.append(tool)
            
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def list_resources(self) -> List[Resource]:
        """List available resources."""
        try:
            response = await self._request('GET', '/capabilities')
            resources_data = response.get('resources', [])
            
            resources = []
            for resource_data in resources_data:
                # Create Resource object from response
                resource = Resource(
                    uri=resource_data.get('uri', ''),
                    name=resource_data.get('name', ''),
                    description=resource_data.get('description', ''),
                    mimeType=resource_data.get('mimeType', 'text/plain')
                )
                resources.append(resource)
            
            return resources
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            return []
    
    async def list_prompts(self) -> List[Prompt]:
        """List available prompts."""
        try:
            response = await self._request('GET', '/capabilities')
            prompts_data = response.get('prompts', [])
            
            prompts = []
            for prompt_data in prompts_data:
                # Create Prompt object from response
                prompt = Prompt(
                    name=prompt_data.get('name', ''),
                    description=prompt_data.get('description', ''),
                    arguments=prompt_data.get('arguments', [])
                )
                prompts.append(prompt)
            
            return prompts
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the server."""
        data = {
            "name": tool_name,
            "arguments": arguments
        }
        return await self._request('POST', '/execute', data)
    
    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the server."""
        # For our TypeScript servers, resources are accessed via GET requests
        # Extract the resource path from the URI
        resource_path = uri.replace('resource://', '')
        return await self._request('GET', f'/resources/{resource_path}')
    
    async def get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Any:
        """Get a prompt from the server."""
        data = {
            "name": prompt_name,
            "arguments": arguments
        }
        return await self._request('POST', '/prompts', data)
    
    async def ping(self) -> bool:
        """Ping the server."""
        try:
            await self._request('GET', '/health')
            return True
        except Exception:
            return False


class ServerConnection:
    """Represents a connection to a single MCP server."""
    
    def __init__(self, name: str, config: ServerConfig, client: Any):
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
            logger.info(f"Connected to server '{self.name}' - Tools: {len(self.tools)}, Resources: {len(self.resources)}, Prompts: {len(self.prompts)}")
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
            result = await self.client.ping()
            self.last_ping = datetime.now()
            return result
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
            if server_config.url and server_config.transport == 'http':
                # HTTP MCP server
                client = HTTPMCPClient(server_config.url, server_config.headers)
                logger.info(f"Created HTTP client for server '{name}' at {server_config.url}")
            elif server_config.command:
                # Local stdio server
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
                logger.info(f"Created stdio client for server '{name}' with command '{server_config.command}'")
            elif server_config.url:
                # Try FastMCP client for other URL types
                client = Client(server_config.url)
                logger.info(f"Created FastMCP client for server '{name}' at {server_config.url}")
            else:
                raise ValueError(f"Server '{name}' has no command or URL specified")
            
            # Create server connection
            connection = ServerConnection(name, server_config, client)
            
            # Set up log handler
            async def log_handler(message):
                logger.debug(f"[{name}] {message}")
                for handler in self._log_handlers:
                    await handler(name, message)
            
            # Configure client handlers (only for FastMCP clients)
            if hasattr(client, 'log_handler') and not isinstance(client, HTTPMCPClient):
                client.log_handler = log_handler
            
            # Connect
            success = await connection.connect()
            if success:
                self.servers[name] = connection
                logger.info(f"Successfully connected to server '{name}'")
            else:
                logger.error(f"Failed to connect to server '{name}': {connection.last_error}")
            
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