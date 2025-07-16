"""Test full agent lifecycle"""

import pytest
from unittest.mock import Mock, patch
import asyncio


@pytest.mark.asyncio
@pytest.mark.timeout(10)  # Shorter timeout for tests
async def test_agent_initialization():
    """Test agent can initialize"""
    with patch('src.core.agent.settings') as mock_settings:
        # Mock settings
        mock_settings.agent_id = "test"
        mock_settings.starting_treasury = 100.0
        mock_settings.network = "base-sepolia"
        mock_settings.cdp_api_key_name = None  # Force simulation
        mock_settings.cdp_api_key_secret = None
        
        from src.core.agent import AthenaAgent
        
        # Just test initialization
        agent = AthenaAgent()
        assert agent is not None
        assert agent.state.treasury_balance == 100.0