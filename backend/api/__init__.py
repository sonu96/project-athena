"""
API module initialization
"""

from .personal_routes import router as personal_router
from .automation_routes import router as automation_router

__all__ = ['personal_router', 'automation_router']