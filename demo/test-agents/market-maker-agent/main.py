#!/usr/bin/env python3
"""
Market Maker Agent with Realistic P&L
Provides liquidity by placing bid/ask orders and profiting from spreads
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Maker Agent", version="1.0.0")

@dataclass
class Order:
    id: str
    symbol: str
    side: str  # "buy" or "sell"
    price: float
    amount: float
    timestamp: datetime

# Global state
class TradingState:
    def __init__(self):
        self.positions = {"BTC": 1.0, "ETH": 5.0, "USDT": 50000.0}  # Start with inventory
        self.trades = []
        self.total_pnl = 0.0
        self.order_id_counter = 0
        self.active_orders: Dict[str, Order] = {}
        self.spread_targets = {"BTC": 0.0005, "ETH": 0.0007}  # Target spreads
        self.inventory_targets = {"BTC": 1.0, "ETH": 5.0}  # Target inventory
        self.max_inventory = {"BTC": 2.0, "ETH": 10.0}  # Max inventory
        self.volatility_estimates = {"BTC": 0.001, "ETH": 0.0015}
        self.order_depth = 3  # Number of orders on each side
        self.last_mid_prices = {"BTC": 65000.0, "ETH": 3500.0}
        
state = TradingState()

# Models
class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    total_trades: int
    total_pnl: float
    active_orders: int

class MetricsResponse(BaseModel):
    total_trades: int
    buy_trades: int
    sell_trades: int
    total_pnl: float
    current_positions: Dict[str, float]
    spread_capture_rate: float
    inventory_turnover: float
    active_orders: int

class MarketMakerStats(BaseModel):
    bid_ask_spreads: Dict[str, float]
    inventory_imbalance: Dict[str, float]
    fill_rates: Dict[str, float]

# HTTP Endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for benchmarking"""
    return HealthResponse(
        status="running",
        uptime_seconds=100.0,
        total_trades=len(state.trades),
        total_pnl=state.total_pnl,
        active_orders=len(state.active_orders)
    )

