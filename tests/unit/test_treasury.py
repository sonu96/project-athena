"""
Unit tests for Treasury Manager
Tests treasury balance tracking, emotional states, and survival mechanisms
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.treasury import TreasuryManager


class TestTreasuryManager:
    """Test suite for TreasuryManager"""
    
    @pytest.fixture
    def mock_firestore_client(self):
        """Mock Firestore client"""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_doc = MagicMock()
        
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc
        
        return mock_client
    
    @pytest.fixture
    def mock_bigquery_client(self):
        """Mock BigQuery client"""
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []
        return mock_client
    
    @pytest.fixture
    def treasury_manager(self, mock_firestore_client, mock_bigquery_client):
        """Create TreasuryManager with mocked dependencies"""
        with patch('core.treasury.firestore.Client', return_value=mock_firestore_client), \
             patch('core.treasury.bigquery.Client', return_value=mock_bigquery_client):
            return TreasuryManager(starting_balance=100.0)
    
    def test_initialization(self, treasury_manager):
        """Test TreasuryManager initialization"""
        assert treasury_manager.current_balance == 100.0
        assert treasury_manager.starting_balance == 100.0
        assert treasury_manager.emotional_state == "stable"
    
    def test_emotional_state_confident(self, treasury_manager):
        """Test emotional state when balance is high"""
        treasury_manager.current_balance = 150.0
        state = treasury_manager._calculate_emotional_state()
        assert state == "confident"
    
    def test_emotional_state_stable(self, treasury_manager):
        """Test emotional state when balance is normal"""
        treasury_manager.current_balance = 80.0
        state = treasury_manager._calculate_emotional_state()
        assert state == "stable"
    
    def test_emotional_state_cautious(self, treasury_manager):
        """Test emotional state when balance is low"""
        treasury_manager.current_balance = 40.0
        state = treasury_manager._calculate_emotional_state()
        assert state == "cautious"
    
    def test_emotional_state_desperate(self, treasury_manager):
        """Test emotional state when balance is critical"""
        treasury_manager.current_balance = 15.0
        state = treasury_manager._calculate_emotional_state()
        assert state == "desperate"
    
    def test_days_until_bankruptcy(self, treasury_manager):
        """Test bankruptcy calculation"""
        treasury_manager.current_balance = 50.0
        treasury_manager.daily_burn_rate = 2.0
        
        days = treasury_manager._calculate_days_until_bankruptcy()
        assert days == 25  # 50 / 2 = 25 days
    
    def test_days_until_bankruptcy_zero_burn(self, treasury_manager):
        """Test bankruptcy calculation with zero burn rate"""
        treasury_manager.current_balance = 50.0
        treasury_manager.daily_burn_rate = 0.0
        
        days = treasury_manager._calculate_days_until_bankruptcy()
        assert days == 365  # Default when no burn
    
    @pytest.mark.asyncio
    async def test_deduct_cost_normal(self, treasury_manager):
        """Test normal cost deduction"""
        initial_balance = treasury_manager.current_balance
        
        with patch.object(treasury_manager, '_store_cost_data') as mock_store:
            success = await treasury_manager.deduct_cost(5.0, "test_operation", "test")
            
            assert success is True
            assert treasury_manager.current_balance == initial_balance - 5.0
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deduct_cost_insufficient_funds(self, treasury_manager):
        """Test cost deduction with insufficient funds"""
        treasury_manager.current_balance = 3.0
        
        with patch.object(treasury_manager, '_store_cost_data') as mock_store:
            success = await treasury_manager.deduct_cost(5.0, "test_operation", "test")
            
            assert success is False
            assert treasury_manager.current_balance == 3.0  # Unchanged
            mock_store.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_deduct_cost_emergency_mode(self, treasury_manager):
        """Test cost deduction in emergency mode"""
        treasury_manager.current_balance = 20.0  # Low balance
        treasury_manager.emergency_mode = True
        
        with patch.object(treasury_manager, '_store_cost_data') as mock_store:
            success = await treasury_manager.deduct_cost(0.5, "emergency_operation", "emergency")
            
            assert success is True
            assert treasury_manager.current_balance == 19.5
    
    @pytest.mark.asyncio
    async def test_update_burn_rate(self, treasury_manager):
        """Test burn rate calculation"""
        # Add some cost history
        treasury_manager.cost_history = [
            {'timestamp': datetime.utcnow().isoformat(), 'cost_usd': 2.0},
            {'timestamp': (datetime.utcnow() - timedelta(hours=12)).isoformat(), 'cost_usd': 1.5},
            {'timestamp': (datetime.utcnow() - timedelta(hours=36)).isoformat(), 'cost_usd': 1.0}  # Older than 24h
        ]
        
        await treasury_manager._update_burn_rate()
        
        # Should only count costs from last 24 hours: 2.0 + 1.5 = 3.5
        assert treasury_manager.daily_burn_rate == 3.5
    
    def test_get_risk_tolerance_confident(self, treasury_manager):
        """Test risk tolerance when confident"""
        treasury_manager.emotional_state = "confident"
        tolerance = treasury_manager.get_risk_tolerance()
        assert tolerance == 0.8
    
    def test_get_risk_tolerance_stable(self, treasury_manager):
        """Test risk tolerance when stable"""
        treasury_manager.emotional_state = "stable"
        tolerance = treasury_manager.get_risk_tolerance()
        assert tolerance == 0.6
    
    def test_get_risk_tolerance_cautious(self, treasury_manager):
        """Test risk tolerance when cautious"""
        treasury_manager.emotional_state = "cautious"
        tolerance = treasury_manager.get_risk_tolerance()
        assert tolerance == 0.3
    
    def test_get_risk_tolerance_desperate(self, treasury_manager):
        """Test risk tolerance when desperate"""
        treasury_manager.emotional_state = "desperate"
        tolerance = treasury_manager.get_risk_tolerance()
        assert tolerance == 0.1
    
    def test_should_activate_emergency_mode_true(self, treasury_manager):
        """Test emergency mode activation"""
        treasury_manager.current_balance = 20.0
        treasury_manager.daily_burn_rate = 10.0  # 2 days until bankruptcy
        
        should_activate = treasury_manager._should_activate_emergency_mode()
        assert should_activate is True
    
    def test_should_activate_emergency_mode_false(self, treasury_manager):
        """Test emergency mode not activated"""
        treasury_manager.current_balance = 80.0
        treasury_manager.daily_burn_rate = 2.0  # 40 days until bankruptcy
        
        should_activate = treasury_manager._should_activate_emergency_mode()
        assert should_activate is False
    
    @pytest.mark.asyncio
    async def test_get_status(self, treasury_manager):
        """Test status retrieval"""
        treasury_manager.current_balance = 75.0
        treasury_manager.daily_burn_rate = 3.0
        
        status = await treasury_manager.get_status()
        
        assert status['balance'] == 75.0
        assert status['emotional_state'] == 'stable'
        assert status['daily_burn_rate'] == 3.0
        assert status['days_until_bankruptcy'] == 25
        assert status['risk_tolerance'] == 0.6
        assert status['emergency_mode'] is False
    
    @pytest.mark.asyncio
    async def test_get_cost_summary(self, treasury_manager):
        """Test cost summary"""
        treasury_manager.cost_history = [
            {'timestamp': datetime.utcnow().isoformat(), 'cost_usd': 2.0, 'cost_type': 'llm'},
            {'timestamp': datetime.utcnow().isoformat(), 'cost_usd': 1.0, 'cost_type': 'api'},
            {'timestamp': datetime.utcnow().isoformat(), 'cost_usd': 0.5, 'cost_type': 'llm'}
        ]
        
        summary = await treasury_manager.get_cost_summary()
        
        assert summary['total_spent'] == 96.5  # 100 - 3.5
        assert summary['remaining_balance'] == 100.0  # current_balance
        assert summary['daily_burn_rate'] == 3.5
        assert 'cost_breakdown' in summary
    
    def test_survival_pressure_high(self, treasury_manager):
        """Test high survival pressure calculation"""
        treasury_manager.current_balance = 20.0
        treasury_manager.starting_balance = 100.0
        
        pressure = treasury_manager._calculate_survival_pressure()
        assert pressure == 0.8  # (100 - 20) / 100
    
    def test_survival_pressure_low(self, treasury_manager):
        """Test low survival pressure calculation"""
        treasury_manager.current_balance = 90.0
        treasury_manager.starting_balance = 100.0
        
        pressure = treasury_manager._calculate_survival_pressure()
        assert pressure == 0.1  # (100 - 90) / 100