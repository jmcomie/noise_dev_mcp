"""
Logging configuration and utilities for Gradio MCP UI.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque
import asyncio

from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme


# Custom theme for rich logging
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "critical": "red bold reverse",
    "debug": "dim",
    "server": "green",
})


class LogCollector:
    """Collects logs for display in the UI."""
    
    def __init__(self, max_logs: int = 1000):
        self.logs: deque = deque(maxlen=max_logs)
        self._handlers: List[Any] = []
    
    def add_log(self, record: logging.LogRecord):
        """Add a log record to the collection."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "server": getattr(record, 'server', None)
        }
        self.logs.append(log_entry)
        
        # Notify handlers
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(log_entry))
                else:
                    handler(log_entry)
            except Exception:
                pass
    
    def get_logs(self, 
                 level: Optional[str] = None,
                 server: Optional[str] = None,
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get filtered logs."""
        logs = list(self.logs)
        
        # Filter by level
        if level:
            logs = [log for log in logs if log["level"] == level]
        
        # Filter by server
        if server:
            logs = [log for log in logs if log.get("server") == server]
        
        # Limit results
        if limit:
            logs = logs[-limit:]
        
        return logs
    
    def clear(self):
        """Clear all logs."""
        self.logs.clear()
    
    def add_handler(self, handler):
        """Add a log handler."""
        self._handlers.append(handler)
    
    def remove_handler(self, handler):
        """Remove a log handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)


class CollectorHandler(logging.Handler):
    """Logging handler that sends logs to a LogCollector."""
    
    def __init__(self, collector: LogCollector):
        super().__init__()
        self.collector = collector
    
    def emit(self, record):
        """Emit a log record."""
        try:
            self.collector.add_log(record)
        except Exception:
            self.handleError(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    collector: Optional[LogCollector] = None
) -> LogCollector:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        collector: Optional LogCollector instance (creates new if not provided)
    
    Returns:
        LogCollector instance
    """
    # Create console for rich logging
    console = Console(theme=custom_theme)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add rich console handler
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create or use provided collector
    if collector is None:
        collector = LogCollector()
    
    # Add collector handler
    collector_handler = CollectorHandler(collector)
    collector_handler.setLevel(logging.DEBUG)  # Collect all logs
    root_logger.addHandler(collector_handler)
    
    # Configure specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    return collector


class ServerLogAdapter(logging.LoggerAdapter):
    """Adds server name to log records."""
    
    def process(self, msg, kwargs):
        """Add server name to the log record."""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['server'] = self.extra.get('server', 'unknown')
        return msg, kwargs


def get_server_logger(name: str, server: str) -> logging.LoggerAdapter:
    """
    Get a logger adapter that includes server name in logs.
    
    Args:
        name: Logger name
        server: Server name
    
    Returns:
        Logger adapter with server context
    """
    logger = logging.getLogger(name)
    return ServerLogAdapter(logger, {'server': server})