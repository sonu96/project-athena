"""
Cognitive loop implementation using LangGraph

This module creates the main consciousness loop that serves as Athena's 
nervous system, implementing the Sense → Think → Feel → Decide → Learn cycle.
"""

from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from .consciousness import ConsciousnessState
from .nodes import SenseNode, ThinkNode, FeelNode, DecideNode, LearnNode


def create_cognitive_loop() -> StateGraph:
    """Create the main cognitive loop that serves as Athena's nervous system
    
    This creates a continuous loop where:
    1. Sense: Perceive the environment (market data, wallet balance)
    2. Think: Analyze and understand the situation
    3. Feel: Update emotional state based on treasury and conditions
    4. Decide: Make decisions based on full context and emotions
    5. Learn: Form memories and extract lessons from experiences
    
    The loop then continues back to Sense, creating a continuous consciousness.
    
    Returns:
        Compiled StateGraph representing the cognitive loop
    """
    
    # Initialize the graph with consciousness state
    workflow = StateGraph(ConsciousnessState)
    
    # Initialize nodes (each wraps existing components)
    sense_node = SenseNode()    # Wraps market_data_collector and CDP
    think_node = ThinkNode()     # Wraps market_analysis_flow
    feel_node = FeelNode()       # Updates emotional state based on treasury
    decide_node = DecideNode()   # Wraps decision_flow
    learn_node = LearnNode()     # Wraps memory_manager
    
    # Add nodes to graph with descriptive names
    workflow.add_node("sense", sense_node.execute)
    workflow.add_node("think", think_node.execute)
    workflow.add_node("feel", feel_node.execute)
    workflow.add_node("decide", decide_node.execute)
    workflow.add_node("learn", learn_node.execute)
    
    # Define the cognitive flow
    workflow.add_edge(START, "sense")      # Start by sensing environment
    workflow.add_edge("sense", "think")    # Sense leads to thinking
    workflow.add_edge("think", "feel")     # Thinking influences emotions
    workflow.add_edge("feel", "decide")    # Emotions affect decisions
    workflow.add_edge("decide", "learn")   # Decisions create learning
    workflow.add_edge("learn", "sense")    # Learning updates perception (continuous loop)
    
    # Note: We don't add an edge to END, creating an infinite loop
    # The agent will run continuously until externally stopped
    
    return workflow.compile()


@traceable(name="cognitive_loop_with_termination")
def create_cognitive_loop_with_termination() -> StateGraph:
    """Create a cognitive loop with optional termination conditions
    
    This variant allows the loop to end based on certain conditions,
    useful for testing or specific operational modes.
    """
    
    # Initialize the graph with consciousness state
    workflow = StateGraph(ConsciousnessState)
    
    # Initialize nodes
    sense_node = SenseNode()
    think_node = ThinkNode()
    feel_node = FeelNode()
    decide_node = DecideNode()
    learn_node = LearnNode()
    
    # Add nodes to graph
    workflow.add_node("sense", sense_node.execute)
    workflow.add_node("think", think_node.execute)
    workflow.add_node("feel", feel_node.execute)
    workflow.add_node("decide", decide_node.execute)
    workflow.add_node("learn", learn_node.execute)
    
    # Define the flow
    workflow.add_edge(START, "sense")
    workflow.add_edge("sense", "think")
    workflow.add_edge("think", "feel")
    workflow.add_edge("feel", "decide")
    workflow.add_edge("decide", "learn")
    
    # Conditional edge: continue or end based on state
    def should_continue(state: ConsciousnessState) -> str:
        """Determine if the loop should continue"""
        # End if critical error
        if len(state.get("errors", [])) > 5:
            return "end"
        # End if bankruptcy imminent
        if state.get("days_until_bankruptcy", 999) < 1:
            return "end"
        # Otherwise continue
        return "sense"
    
    workflow.add_conditional_edges(
        "learn",
        should_continue,
        {
            "sense": "sense",  # Continue loop
            "end": END         # Terminate
        }
    )
    
    return workflow.compile()