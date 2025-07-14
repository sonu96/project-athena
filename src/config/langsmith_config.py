"""
LangSmith configuration for workflow monitoring and tracing
"""

import os
from typing import Optional
from langsmith import Client
import logging

from .settings import settings

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """Manages LangSmith configuration and tracing setup"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.project_name = settings.langsmith_project
        self.enabled = bool(settings.langsmith_api_key)
        
        if self.enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize LangSmith client"""
        try:
            # Set environment variables for LangSmith
            if settings.langsmith_api_key:
                os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_PROJECT"] = self.project_name
                
                # Initialize client
                self.client = Client(
                    api_url="https://api.smith.langchain.com",
                    api_key=settings.langsmith_api_key
                )
                
                logger.info(f"✅ LangSmith initialized for project: {self.project_name}")
            else:
                logger.warning("⚠️ LangSmith API key not provided, tracing disabled")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize LangSmith: {e}")
            self.enabled = False
    
    def create_session(self, session_name: str, metadata: dict = None) -> Optional[str]:
        """Create a new tracing session"""
        if not self.enabled or not self.client:
            return None
        
        try:
            # Create session with metadata
            session_metadata = {
                "agent_id": settings.agent_id,
                "session_type": "athena_operations",
                **(metadata or {})
            }
            
            # LangSmith will automatically track sessions through project name
            logger.info(f"📊 Created LangSmith session: {session_name}")
            return session_name
            
        except Exception as e:
            logger.error(f"Failed to create LangSmith session: {e}")
            return None
    
    def log_agent_event(self, event_type: str, data: dict):
        """Log agent-specific events to LangSmith"""
        if not self.enabled or not self.client:
            return
        
        try:
            # This would log custom events to LangSmith
            # LangGraph workflows are automatically traced
            logger.debug(f"LangSmith event: {event_type} - {data}")
            
        except Exception as e:
            logger.error(f"Failed to log event to LangSmith: {e}")
    
    def get_workflow_analytics(self, days: int = 7) -> dict:
        """Get workflow analytics from LangSmith"""
        if not self.enabled or not self.client:
            return {}
        
        try:
            # This would query LangSmith for workflow performance data
            # For now, return placeholder
            return {
                "workflows_executed": 0,
                "average_latency": 0,
                "success_rate": 0,
                "cost_tracking": {},
                "error_rate": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow analytics: {e}")
            return {}
    
    def setup_workflow_monitoring(self, workflow_name: str) -> dict:
        """Set up monitoring for a specific workflow"""
        if not self.enabled:
            return {"monitoring_enabled": False}
        
        monitoring_config = {
            "monitoring_enabled": True,
            "project": self.project_name,
            "workflow": workflow_name,
            "tracing": True,
            "performance_tracking": True,
            "cost_tracking": True,
            "error_monitoring": True
        }
        
        logger.info(f"📈 Monitoring configured for workflow: {workflow_name}")
        return monitoring_config


# Global LangSmith configuration
langsmith_config = LangSmithConfig()


def get_langsmith_config() -> LangSmithConfig:
    """Get the global LangSmith configuration"""
    return langsmith_config


def enable_tracing(session_name: str = None, metadata: dict = None) -> bool:
    """Enable LangSmith tracing for the current session"""
    if not langsmith_config.enabled:
        logger.warning("LangSmith not available - tracing disabled")
        return False
    
    if session_name:
        langsmith_config.create_session(session_name, metadata)
    
    # Set environment variables to ensure tracing is active
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = langsmith_config.project_name
    
    return True


def disable_tracing():
    """Disable LangSmith tracing"""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    logger.info("LangSmith tracing disabled")


def trace_workflow_execution(workflow_name: str, input_data: dict, output_data: dict, duration: float, cost: float):
    """Manually trace workflow execution details"""
    if not langsmith_config.enabled:
        return
    
    try:
        trace_data = {
            "workflow": workflow_name,
            "input_size": len(str(input_data)),
            "output_size": len(str(output_data)), 
            "duration_seconds": duration,
            "cost_usd": cost,
            "success": "errors" not in output_data or len(output_data.get("errors", [])) == 0
        }
        
        langsmith_config.log_agent_event("workflow_execution", trace_data)
        
    except Exception as e:
        logger.error(f"Failed to trace workflow execution: {e}")


# Workflow monitoring decorators for easy integration
def monitor_workflow(workflow_name: str):
    """Decorator to automatically monitor workflow execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                cost = sum(cost.get("amount", 0) for cost in result.get("costs_incurred", []))
                
                trace_workflow_execution(workflow_name, kwargs, result, duration, cost)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                trace_workflow_execution(workflow_name, kwargs, {"error": str(e)}, duration, 0)
                raise
                
        return wrapper
    return decorator