@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Trading metrics endpoint"""
    buy_trades = sum(1 for t in state.trades if t["side"] == "buy")
    sell_trades = sum(1 for t in state.trades if t["side"] == "sell")
    
    # Calculate spread capture rate (simplified)
    profitable_trades = sum(1 for t in state.trades if t.get("pnl", 0) > 0)
    spread_capture_rate = profitable_trades / len(state.trades) if state.trades else 0
    
    # Inventory turnover (trades per unit of inventory)
    avg_inventory = (state.inventory_targets["BTC"] + state.inventory_targets["ETH"]) / 2
    inventory_turnover = len(state.trades) / (avg_inventory * 100) if avg_inventory > 0 else 0
    
    return MetricsResponse(
        total_trades=len(state.trades),
        buy_trades=buy_trades,
        sell_trades=sell_trades,
        total_pnl=state.total_pnl,
        current_positions={k: v for k, v in state.positions.items() if k != "USDT" or v != 0},
        spread_capture_rate=spread_capture_rate,
        inventory_turnover=inventory_turnover,
        active_orders=len(state.active_orders)
    )

@app.get("/market_maker_stats", response_model=MarketMakerStats)
async def market_maker_stats():
    """Market maker specific statistics"""
    # Calculate current spreads
    spreads = {}
    for symbol in ["BTC", "ETH"]:
        buy_orders = [o for o in state.active_orders.values() 
                     if o.symbol == symbol and o.side == "buy"]
        sell_orders = [o for o in state.active_orders.values() 
                      if o.symbol == symbol and o.side == "sell"]
        
        if buy_orders and sell_orders:
            best_bid = max(o.price for o in buy_orders)
            best_ask = min(o.price for o in sell_orders)
            spreads[symbol] = (best_ask - best_bid) / best_bid
        else:
            spreads[symbol] = state.spread_targets[symbol]
    
    # Calculate inventory imbalance
    imbalances = {}
    for symbol in ["BTC", "ETH"]:
        current = state.positions.get(symbol, 0)
        target = state.inventory_targets[symbol]
        imbalances[symbol] = (current - target) / target if target > 0 else 0
    
    # Placeholder fill rates
    fill_rates = {"BTC": 0.65, "ETH": 0.70}  # 65-70% fill rate
    
    return MarketMakerStats(
        bid_ask_spreads=spreads,
        inventory_imbalance=imbalances,
        fill_rates=fill_rates
    )

# Trading Logic
def calculate_dynamic_spread(
    symbol: str,
    base_spread: float,
    inventory_imbalance: float,
    volatility: float
) -> Tuple[float, float]:
    """Calculate bid/ask spreads based on inventory and volatility"""
    # Adjust spread based on volatility
    vol_adjustment = 1 + (volatility / 0.001 - 1) * 0.5  # Higher vol = wider spread
    
    # Adjust spread based on inventory (skew prices to rebalance)
    # If we have too much inventory, lower ask spread (sell more aggressively)
    # If we have too little, lower bid spread (buy more aggressively)
    inventory_skew = inventory_imbalance * 0.3  # 30% max skew
    
    bid_spread = base_spread * vol_adjustment * (1 + inventory_skew)
    ask_spread = base_spread * vol_adjustment * (1 - inventory_skew)
    
    # Ensure minimum spread
    min_spread = 0.0002
    bid_spread = max(bid_spread, min_spread)
    ask_spread = max(ask_spread, min_spread)
    
    return bid_spread, ask_spread

def generate_order_id() -> str:
    """Generate unique order ID"""
    state.order_id_counter += 1
    return f"MM_{state.order_id_counter:06d}"

async def place_orders(symbol: str, mid_price: float):
    """Place multiple bid/ask orders around mid price"""
    # Cancel existing orders for this symbol
    to_cancel = [oid for oid, order in state.active_orders.items() 
                 if order.symbol == symbol]
    for oid in to_cancel:
        del state.active_orders[oid]
    
    # Calculate inventory imbalance
    current_inventory = state.positions.get(symbol, 0)
    target_inventory = state.inventory_targets[symbol]
    imbalance = (current_inventory - target_inventory) / target_inventory
    
    # Get dynamic spreads
    bid_spread, ask_spread = calculate_dynamic_spread(
        symbol,
        state.spread_targets[symbol],
        imbalance,
        state.volatility_estimates[symbol]
    )
    
    # Place multiple orders at different price levels
    for i in range(state.order_depth):
        depth_multiplier = 1 + (i * 0.0002)  # Each level 0.02% further
        
        # Buy orders (only if not at max inventory)
        if current_inventory < state.max_inventory[symbol]:
            buy_price = mid_price * (1 - bid_spread * depth_multiplier)
            buy_amount = 0.01 if symbol == "BTC" else 0.1  # Smaller for BTC
            buy_amount *= (1 + i * 0.5)  # Larger orders further from mid
            
            order = Order(
                id=generate_order_id(),
                symbol=symbol,
                side="buy",
                price=buy_price,
                amount=buy_amount,
                timestamp=datetime.utcnow()
            )
            state.active_orders[order.id] = order
        
        # Sell orders (only if we have inventory)
        if current_inventory > 0.1:
            sell_price = mid_price * (1 + ask_spread * depth_multiplier)
            sell_amount = min(0.01 if symbol == "BTC" else 0.1, current_inventory / 3)
            sell_amount *= (1 + i * 0.5)
            
            order = Order(
                id=generate_order_id(),
                symbol=symbol,
                side="sell",
                price=sell_price,
                amount=sell_amount,
                timestamp=datetime.utcnow()
            )
            state.active_orders[order.id] = order
    
    # Log order placement
    logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "orders_placed",
        "symbol": symbol,
        "mid_price": mid_price,
        "bid_spread": bid_spread,
        "ask_spread": ask_spread,
        "inventory_imbalance": imbalance,
        "active_orders": len([o for o in state.active_orders.values() if o.symbol == symbol])
    }))

async def simulate_order_fills(symbol: str, market_price: float):
    """Simulate order fills based on market price movements"""
    filled_orders = []
    
    for order_id, order in state.active_orders.items():
        if order.symbol != symbol:
            continue
        
        # Check if order should fill
        should_fill = False
        if order.side == "buy" and market_price <= order.price:
            should_fill = True
        elif order.side == "sell" and market_price >= order.price:
            should_fill = True
        
        # Add some randomness (not all touched orders fill)
        if should_fill and np.random.random() < 0.7:  # 70% fill probability
            filled_orders.append(order_id)
            
            # Calculate P&L for this trade
            spread_captured = abs(order.price - state.last_mid_prices[symbol]) / state.last_mid_prices[symbol]
            trade_value = order.amount * order.price
            
            # Market makers profit from spread minus fees
            fee_rate = 0.0002  # 0.02% maker fee
            pnl = trade_value * (spread_captured - fee_rate)
            
            # Execute trade
            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "market_making_fill",
                "symbol": symbol,
                "side": order.side,
                "price": order.price,
                "amount": order.amount,
                "order_id": order_id,
                "pnl": pnl,
                "spread_captured": spread_captured,
                "reason": f"Order filled at {order.price:.2f}"
            }
            
            # Update positions
            if order.side == "buy":
                state.positions["USDT"] -= trade_value * (1 + fee_rate)
                state.positions[symbol] += order.amount
            else:
                state.positions["USDT"] += trade_value * (1 - fee_rate)
                state.positions[symbol] -= order.amount
            
            state.total_pnl += pnl
            logger.info(json.dumps(trade))
            state.trades.append(trade)
    
    # Remove filled orders
    for order_id in filled_orders:
        del state.active_orders[order_id]

async def update_volatility_estimates():
    """Update volatility estimates based on recent price movements"""
    # This would use historical data in production
    # For simulation, add some random walk to volatility
    for symbol in ["BTC", "ETH"]:
        change = np.random.normal(0, 0.0001)
        state.volatility_estimates[symbol] *= (1 + change)
        state.volatility_estimates[symbol] = np.clip(
            state.volatility_estimates[symbol], 0.0005, 0.003
        )

async def inventory_manager():
    """Manage inventory risk and rebalancing"""
    while True:
        for symbol in ["BTC", "ETH"]:
            current = state.positions.get(symbol, 0)
            target = state.inventory_targets[symbol]
            max_inv = state.max_inventory[symbol]
            
            # Emergency liquidation if way over limit
            if current > max_inv * 1.5:
                logger.info(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "emergency_liquidation",
                    "symbol": symbol,
                    "current_inventory": current,
                    "max_allowed": max_inv,
                    "reason": "Inventory limit exceeded by 50%"
                }))
                
                # Adjust spreads to sell more aggressively
                state.spread_targets[symbol] *= 0.5
        
        await asyncio.sleep(60)  # Check every minute

async def simulate_market_data():
    """Simulate market data and trigger order management"""
    while True:
        for symbol in ["BTC", "ETH"]:
            # Simulate price movements
            last_price = state.last_mid_prices[symbol]
            volatility = state.volatility_estimates[symbol]
            
            # Random walk with occasional jumps
            if np.random.random() < 0.05:  # 5% chance of jump
                price_change = np.random.normal(0, volatility * 3)
            else:
                price_change = np.random.normal(0, volatility)
            
            new_price = last_price * (1 + price_change)
            state.last_mid_prices[symbol] = new_price
            
            # Update orders
            await place_orders(symbol, new_price)
            
            # Check for fills
            await simulate_order_fills(symbol, new_price)
        
        # Update volatility estimates
        await update_volatility_estimates()
        
        await asyncio.sleep(0.5)  # Update every 500ms

async def run_trading_agent():
    """Main trading loop"""
    logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "agent_start",
        "strategy": "market_making",
        "initial_capital": state.positions["USDT"],
        "initial_inventory": {k: v for k, v in state.positions.items() if k != "USDT"},
        "risk_profile": "low",
        "spread_targets": state.spread_targets,
        "order_depth": state.order_depth
    }))
    
    # Start concurrent tasks
    await asyncio.gather(
        simulate_market_data(),
        inventory_manager(),
        return_exceptions=True
    )

# Main entry point
async def main():
    # Start FastAPI server in background
    config = uvicorn.Config(app, host="0.0.0.0", port=8003, log_level="error")
    server = uvicorn.Server(config)
    
    # Run server and trading agent concurrently
    await asyncio.gather(
        server.serve(),
        run_trading_agent(),
        return_exceptions=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Final summary
        logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "agent_shutdown",
            "total_trades": len(state.trades),
            "total_pnl": state.total_pnl,
            "final_positions": state.positions,
            "unfilled_orders": len(state.active_orders),
            "final_spreads": state.spread_targets
        }))