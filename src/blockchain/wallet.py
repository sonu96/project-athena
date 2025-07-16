"""
Wallet Management

Handles wallet state and security.
"""

import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Manages wallet data and security
    
    Note: Private keys are handled by CDP SDK, not stored directly
    """
    
    def __init__(self, wallet_path: str = "wallet_data"):
        self.wallet_path = wallet_path
        self.wallet_info: Optional[Dict[str, Any]] = None
        
        # Ensure wallet directory exists
        os.makedirs(self.wallet_path, exist_ok=True)
    
    def load_wallet_info(self) -> Optional[Dict[str, Any]]:
        """Load wallet information (not private keys)"""
        
        info_file = os.path.join(self.wallet_path, "wallet_info.json")
        
        try:
            if os.path.exists(info_file):
                with open(info_file, 'r') as f:
                    self.wallet_info = json.load(f)
                    logger.info(f"Loaded wallet info for {self.wallet_info.get('address')}")
                    return self.wallet_info
        except Exception as e:
            logger.error(f"Failed to load wallet info: {e}")
        
        return None
    
    def save_wallet_info(self, address: str, network: str) -> None:
        """Save wallet information (not private keys)"""
        
        self.wallet_info = {
            "address": address,
            "network": network,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        info_file = os.path.join(self.wallet_path, "wallet_info.json")
        
        try:
            with open(info_file, 'w') as f:
                json.dump(self.wallet_info, f, indent=2)
            logger.info(f"Saved wallet info for {address}")
        except Exception as e:
            logger.error(f"Failed to save wallet info: {e}")
    
    def update_wallet_stats(self, stats: Dict[str, Any]) -> None:
        """Update wallet statistics"""
        
        if not self.wallet_info:
            logger.warning("No wallet info loaded")
            return
        
        # Update stats
        if "stats" not in self.wallet_info:
            self.wallet_info["stats"] = {}
        
        self.wallet_info["stats"].update(stats)
        self.wallet_info["last_updated"] = datetime.utcnow().isoformat()
        
        # Save updated info
        info_file = os.path.join(self.wallet_path, "wallet_info.json")
        
        try:
            with open(info_file, 'w') as f:
                json.dump(self.wallet_info, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update wallet stats: {e}")
    
    def get_wallet_age_days(self) -> int:
        """Get wallet age in days"""
        
        if not self.wallet_info or "created_at" not in self.wallet_info:
            return 0
        
        try:
            created = datetime.fromisoformat(self.wallet_info["created_at"].replace('Z', '+00:00'))
            age = datetime.utcnow() - created.replace(tzinfo=None)
            return age.days
        except Exception as e:
            logger.error(f"Failed to calculate wallet age: {e}")
            return 0
    
    def should_backup_wallet(self) -> bool:
        """Check if wallet should be backed up"""
        
        # Backup every 7 days
        backup_file = os.path.join(self.wallet_path, "last_backup.txt")
        
        try:
            if os.path.exists(backup_file):
                with open(backup_file, 'r') as f:
                    last_backup = datetime.fromisoformat(f.read().strip())
                
                days_since = (datetime.utcnow() - last_backup).days
                return days_since >= 7
        except:
            pass
        
        return True  # No backup found
    
    def mark_backup_complete(self) -> None:
        """Mark that backup was completed"""
        
        backup_file = os.path.join(self.wallet_path, "last_backup.txt")
        
        try:
            with open(backup_file, 'w') as f:
                f.write(datetime.utcnow().isoformat())
            logger.info("Backup marked as complete")
        except Exception as e:
            logger.error(f"Failed to mark backup: {e}")