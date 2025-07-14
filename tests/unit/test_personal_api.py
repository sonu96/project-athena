"""
Unit tests for personal API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app


client = TestClient(app)


class TestPersonalAPI:
    """Test personal API endpoints"""
    
    @patch('backend.api.personal_routes.treasury_monitor')
    @patch('backend.api.personal_routes.memory_aggregator')
    @patch('backend.api.personal_routes.agent')
    def test_get_dashboard(self, mock_agent, mock_memory, mock_treasury):
        """Test dashboard endpoint"""
        
        # Mock return values
        mock_treasury.get_dashboard_metrics = AsyncMock(return_value={
            'current_balance': 1000,
            'burn_rate': {'daily': 10},
            'runway': {'days': 100},
            'health': {'status': 'HEALTHY'}
        })
        
        mock_agent.get_agent_state = AsyncMock(return_value={
            'mode': 'NORMAL',
            'last_decision': None
        })
        
        mock_memory.mem0_manager.get_memory_insights = AsyncMock(return_value={
            'total_decisions': 10,
            'success_rate': 0.8
        })
        
        # Make request
        response = client.get("/api/personal/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'treasury' in data['data']
        assert 'agent_state' in data['data']
    
    def test_emergency_stop(self):
        """Test emergency stop endpoint"""
        response = client.post("/api/personal/emergency-stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'stopped'
    
    def test_restart_agent(self):
        """Test agent restart endpoint"""
        response = client.post("/api/personal/restart-agent")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'restarted'
    
    @patch('backend.api.personal_routes.alert_manager')
    def test_get_active_alerts(self, mock_alert_manager):
        """Test get active alerts endpoint"""
        
        mock_alert_manager.get_active_alerts.return_value = [
            {
                'id': 'test_alert',
                'level': 'WARNING',
                'message': 'Test alert',
                'timestamp': '2024-01-01T00:00:00'
            }
        ]
        
        response = client.get("/api/personal/alerts/active")
        
        assert response.status_code == 200
        data = response.json()
        assert 'alerts' in data
        assert len(data['alerts']) == 1
    
    @patch('backend.api.personal_routes.alert_manager')
    def test_acknowledge_alert(self, mock_alert_manager):
        """Test acknowledge alert endpoint"""
        
        mock_alert_manager.acknowledge_alert.return_value = True
        
        response = client.post("/api/personal/alerts/test_alert/acknowledge")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'acknowledged'
    
    @patch('backend.api.personal_routes.memory_aggregator')
    def test_get_performance_summary(self, mock_memory):
        """Test performance summary endpoint"""
        
        mock_memory.get_performance_summary = AsyncMock(return_value={
            'overall': {'success_rate': 0.75},
            'strategies': {'best': 'conservative'},
            'health_score': 0.8
        })
        
        response = client.get("/api/personal/performance/summary?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data
        assert data['period_days'] == 7


class TestAutomationAPI:
    """Test automation API endpoints"""
    
    def test_schedule_treasury_check(self):
        """Test scheduling treasury check"""
        response = client.post("/api/automation/schedule/treasury-check", json={
            "hour": 9,
            "minute": 0,
            "enabled": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'scheduled'
        assert 'job_id' in data
    
    def test_schedule_market_scan(self):
        """Test scheduling market scan"""
        response = client.post("/api/automation/schedule/market-scan", json={
            "interval_hours": 4,
            "enabled": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'scheduled'
    
    def test_get_automations(self):
        """Test get active automations"""
        response = client.get("/api/automation/automations")
        
        assert response.status_code == 200
        data = response.json()
        assert 'automations' in data
        assert 'total' in data
    
    def test_disable_automation(self):
        """Test disabling an automation"""
        # First schedule one
        response = client.post("/api/automation/schedule/treasury-check", json={
            "enabled": True
        })
        
        # Then disable it
        response = client.post("/api/automation/schedule/treasury-check", json={
            "enabled": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'disabled'