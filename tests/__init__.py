"""
Athena DeFi Agent Test Suite

This package contains comprehensive tests for the Athena DeFi Agent:
- Unit tests for individual components
- Integration tests for component interactions  
- End-to-end tests for full agent lifecycle

Test Categories:
- Treasury management and survival mechanisms
- Memory formation and retrieval
- Market condition detection and analysis
- LangGraph workflow execution
- Agent orchestration and decision making
- Cost optimization and emergency responses

Run with: pytest
"""

import os
import sys

# Add src directory to Python path for imports
test_dir = os.path.dirname(__file__)
project_root = os.path.dirname(test_dir)
src_dir = os.path.join(project_root, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)