#!/bin/bash
# Launch the Gradio MCP UI

echo "🚀 Starting Gradio MCP UI..."
echo "📍 URL: http://127.0.0.1:7860"
echo "Press Ctrl+C to stop"
echo ""

uv run python src/main.py "$@"