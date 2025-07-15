#!/usr/bin/env python3
"""
Check daily GCP costs for Athena project
"""

import subprocess
import json
from datetime import datetime, timedelta

def check_costs():
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get cost data
    cmd = f"""
    gcloud billing costs list \
        --billing-account={BILLING_ACCOUNT} \
        --filter="usage_start_time>={yesterday}" \
        --format=json
    """
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        costs = json.loads(result.stdout) if result.stdout else []
        
        total_cost = sum(float(cost.get('cost', {}).get('amount', 0)) for cost in costs)
        
        print(f"💰 Daily Cost Report for {yesterday}")
        print(f"Total spend: ${total_cost:.2f}")
        print(f"Remaining budget: ${30 - total_cost:.2f}")
        print(f"Days until limit: {(30 - total_cost) / total_cost if total_cost > 0 else 'N/A'}")
        
    except Exception as e:
        print(f"Error checking costs: {e}")

if __name__ == "__main__":
    check_costs()
