"""
Treasury alert system for critical notifications
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import asyncio
import json


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertType(Enum):
    """Types of treasury alerts"""
    LOW_BALANCE = "LOW_BALANCE"
    HIGH_BURN_RATE = "HIGH_BURN_RATE"
    SHORT_RUNWAY = "SHORT_RUNWAY"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    UNUSUAL_ACTIVITY = "UNUSUAL_ACTIVITY"
    OPTIMIZATION_OPPORTUNITY = "OPTIMIZATION_OPPORTUNITY"


class TreasuryAlertManager:
    """
    Manages treasury alerts and notifications
    """
    
    def __init__(self):
        self.alert_handlers = {
            AlertLevel.INFO: [],
            AlertLevel.WARNING: [],
            AlertLevel.CRITICAL: [],
            AlertLevel.EMERGENCY: []
        }
        
        self.alert_history = []
        self.active_alerts = {}
        
        # Alert configuration
        self.config = {
            'enable_notifications': True,
            'critical_balance': 100,
            'warning_balance': 500,
            'critical_runway_days': 7,
            'warning_runway_days': 30,
            'max_burn_rate': 100,  # $/day
            'alert_cooldown_minutes': 60  # Don't repeat same alert within this period
        }
    
    async def create_alert(self,
                          alert_type: AlertType,
                          level: AlertLevel,
                          message: str,
                          data: Dict[str, Any] = None) -> str:
        """Create and dispatch a new alert"""
        
        alert_id = f"{alert_type.value}_{datetime.now().timestamp()}"
        
        alert = {
            'id': alert_id,
            'type': alert_type.value,
            'level': level.value,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        }
        
        # Check if similar alert was recently sent
        if not self._should_send_alert(alert_type, level):
            return None
        
        # Store alert
        self.alert_history.append(alert)
        self.active_alerts[alert_id] = alert
        
        # Dispatch to handlers
        await self._dispatch_alert(alert, level)
        
        # Emergency alerts trigger immediate action
        if level == AlertLevel.EMERGENCY:
            await self._handle_emergency(alert)
        
        return alert_id
    
    def register_handler(self, level: AlertLevel, handler):
        """Register an alert handler for specific level"""
        self.alert_handlers[level].append(handler)
    
    async def check_treasury_alerts(self, treasury_data: Dict) -> List[str]:
        """Check treasury data and create appropriate alerts"""
        
        created_alerts = []
        
        balance = treasury_data.get('current_balance', 0)
        burn_rate = treasury_data.get('burn_rate', {}).get('daily', 0)
        runway_days = treasury_data.get('runway', {}).get('days', 0)
        
        # Check balance alerts
        if balance < self.config['critical_balance']:
            alert_id = await self.create_alert(
                AlertType.LOW_BALANCE,
                AlertLevel.CRITICAL,
                f"Treasury balance critically low: ${balance:.2f}",
                {'balance': balance, 'threshold': self.config['critical_balance']}
            )
            if alert_id:
                created_alerts.append(alert_id)
                
        elif balance < self.config['warning_balance']:
            alert_id = await self.create_alert(
                AlertType.LOW_BALANCE,
                AlertLevel.WARNING,
                f"Treasury balance below warning threshold: ${balance:.2f}",
                {'balance': balance, 'threshold': self.config['warning_balance']}
            )
            if alert_id:
                created_alerts.append(alert_id)
        
        # Check runway alerts
        if runway_days < self.config['critical_runway_days']:
            alert_id = await self.create_alert(
                AlertType.SHORT_RUNWAY,
                AlertLevel.EMERGENCY if runway_days < 3 else AlertLevel.CRITICAL,
                f"Only {runway_days:.1f} days of runway remaining!",
                {'runway_days': runway_days, 'burn_rate': burn_rate}
            )
            if alert_id:
                created_alerts.append(alert_id)
                
        elif runway_days < self.config['warning_runway_days']:
            alert_id = await self.create_alert(
                AlertType.SHORT_RUNWAY,
                AlertLevel.WARNING,
                f"Runway below {self.config['warning_runway_days']} days: {runway_days:.1f} days",
                {'runway_days': runway_days, 'burn_rate': burn_rate}
            )
            if alert_id:
                created_alerts.append(alert_id)
        
        # Check burn rate
        if burn_rate > self.config['max_burn_rate']:
            alert_id = await self.create_alert(
                AlertType.HIGH_BURN_RATE,
                AlertLevel.WARNING,
                f"High burn rate detected: ${burn_rate:.2f}/day",
                {'burn_rate': burn_rate, 'max_allowed': self.config['max_burn_rate']}
            )
            if alert_id:
                created_alerts.append(alert_id)
        
        return created_alerts
    
    async def check_transaction_alert(self, transaction: Dict) -> Optional[str]:
        """Check if a transaction warrants an alert"""
        
        if transaction.get('status') == 'failed':
            return await self.create_alert(
                AlertType.TRANSACTION_FAILED,
                AlertLevel.WARNING,
                f"Transaction failed: {transaction.get('reason', 'Unknown reason')}",
                transaction
            )
        
        # Check for unusually large transactions
        amount = transaction.get('amount', 0)
        if amount > 100:  # More than $100
            return await self.create_alert(
                AlertType.UNUSUAL_ACTIVITY,
                AlertLevel.INFO,
                f"Large transaction: ${amount:.2f}",
                transaction
            )
        
        return None
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['acknowledged'] = True
            self.active_alerts[alert_id]['acknowledged_at'] = datetime.now().isoformat()
            return True
        
        return False
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Dict]:
        """Get all active (unacknowledged) alerts"""
        
        active = []
        for alert in self.active_alerts.values():
            if not alert['acknowledged']:
                if level is None or alert['level'] == level.value:
                    active.append(alert)
        
        return sorted(active, key=lambda x: x['timestamp'], reverse=True)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert status"""
        
        active_by_level = {
            'INFO': 0,
            'WARNING': 0,
            'CRITICAL': 0,
            'EMERGENCY': 0
        }
        
        for alert in self.active_alerts.values():
            if not alert['acknowledged']:
                active_by_level[alert['level']] += 1
        
        return {
            'total_active': sum(active_by_level.values()),
            'by_level': active_by_level,
            'requires_action': active_by_level['CRITICAL'] + active_by_level['EMERGENCY'] > 0,
            'latest_critical': self._get_latest_critical_alert()
        }
    
    # Helper methods
    
    def _should_send_alert(self, alert_type: AlertType, level: AlertLevel) -> bool:
        """Check if we should send this alert (cooldown period)"""
        
        if level == AlertLevel.EMERGENCY:
            return True  # Always send emergency alerts
        
        # Check recent alerts of same type
        cooldown_minutes = self.config['alert_cooldown_minutes']
        cutoff_time = datetime.now().timestamp() - (cooldown_minutes * 60)
        
        for alert in self.alert_history[-20:]:  # Check last 20 alerts
            if (alert['type'] == alert_type.value and 
                alert['level'] == level.value and
                datetime.fromisoformat(alert['timestamp']).timestamp() > cutoff_time):
                return False
        
        return True
    
    async def _dispatch_alert(self, alert: Dict, level: AlertLevel):
        """Dispatch alert to registered handlers"""
        
        handlers = []
        
        # Add handlers for this level and higher
        if level == AlertLevel.INFO:
            handlers.extend(self.alert_handlers[AlertLevel.INFO])
        if level in [AlertLevel.INFO, AlertLevel.WARNING]:
            handlers.extend(self.alert_handlers[AlertLevel.WARNING])
        if level in [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.CRITICAL]:
            handlers.extend(self.alert_handlers[AlertLevel.CRITICAL])
        if level == AlertLevel.EMERGENCY:
            handlers.extend(self.alert_handlers[AlertLevel.EMERGENCY])
        
        # Call all handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                print(f"Error in alert handler: {e}")
    
    async def _handle_emergency(self, alert: Dict):
        """Handle emergency alerts with immediate action"""
        
        # Log to file
        with open('emergency_alerts.log', 'a') as f:
            f.write(f"{json.dumps(alert)}\n")
        
        # Could trigger additional emergency procedures here
        # - Send email/SMS
        # - Trigger emergency shutdown
        # - etc.
    
    def _get_latest_critical_alert(self) -> Optional[Dict]:
        """Get the most recent critical/emergency alert"""
        
        critical_alerts = [
            a for a in self.active_alerts.values()
            if a['level'] in ['CRITICAL', 'EMERGENCY'] and not a['acknowledged']
        ]
        
        if critical_alerts:
            return max(critical_alerts, key=lambda x: x['timestamp'])
        
        return None