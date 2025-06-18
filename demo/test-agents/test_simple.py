#!/usr/bin/env python3
"""Simple test to verify agent produces output"""

import json
import os
from datetime import datetime

# Simple sync test
print(json.dumps({
    "timestamp": datetime.utcnow().isoformat(),
    "action": "test_start",
    "backtest_mode": os.environ.get("BACKTEST_MODE", "false")
}))

# Simulate some trades
for i in range(5):
    print(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "arbitrage_buy",
        "symbol": "BTC",
        "side": "buy",
        "price": 65000 + i * 10,
        "amount": 0.1,
        "exchange": "binance",
        "reason": f"Test trade {i}"
    }))
    
    print(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "arbitrage_sell",
        "symbol": "BTC",
        "side": "sell",
        "price": 65100 + i * 10,
        "amount": 0.1,
        "exchange": "kraken",
        "pnl": 10.0,
        "reason": f"Completing arbitrage {i}"
    }))

print(json.dumps({
    "timestamp": datetime.utcnow().isoformat(),
    "action": "test_complete",
    "total_trades": 10
}))