"""
Real-time treasury monitoring for personal DeFi agent
Provides comprehensive financial health tracking and alerts
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from .treasury_manager import TreasuryManager
from .burn_rate_calculator import BurnRateCalculator
from .survival_metrics import SurvivalMetrics


@dataclass
class TreasuryAlert:
    """Alert data structure"""
    level: str  # CRITICAL, WARNING, INFO
    message: str
    timestamp: datetime
    metric: str
    value: float
    threshold: float


class TreasuryMonitor:
    """
    Enhanced treasury monitoring with real-time alerts and insights
    """
    
    def __init__(self):
        self.manager = TreasuryManager()
        self.burn_rate_calc = BurnRateCalculator()
        self.survival = SurvivalMetrics()
        
        # Alert thresholds
        self.thresholds = {
            'critical_balance': 100,      # $ - Critical if below
            'warning_balance': 500,       # $ - Warning if below
            'critical_runway': 7,         # days - Critical if below
            'warning_runway': 30,         # days - Warning if below
            'high_burn_rate': 50,         # $/day - Warning if above
            'critical_burn_rate': 100,    # $/day - Critical if above
        }
        
        # Alert history
        self.alerts: List[TreasuryAlert] = []
        self.alert_callbacks = []
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive treasury metrics for dashboard"""
        
        current_balance = self.manager.get_balance()
        burn_rate = self.burn_rate_calc.calculate_daily_burn_rate()
        runway_days = self.survival.calculate_runway_days()
        health_status = self.survival.get_health_status()
        
        # Calculate additional metrics
        weekly_spend = self.burn_rate_calc.calculate_weekly_spend()
        monthly_projection = burn_rate * 30
        
        # Get spending breakdown
        spending_breakdown = self.manager.get_spending_breakdown()
        
        # Check for alerts
        alerts = await self.check_alerts()
        
        return {
            'current_balance': current_balance,
            'burn_rate': {
                'daily': burn_rate,
                'weekly': weekly_spend,
                'monthly_projection': monthly_projection
            },
            'runway': {
                'days': runway_days,
                'weeks': runway_days / 7,
                'months': runway_days / 30
            },
            'health': {
                'status': health_status,
                'score': self._calculate_health_score(current_balance, runway_days),
                'risk_level': self._assess_risk_level(current_balance, burn_rate)
            },
            'spending': {
                'breakdown': spending_breakdown,
                'largest_expense': max(spending_breakdown.items(), key=lambda x: x[1]) if spending_breakdown else None,
                'optimization_suggestions': self._get_optimization_suggestions(spending_breakdown)
            },
            'alerts': alerts,
            'last_updated': datetime.now().isoformat()
        }
    
    async def check_alerts(self) -> List[TreasuryAlert]:
        """Check for treasury alerts and trigger callbacks"""
        
        new_alerts = []
        
        # Get current metrics
        balance = self.manager.get_balance()
        burn_rate = self.burn_rate_calc.calculate_daily_burn_rate()
        runway = self.survival.calculate_runway_days()
        
        # Check balance alerts
        if balance < self.thresholds['critical_balance']:
            alert = TreasuryAlert(
                level='CRITICAL',
                message=f'Treasury balance critically low: ${balance:.2f}',
                timestamp=datetime.now(),
                metric='balance',
                value=balance,
                threshold=self.thresholds['critical_balance']
            )
            new_alerts.append(alert)
        elif balance < self.thresholds['warning_balance']:
            alert = TreasuryAlert(
                level='WARNING',
                message=f'Treasury balance low: ${balance:.2f}',
                timestamp=datetime.now(),
                metric='balance',
                value=balance,
                threshold=self.thresholds['warning_balance']
            )
            new_alerts.append(alert)
        
        # Check runway alerts
        if runway < self.thresholds['critical_runway']:
            alert = TreasuryAlert(
                level='CRITICAL',
                message=f'Only {runway:.1f} days of runway remaining',
                timestamp=datetime.now(),
                metric='runway',
                value=runway,
                threshold=self.thresholds['critical_runway']
            )
            new_alerts.append(alert)
        elif runway < self.thresholds['warning_runway']:
            alert = TreasuryAlert(
                level='WARNING',
                message=f'Limited runway: {runway:.1f} days remaining',
                timestamp=datetime.now(),
                metric='runway',
                value=runway,
                threshold=self.thresholds['warning_runway']
            )
            new_alerts.append(alert)
        
        # Check burn rate alerts
        if burn_rate > self.thresholds['critical_burn_rate']:
            alert = TreasuryAlert(
                level='CRITICAL',
                message=f'Burn rate critically high: ${burn_rate:.2f}/day',
                timestamp=datetime.now(),
                metric='burn_rate',
                value=burn_rate,
                threshold=self.thresholds['critical_burn_rate']
            )
            new_alerts.append(alert)
        elif burn_rate > self.thresholds['high_burn_rate']:
            alert = TreasuryAlert(
                level='WARNING',
                message=f'High burn rate: ${burn_rate:.2f}/day',
                timestamp=datetime.now(),
                metric='burn_rate',
                value=burn_rate,
                threshold=self.thresholds['high_burn_rate']
            )
            new_alerts.append(alert)
        
        # Store new alerts
        self.alerts.extend(new_alerts)
        
        # Trigger callbacks for critical alerts
        critical_alerts = [a for a in new_alerts if a.level == 'CRITICAL']
        if critical_alerts and self.alert_callbacks:
            await self._trigger_alert_callbacks(critical_alerts)
        
        return new_alerts
    
    def register_alert_callback(self, callback):
        """Register a callback for critical alerts"""
        self.alert_callbacks.append(callback)
    
    async def get_historical_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get historical treasury metrics"""
        
        # Get transaction history
        history = self.manager.get_transaction_history(days)
        
        # Calculate daily balances
        daily_balances = []
        daily_burns = []
        
        current_date = datetime.now()
        for i in range(days):
            date = current_date - timedelta(days=i)
            day_transactions = [t for t in history if t['timestamp'].date() == date.date()]
            
            # Calculate daily metrics
            daily_spend = sum(t['amount'] for t in day_transactions if t['type'] == 'expense')
            daily_revenue = sum(t['amount'] for t in day_transactions if t['type'] == 'revenue')
            
            daily_balances.append({
                'date': date.isoformat(),
                'balance': self.manager.get_balance_at_date(date),
                'spend': daily_spend,
                'revenue': daily_revenue,
                'net': daily_revenue - daily_spend
            })
            
            daily_burns.append(daily_spend)
        
        # Calculate trends
        avg_burn = sum(daily_burns) / len(daily_burns) if daily_burns else 0
        burn_trend = self._calculate_trend(daily_burns)
        
        return {
            'daily_data': daily_balances,
            'averages': {
                'daily_burn': avg_burn,
                'daily_revenue': sum(d['revenue'] for d in daily_balances) / len(daily_balances)
            },
            'trends': {
                'burn_rate': burn_trend,
                'balance': self._calculate_balance_trend(daily_balances)
            },
            'projections': {
                '7_day': self._project_balance(7, avg_burn),
                '30_day': self._project_balance(30, avg_burn),
                '90_day': self._project_balance(90, avg_burn)
            }
        }
    
    def get_cost_optimization_report(self) -> Dict[str, Any]:
        """Generate cost optimization recommendations"""
        
        breakdown = self.manager.get_spending_breakdown()
        total_spend = sum(breakdown.values())
        
        report = {
            'total_monthly_spend': total_spend,
            'largest_categories': sorted(
                breakdown.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            'recommendations': [],
            'potential_savings': 0
        }
        
        # Gas optimization
        gas_spend = breakdown.get('gas_fees', 0)
        if gas_spend > total_spend * 0.3:  # More than 30% on gas
            savings = gas_spend * 0.2  # Could save 20%
            report['recommendations'].append({
                'category': 'gas_fees',
                'action': 'Batch transactions and optimize timing',
                'potential_savings': savings,
                'priority': 'HIGH'
            })
            report['potential_savings'] += savings
        
        # API cost optimization
        api_spend = breakdown.get('api_calls', 0)
        if api_spend > total_spend * 0.2:  # More than 20% on APIs
            savings = api_spend * 0.15
            report['recommendations'].append({
                'category': 'api_calls',
                'action': 'Implement caching and reduce redundant calls',
                'potential_savings': savings,
                'priority': 'MEDIUM'
            })
            report['potential_savings'] += savings
        
        # Decision frequency
        decision_cost = breakdown.get('decisions', 0)
        decisions_per_day = self.manager.get_daily_decision_count()
        if decisions_per_day > 20:
            savings = decision_cost * 0.3
            report['recommendations'].append({
                'category': 'decisions',
                'action': 'Reduce decision frequency, increase thresholds',
                'potential_savings': savings,
                'priority': 'MEDIUM'
            })
            report['potential_savings'] += savings
        
        return report
    
    # Helper methods
    
    def _calculate_health_score(self, balance: float, runway: float) -> float:
        """Calculate treasury health score (0-1)"""
        
        # Balance component (40%)
        balance_score = min(1.0, balance / 1000)  # Full score at $1000+
        
        # Runway component (60%)
        runway_score = min(1.0, runway / 90)  # Full score at 90+ days
        
        return (balance_score * 0.4) + (runway_score * 0.6)
    
    def _assess_risk_level(self, balance: float, burn_rate: float) -> str:
        """Assess current risk level"""
        
        runway = balance / burn_rate if burn_rate > 0 else float('inf')
        
        if runway < 7 or balance < 100:
            return 'CRITICAL'
        elif runway < 30 or balance < 500:
            return 'HIGH'
        elif runway < 60 or balance < 1000:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_optimization_suggestions(self, breakdown: Dict[str, float]) -> List[str]:
        """Get spending optimization suggestions"""
        
        suggestions = []
        total = sum(breakdown.values())
        
        for category, amount in breakdown.items():
            percentage = (amount / total * 100) if total > 0 else 0
            
            if category == 'gas_fees' and percentage > 30:
                suggestions.append('Consider batching transactions to reduce gas costs')
            elif category == 'api_calls' and percentage > 25:
                suggestions.append('Implement caching to reduce API costs')
            elif category == 'failed_transactions' and amount > 0:
                suggestions.append('Improve transaction validation to avoid failures')
        
        return suggestions
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values (increasing/decreasing/stable)"""
        
        if len(values) < 3:
            return 'stable'
        
        # Simple linear regression
        recent = values[-7:]  # Last week
        older = values[-14:-7]  # Previous week
        
        recent_avg = sum(recent) / len(recent) if recent else 0
        older_avg = sum(older) / len(older) if older else 0
        
        change_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        
        if change_percent > 10:
            return 'increasing'
        elif change_percent < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_balance_trend(self, daily_balances: List[Dict]) -> str:
        """Calculate balance trend"""
        
        balances = [d['balance'] for d in daily_balances]
        return self._calculate_trend(balances)
    
    def _project_balance(self, days: int, avg_burn: float) -> float:
        """Project future balance"""
        
        current = self.manager.get_balance()
        return max(0, current - (avg_burn * days))
    
    async def _trigger_alert_callbacks(self, alerts: List[TreasuryAlert]):
        """Trigger registered callbacks for alerts"""
        
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alerts)
                else:
                    callback(alerts)
            except Exception as e:
                print(f"Error in alert callback: {e}")