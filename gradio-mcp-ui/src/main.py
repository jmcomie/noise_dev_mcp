#!/usr/bin/env python3
"""
Main entry point for the Gradio MCP UI application.
"""

import asyncio
import argparse
import logging
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_manager import MCPManager
from src.ui.chat_interface import ChatInterface
from src.utils.logging import setup_logging, LogCollector

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Gradio MCP UI - Interactive interface for MCP servers"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("servers/config.yaml"),
        help="Path to server configuration file (default: servers/config.yaml)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the Gradio interface on (default: 7860)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the interface to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Path to log file (optional)"
    )
    
    return parser.parse_args()


async def main():
    """Main application entry point."""
    args = parse_args()
    
    # Set up logging
    log_collector = setup_logging(
        log_level=args.log_level,
        log_file=args.log_file
    )
    
    logger.info("Starting Gradio MCP UI")
    logger.info(f"Configuration file: {args.config}")
    
    # Create MCP manager
    mcp_manager = MCPManager()
    
    # Load configuration
    try:
        if args.config.exists():
            await mcp_manager.load_config(args.config)
            logger.info(f"Loaded configuration from {args.config}")
        else:
            logger.warning(f"Configuration file not found: {args.config}")
            logger.info("Creating default configuration...")
            
            # Create a default configuration
            default_config = {
                "mcpServers": {
                    "example": {
                        "command": "python",
                        "args": ["./servers/example_server.py"]
                    }
                }
            }
            mcp_manager.load_config_dict(default_config)
            
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Set up log handler for MCP servers
    async def server_log_handler(server_name: str, message):
        """Handle logs from MCP servers."""
        server_logger = logging.getLogger(f"mcp.{server_name}")
        if hasattr(message, 'level'):
            level = getattr(logging, message.level.upper(), logging.INFO)
        else:
            level = logging.INFO
        
        server_logger.log(level, str(message))
    
    mcp_manager.add_log_handler(server_log_handler)
    
    # Create chat interface
    chat_interface = ChatInterface(mcp_manager)
    interface = chat_interface.create_interface()
    
    # Auto-connect to servers if specified
    if os.getenv("MCP_AUTO_CONNECT", "").lower() == "true":
        logger.info("Auto-connecting to all configured servers...")
        results = await mcp_manager.connect_all()
        for server, success in results.items():
            if success:
                logger.info(f"✅ Connected to {server}")
            else:
                logger.warning(f"❌ Failed to connect to {server}")
    
    # Launch the interface
    logger.info(f"Launching Gradio interface on {args.host}:{args.port}")
    
    try:
        # Run the interface in a separate thread to keep async loop available
        interface.launch(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            inbrowser=True,
            show_error=True
        )
        
        # Keep the main loop running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await mcp_manager.disconnect_all()
    except Exception as e:
        logger.error(f"Application error: {e}")
        await mcp_manager.disconnect_all()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)