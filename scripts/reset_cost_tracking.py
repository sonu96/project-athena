#!/usr/bin/env python3
"""Reset cost tracking to allow operations to resume"""

import json
from datetime import datetime

def reset_cost_tracking():
    """Reset the cost tracking file to allow operations"""
    
    cost_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_cost": 0.0,
        "services": {
            "gemini_api": 0.0,
            "openai_api": 0.0,
            "mem0_api": 0.0,
            "google_cloud": 0.0,
            "other": 0.0
        },
        "operations": {
            "llm_calls": 0,
            "memory_operations": 0,
            "database_operations": 0,
            "cognitive_cycles": 0
        },
        "alerts_triggered": [],
        "emergency_mode": False,
        "shutdown_triggered": False,
        "reduced_frequency": False
    }
    
    # Write reset data
    with open("cost_tracking.json", "w") as f:
        json.dump(cost_data, f, indent=2)
    
    print("✅ Cost tracking reset successfully")
    print(f"📅 Date: {cost_data['date']}")
    print("💰 Total cost: $0.00")
    print("🚀 Ready to resume operations")

if __name__ == "__main__":
    reset_cost_tracking()