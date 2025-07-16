"""Test consciousness state"""

import pytest
from src.core.consciousness import ConsciousnessState
from src.core.emotions import EmotionalState


def test_consciousness_initialization():
    """Test consciousness state initialization"""
    state = ConsciousnessState(
        agent_id="test",
        treasury_balance=100.0,
        emotional_state=EmotionalState.STABLE
    )
    
    assert state.agent_id == "test"
    assert state.treasury_balance == 100.0
    assert state.emotional_state == EmotionalState.STABLE


def test_observation_frequency():
    """Test observation frequency based on emotional state"""
    state = ConsciousnessState(
        agent_id="test",
        treasury_balance=100.0,
        emotional_state=EmotionalState.DESPERATE
    )
    
    assert state.get_observation_frequency_minutes() == 240  # 4 hours
    
    state.emotional_state = EmotionalState.CONFIDENT
    assert state.get_observation_frequency_minutes() == 30  # 30 minutes


def test_should_run_cycle():
    """Test cycle running logic"""
    state = ConsciousnessState(
        agent_id="test",
        treasury_balance=100.0,
        emotional_state=EmotionalState.STABLE
    )
    
    # Should run on first cycle
    assert state.should_run_cycle() is True