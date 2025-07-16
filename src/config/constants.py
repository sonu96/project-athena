"""
System constants for Athena Agent
"""

# Cognitive Loop Parameters
COGNITIVE_CYCLE_MIN_INTERVAL_SECONDS = 30  # Minimum time between cycles
COGNITIVE_CYCLE_MAX_RETRIES = 3           # Max retries on failure

# Memory System
MEMORY_CATEGORIES = [
    "market_patterns",
    "gas_patterns",
    "pool_behavior", 
    "timing_patterns",
    "risk_patterns",
    "survival_memories"
]

MEMORY_IMPORTANCE_LEVELS = {
    "critical": 1.0,
    "high": 0.8,
    "medium": 0.6,
    "low": 0.4,
    "trivial": 0.2
}

# Pattern Recognition
MIN_PATTERN_OCCURRENCES = 3      # Minimum occurrences to form pattern
PATTERN_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence to act on pattern

# Aerodrome Pools (V1 Observation)
AERODROME_FACTORY_ADDRESS = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
AERODROME_ROUTER_ADDRESS = "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"

# Pool Types
POOL_TYPE_STABLE = "stable"
POOL_TYPE_VOLATILE = "volatile"

# Observation Limits
MAX_POOLS_TO_OBSERVE = 10         # Maximum pools to track
MAX_OBSERVATIONS_PER_POOL = 100   # Maximum historical observations per pool

# Cost Limits (per cycle)
MAX_LLM_COST_PER_CYCLE = 0.10    # $0.10 max per cognitive cycle
MAX_MEMORY_OPERATIONS = 20        # Max memory operations per cycle

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL = 30        # Seconds
WS_MAX_MESSAGE_SIZE = 1048576     # 1MB

# Time Formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S UTC"
DATE_FORMAT = "%Y-%m-%d"

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Emojis for states (optional UI feature)
EMOJI_STATES = {
    "desperate": "😱",
    "cautious": "😟", 
    "stable": "😊",
    "confident": "😎",
    "thinking": "🤔",
    "learning": "🧠",
    "observing": "👁️",
    "deciding": "🎯"
}