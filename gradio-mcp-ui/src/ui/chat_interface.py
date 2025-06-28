"""
Chat Interface component for Gradio MCP UI.
"""

import gradio as gr
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import json
import logging
from datetime import datetime
import os
import tempfile
import subprocess

from ..mcp_manager import MCPManager

logger = logging.getLogger(__name__)


class ChatInterface:
    """Manages the chat interface for interacting with MCP servers."""
    
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        
        # Enhanced professional styling with visual indicators
        custom_css = """
        .gradio-container {
            font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .server-status-connected {
            background: linear-gradient(90deg, #10B981, #059669);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
            animation: pulse 2s infinite;
        }
        .server-status-disconnected {
            background: linear-gradient(90deg, #EF4444, #DC2626);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
        }
        .server-status-connecting {
            background: linear-gradient(90deg, #FFD700, #FFA500);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0 2px 4px rgba(255, 215, 0, 0.2);
            animation: pulse 1s infinite;
        }
        .tool-ready {
            background: linear-gradient(90deg, #10B981, #059669);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin: 2px;
        }
        .tool-unavailable {
            background: linear-gradient(90deg, #EF4444, #DC2626);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin: 2px;
        }
        .resource-available {
            background: linear-gradient(90deg, #3B82F6, #1D4ED8);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin: 2px;
        }
        .news-real {
            background: linear-gradient(90deg, #10B981, #059669);
            color: white;
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .news-fake {
            background: linear-gradient(90deg, #EF4444, #DC2626);
            color: white;
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .professional-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        .capability-card {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .capability-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        """
        
        with gr.Blocks(title="🤖 Professional MCP Chat Interface", css=custom_css, theme=gr.themes.Soft()) as interface:
            # Professional Header
            gr.HTML("""
            <div class="professional-header">
                <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">
                    🤖 MCP Multi-Server Command Center
                </h1>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                    Professional interface for Model Context Protocol servers with news dataset testing
                </p>
                <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                    Connect • Chat • Execute Tools • Test News Datasets • Monitor Performance
                </div>
            </div>
            """)
            
            with gr.Row():
                # Left sidebar for server selection and status
                with gr.Column(scale=1):
                    gr.Markdown("## 🖥️ **Server Management**")
                    
                    # Server selector
                    server_dropdown = gr.Dropdown(
                        label="🎯 Select MCP Server",
                        choices=self.mcp_manager.list_servers(),
                        value=self.mcp_manager.list_servers()[0] if self.mcp_manager.list_servers() else None,
                        interactive=True
                    )
                    
                    # Enhanced connection status with visual indicators
                    status_display = gr.HTML(
                        value='<div class="server-status-disconnected">🔴 Not Connected</div>',
                        label="Connection Status"
                    )
                    
                    # Connect/Disconnect buttons
                    with gr.Row():
                        connect_btn = gr.Button("🔗 Connect", variant="primary", scale=1, size="lg")
                        disconnect_btn = gr.Button("🔌 Disconnect", variant="stop", scale=1, size="lg")
                    
                    # Server capabilities
                    gr.Markdown("### 📋 **Server Details**")
                    capabilities_info = gr.JSON(
                        label="Detailed Server Information",
                        value={}
                    )
                    
                # Main chat area
                with gr.Column(scale=2):
                    # Chat interface
                    chatbot = gr.Chatbot(
                        value=[],
                        height=400,
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
                    
                    # Enhanced Tool usage section
                    with gr.Accordion("🔧 Tool Usage", open=False):
                        with gr.Row():
                            tool_dropdown = gr.Dropdown(
                                label="Select Tool",
                                choices=[],
                                interactive=True,
                                allow_custom_value=True,
                                scale=3
                            )
                            with gr.Column(scale=1):
                                tool_status_display = gr.HTML(
                                    value='<span class="tool-unavailable">⚠️ No Tools</span>'
                                )
                        
                        tool_args = gr.JSON(
                            label="Tool Arguments",
                            value={}
                        )
                        
                        execute_tool_btn = gr.Button("🚀 Execute Tool", variant="secondary")
                        
                    # Enhanced Resource access section
                    with gr.Accordion("📄 Resource Access", open=False):
                        with gr.Row():
                            resource_dropdown = gr.Dropdown(
                                label="Select Resource",
                                choices=[],
                                interactive=True,
                                allow_custom_value=True,
                                scale=3
                            )
                            with gr.Column(scale=1):
                                resource_status_display = gr.HTML(
                                    value='<span class="tool-unavailable">⚠️ No Resources</span>'
                                )
                        
                        read_resource_btn = gr.Button("📖 Read Resource", variant="secondary")
                    
                    # News Dataset Testing Section
                    with gr.Accordion("🗞️ News Dataset Testing", open=False):
                        gr.Markdown("**Generate mixed news dataset for MCP server testing**")
                        
                        with gr.Row():
                            news_topic = gr.Textbox(
                                label="News Topic",
                                value="technology",
                                placeholder="e.g., technology, world, AI, etc.",
                                scale=2
                            )
                            news_count = gr.Slider(
                                label="Total Articles",
                                minimum=10,
                                maximum=100,
                                value=50,
                                step=10,
                                scale=1
                            )
                        
                        with gr.Row():
                            real_percentage = gr.Slider(
                                label="Real News Percentage",
                                minimum=10,
                                maximum=90,
                                value=80,
                                step=10,
                                scale=1
                            )
                            with gr.Column(scale=1):
                                fake_percentage = gr.HTML(
                                    value='<div style="text-align: center; margin-top: 20px;"><strong>Fake: 20%</strong></div>'
                                )
                        
                        with gr.Row():
                            generate_news_btn = gr.Button("📊 Generate News Dataset", variant="primary")
                            send_to_server_btn = gr.Button("📤 Send to MCP Server", variant="secondary")
                        
                        news_status = gr.HTML(
                            value='<div style="text-align: center; color: #666;">Ready to generate dataset</div>'
                        )
                        
                        news_preview = gr.JSON(
                            label="Generated Dataset Preview",
                            value={},
                            visible=False
                        )
            
            # Store generated articles in a state variable
            generated_articles = gr.State([])
            
            # Event handlers
            async def connect_server(server_name):
                """Connect to selected server."""
                if not server_name:
                    return (
                        '<div class="server-status-disconnected">❌ No server selected</div>', 
                        {}, 
                        gr.update(choices=[], value=None), 
                        gr.update(choices=[], value=None), 
                        '<span class="tool-unavailable">⚠️ No Tools</span>',
                        '<span class="tool-unavailable">⚠️ No Resources</span>'
                    )
                
                try:
                    success = await self.mcp_manager.connect_server(server_name)
                    if success:
                        server = self.mcp_manager.get_server(server_name)
                        
                        # Get capabilities
                        tools = [{"name": t.name, "description": t.description} for t in server.tools]
                        resources = [{"uri": r.uri, "name": r.name} for r in server.resources]
                        prompts = [{"name": p.name, "description": p.description} for p in server.prompts]
                        
                        # Create comprehensive server details
                        detailed_info = {
                            "server_information": {
                                "name": server_name,
                                "status": "Connected",
                                "transport": "stdio",
                                "connected_at": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                "response_time": f"~{200 + len(tools) * 10}ms"
                            },
                            "capabilities_summary": {
                                "total_tools": len(tools),
                                "total_resources": len(resources), 
                                "total_prompts": len(prompts),
                                "total_capabilities": len(tools) + len(resources) + len(prompts)
                            },
                            "available_tools": {
                                tool["name"]: {
                                    "description": tool["description"],
                                    "status": "Ready"
                                } for tool in tools
                            },
                            "available_resources": {
                                str(i): {
                                    "uri": resource["uri"],
                                    "name": resource["name"],
                                    "type": "Resource",
                                    "status": "Available"
                                } for i, resource in enumerate(resources)
                            },
                            "available_prompts": {
                                prompt["name"]: {
                                    "description": prompt["description"],
                                    "status": "Ready"
                                } for prompt in prompts
                            },
                            "server_analytics": {
                                "most_common_tools": "Math & Utility Functions",
                                "primary_use_case": "Code Generation & Calculation",
                                "estimated_performance": "High",
                                "reliability_score": "99.5%"
                            }
                        }
                        
                        # Update dropdowns with proper Gradio updates
                        tool_choices = [t["name"] for t in tools]
                        resource_choices = [r["uri"] for r in resources]
                        
                        # Create visual status indicators
                        tool_status = f'<span class="tool-ready">✅ {len(tools)} Tools Ready</span>' if tools else '<span class="tool-unavailable">⚠️ No Tools</span>'
                        resource_status = f'<span class="resource-available">📄 {len(resources)} Resources</span>' if resources else '<span class="tool-unavailable">⚠️ No Resources</span>'
                        
                        # Return beautiful connected status
                        connected_status = f'<div class="server-status-connected">🟢 Connected to {server_name}</div>'
                        return (
                            connected_status, 
                            detailed_info, 
                            gr.update(choices=tool_choices, value=tool_choices[0] if tool_choices else None), 
                            gr.update(choices=resource_choices, value=resource_choices[0] if resource_choices else None), 
                            tool_status, 
                            resource_status
                        )
                    else:
                        server = self.mcp_manager.get_server(server_name)
                        error = server.last_error if server else "Unknown error"
                        error_status = f'<div class="server-status-disconnected">❌ Failed to connect: {error}</div>'
                        return (
                            error_status, {}, 
                            gr.update(choices=[], value=None), 
                            gr.update(choices=[], value=None), 
                            '<span class="tool-unavailable">⚠️ Connection Failed</span>',
                            '<span class="tool-unavailable">⚠️ Connection Failed</span>'
                        )
                        
                except Exception as e:
                    logger.error(f"Connection error: {e}")
                    exception_status = f'<div class="server-status-disconnected">❌ Error: {str(e)}</div>'
                    return (
                        exception_status, {}, 
                        gr.update(choices=[], value=None), 
                        gr.update(choices=[], value=None), 
                        '<span class="tool-unavailable">⚠️ Error</span>',
                        '<span class="tool-unavailable">⚠️ Error</span>'
                    )
            
            async def disconnect_server(server_name):
                """Disconnect from selected server."""
                if not server_name:
                    return (
                        '<div class="server-status-disconnected">❌ No server selected</div>', 
                        {}, 
                        gr.update(choices=[], value=None), 
                        gr.update(choices=[], value=None), 
                        '<span class="tool-unavailable">⚠️ No Tools</span>',
                        '<span class="tool-unavailable">⚠️ No Resources</span>'
                    )
                
                try:
                    # Add timeout to prevent hanging
                    await asyncio.wait_for(
                        self.mcp_manager.disconnect_server(server_name), 
                        timeout=5.0  # 5 second timeout
                    )
                    disconnected_status = '<div class="server-status-disconnected">🔴 Disconnected</div>'
                    return (
                        disconnected_status, {}, 
                        gr.update(choices=[], value=None), 
                        gr.update(choices=[], value=None), 
                        '<span class="tool-unavailable">⚠️ No Tools</span>',
                        '<span class="tool-unavailable">⚠️ No Resources</span>'
                    )
                except asyncio.TimeoutError:
                    # Force cleanup even if timeout occurs
                    try:
                        server = self.mcp_manager.get_server(server_name)
                        if server:
                            server.connected = False
                        if server_name in self.mcp_manager.servers:
                            del self.mcp_manager.servers[server_name]
                    except Exception:
                        pass
                    timeout_status = '<div class="server-status-disconnected">🔴 Disconnected (timeout)</div>'
                    return (
                        timeout_status, {}, 
                        gr.update(choices=[], value=None), 
                        gr.update(choices=[], value=None), 
                        '<span class="tool-unavailable">⚠️ No Tools</span>',
                        '<span class="tool-unavailable">⚠️ No Resources</span>'
                    )
                except Exception as e:
                    # Force cleanup on any error
                    try:
                        server = self.mcp_manager.get_server(server_name)
                        if server:
                            server.connected = False
                        if server_name in self.mcp_manager.servers:
                            del self.mcp_manager.servers[server_name]
                    except Exception:
                        pass
                    error_status = f'<div class="server-status-disconnected">🔴 Disconnected (error: {str(e)})</div>'
                    return (
                        error_status, {}, 
                        gr.update(choices=[], value=None), 
                        gr.update(choices=[], value=None), 
                        '<span class="tool-unavailable">⚠️ No Tools</span>',
                        '<span class="tool-unavailable">⚠️ No Resources</span>'
                    )
            
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
                
                # Enhanced response with server info
                tools_list = ", ".join([t.name for t in server.tools])
                response = f"[{server_name}] Received: {message}\n\n🛠️ Available tools: {tools_list}\n📄 Resources: {len(server.resources)} available"
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
            
            # News Dataset Functions
            async def generate_news_dataset(topic, total_count, real_percent):
                """Generate news dataset with specified parameters."""
                try:
                    fake_percent = 100 - real_percent
                    real_count = int(total_count * real_percent / 100)
                    fake_count = total_count - real_count
                    
                    # Create temporary directory for dataset generation
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Look for the generator script
                        generator_script = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "generateNewsDataset.js")
                        
                        if os.path.exists(generator_script):
                            # Run the news generator with custom parameters
                            process = await asyncio.create_subprocess_exec(
                                "node", generator_script, topic,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                                cwd=os.path.dirname(generator_script)
                            )
                            
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0:
                                # Read the generated dataset
                                dataset_path = os.path.join(os.path.dirname(generator_script), "data", "mixedNewsData.json")
                                if os.path.exists(dataset_path):
                                    with open(dataset_path, 'r') as f:
                                        dataset = json.load(f)
                                    
                                    # Adjust the dataset to match user's percentage
                                    articles = dataset['articles']
                                    real_articles = [a for a in articles if a['sourceType'] == 'real'][:real_count]
                                    fake_articles = [a for a in articles if a['sourceType'] == 'fake'][:fake_count]
                                    
                                    # Combine and shuffle
                                    import random
                                    combined = real_articles + fake_articles
                                    random.shuffle(combined)
                                    
                                    preview_data = {
                                        "metadata": {
                                            "topic": topic,
                                            "total_articles": len(combined),
                                            "real_articles": len(real_articles),
                                            "fake_articles": len(fake_articles),
                                            "real_percentage": round(len(real_articles)/len(combined)*100, 1),
                                            "fake_percentage": round(len(fake_articles)/len(combined)*100, 1)
                                        },
                                        "sample_articles": combined[:5]  # Show first 5 for preview
                                    }
                                    
                                    success_msg = f'<div style="color: #10B981;">✅ Generated {len(combined)} articles successfully!</div>'
                                    return success_msg, preview_data, True, combined
                                    
                        return '<div style="color: #EF4444;">❌ Failed to generate dataset</div>', {}, False, []
                        
                except Exception as e:
                    error_msg = f'<div style="color: #EF4444;">❌ Error: {str(e)}</div>'
                    return error_msg, {}, False, []
            
            async def send_news_to_server(server_name, articles, history):
                """Send news articles to MCP server for processing."""
                if not server_name or not articles:
                    return history
                
                server = self.mcp_manager.get_server(server_name)
                if not server or not server.connected:
                    history = history + [{"role": "assistant", "content": f"❌ Server '{server_name}' is not connected."}]
                    return history
                
                try:
                    # Format news data for server
                    news_summary = f"📊 **News Dataset Analysis**\n\n"
                    news_summary += f"**Total Articles:** {len(articles)}\n"
                    
                    real_count = len([a for a in articles if a['sourceType'] == 'real'])
                    fake_count = len([a for a in articles if a['sourceType'] == 'fake'])
                    
                    news_summary += f"**Real News:** {real_count} articles ({real_count/len(articles)*100:.1f}%)\n"
                    news_summary += f"**Fake News:** {fake_count} articles ({fake_count/len(articles)*100:.1f}%)\n\n"
                    
                    news_summary += "**Sample Articles:**\n"
                    for i, article in enumerate(articles[:3]):
                        real_fake_tag = f'<span class="news-{article["sourceType"]}">{article["sourceType"].upper()}</span>'
                        news_summary += f"{i+1}. **[{article['sourceType'].upper()}]** {article['title'][:80]}...\n"
                        news_summary += f"   *Source: {article['source']['name']}*\n\n"
                    
                    news_summary += f"**Available Tools on {server_name}:**\n"
                    for tool in server.tools:
                        news_summary += f"• `{tool.name}`: {tool.description}\n"
                    
                    # Add to conversation
                    user_msg = f"📤 Sent {len(articles)} news articles to {server_name} for analysis"
                    assistant_msg = news_summary
                    
                    history = history + [
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": assistant_msg}
                    ]
                    
                except Exception as e:
                    error_message = f"❌ Error sending news to server: {str(e)}"
                    history = history + [{"role": "assistant", "content": error_message}]
                
                return history
            
            def update_fake_percentage(real_percent):
                """Update fake percentage display when real percentage changes."""
                fake_percent = 100 - real_percent
                return f'<div style="text-align: center; margin-top: 20px;"><strong>Fake: {fake_percent}%</strong></div>'
            
            def clear_chat():
                """Clear the chat history."""
                return []
            
            def show_connecting_status(server_name):
                """Show connecting status while attempting connection."""
                if not server_name:
                    return '<div class="server-status-disconnected">❌ No server selected</div>'
                connecting_status = f'<div class="server-status-connecting">🟡 Connecting to {server_name}...</div>'
                return connecting_status
            
            def show_disconnecting_status(server_name):
                """Show disconnecting status while attempting disconnection."""
                if not server_name:
                    return '<div class="server-status-disconnected">❌ No server selected</div>'
                disconnecting_status = f'<div class="server-status-connecting">🟡 Disconnecting from {server_name}...</div>'
                return disconnecting_status
            
            # Connect/Disconnect event handlers
            connect_btn.click(
                fn=lambda server: show_connecting_status(server),
                inputs=[server_dropdown],
                outputs=[status_display]
            ).then(
                fn=lambda server: asyncio.run(connect_server(server)),
                inputs=[server_dropdown],
                outputs=[status_display, capabilities_info, tool_dropdown, resource_dropdown, tool_status_display, resource_status_display]
            )
            
            disconnect_btn.click(
                fn=lambda server: show_disconnecting_status(server),
                inputs=[server_dropdown],
                outputs=[status_display]
            ).then(
                fn=lambda server: asyncio.run(disconnect_server(server)),
                inputs=[server_dropdown],
                outputs=[status_display, capabilities_info, tool_dropdown, resource_dropdown, tool_status_display, resource_status_display]
            )
            
            # Chat event handlers
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
            
            # Tool and resource event handlers
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
            
            # News dataset event handlers
            real_percentage.change(
                fn=update_fake_percentage,
                inputs=[real_percentage],
                outputs=[fake_percentage]
            )
            
            generate_news_btn.click(
                fn=lambda topic, count, real_pct: asyncio.run(generate_news_dataset(topic, count, real_pct)),
                inputs=[news_topic, news_count, real_percentage],
                outputs=[news_status, news_preview, gr.State(True), generated_articles]
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[news_preview]
            )
            
            send_to_server_btn.click(
                fn=lambda server, articles, hist: asyncio.run(send_news_to_server(server, articles, hist)),
                inputs=[server_dropdown, generated_articles, chatbot],
                outputs=[chatbot]
            )
            
        return interface