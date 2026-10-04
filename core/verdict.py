"""
Verdict Engine for Evaluating Edge Rigor after Costs.

Produces honest classification:
- 'Signal found'
- 'Marginal'
- 'No persistent edge after costs'
"""

from typing import Dict, Any

def evaluate_verdict(metrics: Dict[str, Any], is_synthetic: bool = False) -> Dict[str, str]:
    """
    Evaluates backtest performance metrics against institutional edge thresholds.
    """
    sharpe = metrics.get("sharpe_ratio", 0.0)
    net_return = metrics.get("net_return_pct", 0.0)
    hit_rate = metrics.get("hit_rate_pct", 0.0)
    total_trades = metrics.get("total_trades", 0)
    
    demo_suffix = " (Result on DEMO data)" if is_synthetic else ""
    
    if total_trades < 3:
        verdict = "No persistent edge after costs"
        reason = f"Insufficient trade sample size ({total_trades} trades executed) to confirm statistically significant mispricing."
        color = "#e74c3c"  # Red
    elif sharpe >= 1.0 and net_return >= 4.0 and hit_rate >= 52.0:
        verdict = "Signal found"
        reason = f"Statistically robust edge detected with Net Sharpe ratio of {sharpe:.2f}, net return of {net_return:.2f}%, and hit rate of {hit_rate:.1f}% after trading costs."
        color = "#2ecc71"  # Green
    elif sharpe >= 0.3 and net_return > 0.0:
        verdict = "Marginal"
        reason = f"Weak relative value edge. Net return is positive ({net_return:.2f}%), but Sharpe ratio ({sharpe:.2f}) is vulnerable to slippage and market friction."
        color = "#f39c12"  # Amber
    else:
        verdict = "No persistent edge after costs"
        reason = f"No persistent edge survives transaction costs and bid-ask slippage. Net return ({net_return:.2f}%) and Sharpe ({sharpe:.2f}) do not justify execution risk."
        color = "#e74c3c"  # Red
        
    full_verdict_label = f"{verdict}{demo_suffix}"
    
    return {
        "status": verdict,
        "full_label": full_verdict_label,
        "reason": reason,
        "color": color,
        "is_synthetic": is_synthetic,
    }
