"""
LangSmith Configuration

Sets up tracing for LangGraph workflows and LLM calls.
"""

import logging
import os

from ..config import settings

logger = logging.getLogger(__name__)


def configure_langsmith():
    """Configure LangSmith for tracing"""
    
    if not settings.langsmith_api_key:
        logger.info("LangSmith API key not found - tracing disabled")
        return
    
    try:
        # Set environment variables for LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        
        logger.info(f"✅ LangSmith configured for project: {settings.langsmith_project}")
        
    except Exception as e:
        logger.error(f"Failed to configure LangSmith: {e}")
        # Continue without tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "false"