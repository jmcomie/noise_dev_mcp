"""
Chat Interface component for Gradio MCP UI.
"""

import gradio as gr
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import json
import logging
from datetime import datetime

from ..mcp_manager import MCPManager

logger = logging.getLogger(__name__)


class ChatInterface:
    """Manages the chat interface for interacting with MCP servers."""
    
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        with gr.Blocks(title="MCP Chat Interface", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🤖 MCP Multi-Server Chat Interface")
            gr.Markdown("Connect to and interact with multiple MCP servers through a unified interface.")
            
            with gr.Row():
                # Left sidebar for server selection and status
                with gr.Column(scale=1):
                    gr.Markdown("## Server Management")
                    
                    # Server selector
                    server_dropdown = gr.Dropdown(
                        label="Select Server",
                        choices=self.mcp_manager.list_servers(),
                        value=self.mcp_manager.list_servers()[0] if self.mcp_manager.list_servers() else None,
                        interactive=True
                    )
                    
                    # Connection status
                    status_text = gr.Textbox(
                        label="Connection Status",
                        value="Not connected",
                        interactive=False,
                        lines=2
                    )
                    
                    # Connect/Disconnect buttons
                    with gr.Row():
                        connect_btn = gr.Button("Connect", variant="primary", scale=1)
                        disconnect_btn = gr.Button("Disconnect", variant="stop", scale=1)
                    
                    # Server capabilities
                    gr.Markdown("### Server Capabilities")
                    capabilities_info = gr.JSON(
                        label="Available Tools & Resources",
                        value={}
                    )
                    
                # Main chat area
                with gr.Column(scale=3):
                    # Chat interface
                    chatbot = gr.Chatbot(
                        value=[],
                        height=500,
                        type="messages",
                        show_copy_button=True,
                        avatar_images=("👤", "🤖")
                    )
                    
                    # Input area
                    with gr.Row():
                        msg_input = gr.Textbox(
                            label="Message",
                            placeholder="Type your message or use a tool...",
                            lines=2,
                            scale=4
                        )
                        
                    with gr.Row():
                        send_btn = gr.Button("Send", variant="primary", scale=1)
                        clear_btn = gr.Button("Clear", scale=1)
                    
                    # Tool usage section
                    with gr.Accordion("Tool Usage", open=False):
                        tool_dropdown = gr.Dropdown(
                            label="Select Tool",
                            choices=[],
                            interactive=True
                        )
                        
                        tool_args = gr.JSON(
                            label="Tool Arguments",
                            value={}
                        )
                        
                        execute_tool_btn = gr.Button("Execute Tool", variant="secondary")
                        
                    # Resource access section
                    with gr.Accordion("Resource Access", open=False):
                        resource_dropdown = gr.Dropdown(
                            label="Select Resource",
                            choices=[],
                            interactive=True
                        )
                        
                        read_resource_btn = gr.Button("Read Resource", variant="secondary")
            
            # Event handlers
            
            async def connect_server(server_name):
                """Connect to selected server."""
                if not server_name:
                    return "No server selected", {}, [], []
                
                try:
                    success = await self.mcp_manager.connect_server(server_name)
                    if success:
                        server = self.mcp_manager.get_server(server_name)
                        
                        # Get capabilities
                        capabilities = {
                            "tools": [{"name": t.name, "description": t.description} for t in server.tools],
                            "resources": [{"uri": r.uri, "name": r.name} for r in server.resources],
                            "prompts": [{"name": p.name, "description": p.description} for p in server.prompts]
                        }
                        
                        # Update dropdowns
                        tool_choices = [t.name for t in server.tools]
                        resource_choices = [r.uri for r in server.resources]
                        
                        return f"✅ Connected to {server_name}", capabilities, tool_choices, resource_choices
                    else:
                        server = self.mcp_manager.get_server(server_name)
                        error = server.last_error if server else "Unknown error"
                        return f"❌ Failed to connect: {error}", {}, [], []
                        
                except Exception as e:
                    logger.error(f"Connection error: {e}")
                    return f"❌ Error: {str(e)}", {}, [], []
            
            async def disconnect_server(server_name):
                """Disconnect from selected server."""
                if not server_name:
                    return "No server selected", {}, [], []
                
                try:
                    await self.mcp_manager.disconnect_server(server_name)
                    return f"Disconnected from {server_name}", {}, [], []
                except Exception as e:
                    return f"❌ Error: {str(e)}", {}, [], []
            
            async def send_message(message, history, server_name):
                """Process and send a message."""
                if not message or not server_name:
                    return history, ""
                
                # Add user message to history
                history = history + [{"role": "user", "content": message}]
                
                # Check if server is connected
                server = self.mcp_manager.get_server(server_name)
                if not server or not server.connected:
                    history = history + [{"role": "assistant", "content": f"❌ Server '{server_name}' is not connected."}]
                    return history, ""
                
                # For now, just echo the message with server info
                # In a real implementation, you might call a chat tool if available
                response = f"[{server_name}] Received: {message}\n\nAvailable tools: {', '.join([t.name for t in server.tools])}"
                history = history + [{"role": "assistant", "content": response}]
                
                return history, ""
            
            async def execute_tool(server_name, tool_name, tool_args_json, history):
                """Execute a tool on the server."""
                if not server_name or not tool_name:
                    return history
                
                try:
                    # Parse arguments
                    args = json.loads(tool_args_json) if isinstance(tool_args_json, str) else tool_args_json
                    
                    # Execute tool
                    result = await self.mcp_manager.call_tool(server_name, tool_name, args)
                    
                    # Format result
                    if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                        # Handle list of results
                        formatted_result = "\n".join([str(r) for r in result])
                    else:
                        formatted_result = str(result)
                    
                    # Add to history
                    tool_message = f"🔧 Executed tool: {tool_name}\nArguments: {json.dumps(args, indent=2)}"
                    result_message = f"✅ Result:\n{formatted_result}"
                    
                    history = history + [
                        {"role": "user", "content": tool_message},
                        {"role": "assistant", "content": result_message}
                    ]
                    
                except Exception as e:
                    error_message = f"❌ Error executing tool: {str(e)}"
                    history = history + [{"role": "assistant", "content": error_message}]
                
                return history
            
            async def read_resource(server_name, resource_uri, history):
                """Read a resource from the server."""
                if not server_name or not resource_uri:
                    return history
                
                try:
                    result = await self.mcp_manager.read_resource(server_name, resource_uri)
                    
                    # Format result
                    if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                        formatted_result = "\n".join([str(r) for r in result])
                    else:
                        formatted_result = str(result)
                    
                    # Add to history
                    resource_message = f"📄 Reading resource: {resource_uri}"
                    result_message = f"✅ Content:\n{formatted_result}"
                    
                    history = history + [
                        {"role": "user", "content": resource_message},
                        {"role": "assistant", "content": result_message}
                    ]
                    
                except Exception as e:
                    error_message = f"❌ Error reading resource: {str(e)}"
                    history = history + [{"role": "assistant", "content": error_message}]
                
                return history
            
            def clear_chat():
                """Clear the chat history."""
                return []
            
            # Connect event handlers
            connect_btn.click(
                fn=lambda server: asyncio.run(connect_server(server)),
                inputs=[server_dropdown],
                outputs=[status_text, capabilities_info, tool_dropdown, resource_dropdown]
            )
            
            disconnect_btn.click(
                fn=lambda server: asyncio.run(disconnect_server(server)),
                inputs=[server_dropdown],
                outputs=[status_text, capabilities_info, tool_dropdown, resource_dropdown]
            )
            
            msg_input.submit(
                fn=lambda msg, hist, server: asyncio.run(send_message(msg, hist, server)),
                inputs=[msg_input, chatbot, server_dropdown],
                outputs=[chatbot, msg_input]
            )
            
            send_btn.click(
                fn=lambda msg, hist, server: asyncio.run(send_message(msg, hist, server)),
                inputs=[msg_input, chatbot, server_dropdown],
                outputs=[chatbot, msg_input]
            )
            
            clear_btn.click(
                fn=clear_chat,
                outputs=[chatbot]
            )
            
            execute_tool_btn.click(
                fn=lambda server, tool, args, hist: asyncio.run(execute_tool(server, tool, args, hist)),
                inputs=[server_dropdown, tool_dropdown, tool_args, chatbot],
                outputs=[chatbot]
            )
            
            read_resource_btn.click(
                fn=lambda server, resource, hist: asyncio.run(read_resource(server, resource, hist)),
                inputs=[server_dropdown, resource_dropdown, chatbot],
                outputs=[chatbot]
            )
            
        return interface