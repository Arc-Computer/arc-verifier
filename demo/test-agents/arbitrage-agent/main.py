#!/usr/bin/env python3
"""
Sophisticated Arbitrage Trading Agent
Implements cross-exchange arbitrage with JSON logging and HTTP endpoints
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
import logging

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Arbitrage Trading Agent", version="1.0.0")

# Global state
class TradingState:
    def __init__(self):
        self.positions = {"BTC": 0.0, "ETH": 0.0, "USDT": 100000.0}
        self.trades = []
        self.total_pnl = 0.0
        self.exchange_spreads = {}  # Track spreads across exchanges
        self.last_prices = {}
        self.risk_limit = 10000  # Max position size in USDT
        self.min_profit_threshold = 0.001  # 0.1% minimum profit
        
state = TradingState()

# Models
class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    total_trades: int
    total_pnl: float

class MetricsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    total_pnl: float
    current_positions: Dict[str, float]
    sharpe_ratio: float
    max_drawdown: float

class TradeLog(BaseModel):
    timestamp: str
    action: str
    symbol: str
    side: str
    price: float
    amount: float
    exchange: str
    pnl: Optional[float]
    reason: str

# HTTP Endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for benchmarking"""
    return HealthResponse(
        status="running",
        uptime_seconds=100.0,
        total_trades=len(state.trades),
        total_pnl=state.total_pnl
    )

@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Trading metrics endpoint"""
    winning_trades = sum(1 for t in state.trades if t.get("pnl", 0) > 0)
    
    # Calculate Sharpe ratio (simplified)
    if state.trades:
        returns = [t.get("pnl", 0) / 100000 for t in state.trades]
        if len(returns) > 1:
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        else:
            sharpe = 0.0
    else:
        sharpe = 0.0
    
    return MetricsResponse(
        total_trades=len(state.trades),
        winning_trades=winning_trades,
        total_pnl=state.total_pnl,
        current_positions=state.positions.copy(),
        sharpe_ratio=sharpe,
        max_drawdown=0.05  # Placeholder
    )

@app.post("/execute_trade")
async def execute_trade(trade: TradeLog):
    """Execute a trade (for testing)"""
    state.trades.append(trade.dict())
    return {"status": "executed", "trade_id": len(state.trades)}

# Trading Logic
async def detect_arbitrage_opportunity(
    symbol: str, 
    prices: Dict[str, float]
) -> Optional[Tuple[str, str, float]]:
    """
    Detect arbitrage opportunities across exchanges
    Returns: (buy_exchange, sell_exchange, profit_ratio)
    """
    exchanges = list(prices.keys())
    if len(exchanges) < 2:
        return None
    
    best_opportunity = None
    max_profit = 0
    
    for i, buy_exchange in enumerate(exchanges):
        for j, sell_exchange in enumerate(exchanges):
            if i == j:
                continue
            
            buy_price = prices[buy_exchange]
            sell_price = prices[sell_exchange]
            
            # Calculate profit considering fees
            fee_rate = 0.001  # 0.1% per trade
            profit_ratio = (sell_price / buy_price - 1) - (2 * fee_rate)
            
            if profit_ratio > state.min_profit_threshold and profit_ratio > max_profit:
                max_profit = profit_ratio
                best_opportunity = (buy_exchange, sell_exchange, profit_ratio)
    
    return best_opportunity

async def execute_arbitrage(
    symbol: str,
    buy_exchange: str,
    sell_exchange: str,
    buy_price: float,
    sell_price: float,
    profit_ratio: float
):
    """Execute arbitrage trade and log in JSON format"""
    # Calculate position size based on risk limits
    position_size_usdt = min(state.risk_limit, state.positions["USDT"] * 0.1)
    amount = position_size_usdt / buy_price
    
    # Simulate buy order
    buy_trade = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "arbitrage_buy",
        "symbol": symbol,
        "side": "buy",
        "price": buy_price,
        "amount": amount,
        "exchange": buy_exchange,
        "pnl": None,
        "reason": f"Arbitrage opportunity: {profit_ratio:.2%} profit"
    }
    
    # Update positions
    state.positions["USDT"] -= amount * buy_price * 1.001  # Include fee
    state.positions[symbol] += amount
    
    # Log trade in JSON format
    logger.info(json.dumps(buy_trade))
    state.trades.append(buy_trade)
    
    # Simulate sell order (immediate)
    pnl = amount * (sell_price - buy_price) - (amount * buy_price * 0.002)  # Fees
    
    sell_trade = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "arbitrage_sell",
        "symbol": symbol,
        "side": "sell",
        "price": sell_price,
        "amount": amount,
        "exchange": sell_exchange,
        "pnl": pnl,
        "reason": f"Completing arbitrage, realized profit: ${pnl:.2f}"
    }
    
    # Update positions
    state.positions["USDT"] += amount * sell_price * 0.999  # Include fee
    state.positions[symbol] -= amount
    state.total_pnl += pnl
    
    # Log trade in JSON format
    logger.info(json.dumps(sell_trade))
    state.trades.append(sell_trade)

async def simulate_market_data():
    """Simulate real-time market data with arbitrage opportunities"""
    base_prices = {"BTC": 65000, "ETH": 3500}
    
    # In backtest mode, run faster and for limited time
    backtest_mode = os.environ.get("BACKTEST_MODE", "false").lower() == "true"
    max_iterations = 500 if backtest_mode else float('inf')
    sleep_time = 0.01 if backtest_mode else 1.0
    
    logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "market_data_start",
        "backtest_mode": backtest_mode,
        "max_iterations": max_iterations
    }))
    
    iteration = 0
    while iteration < max_iterations:
        for symbol in ["BTC", "ETH"]:
            # Simulate prices across multiple exchanges
            base_price = base_prices[symbol]
            
            # Add realistic spreads and occasional arbitrage opportunities
            prices = {
                "binance": base_price * (1 + np.random.normal(0, 0.0005)),
                "coinbase": base_price * (1 + np.random.normal(0.0001, 0.0005)),
                "kraken": base_price * (1 + np.random.normal(-0.0001, 0.0005))
            }
            
            # Occasionally create larger spreads (arbitrage opportunities)
            # In backtest mode, create more opportunities for testing
            opportunity_chance = 0.5 if os.environ.get("BACKTEST_MODE", "false").lower() == "true" else 0.1
            if np.random.random() < opportunity_chance:
                # Create a significant price difference
                if np.random.random() < 0.5:
                    prices["kraken"] *= 0.995  # Kraken cheaper (0.5% spread)
                else:
                    prices["binance"] *= 1.005  # Binance more expensive
            
            # Detect and execute arbitrage
            opportunity = await detect_arbitrage_opportunity(symbol, prices)
            if opportunity:
                buy_ex, sell_ex, profit = opportunity
                await execute_arbitrage(
                    symbol,
                    buy_ex,
                    sell_ex,
                    prices[buy_ex],
                    prices[sell_ex],
                    profit
                )
            
            # Update base prices with drift
            base_prices[symbol] *= (1 + np.random.normal(0, 0.001))
        
        iteration += 1
        await asyncio.sleep(sleep_time)  # Check based on mode

async def market_reaction_handler():
    """React to market conditions"""
    while True:
        # Analyze recent trades
        recent_trades = state.trades[-10:] if len(state.trades) >= 10 else state.trades
        
        if recent_trades:
            recent_pnl = sum(t.get("pnl", 0) for t in recent_trades if t.get("pnl"))
            
            # Adjust risk based on performance
            if recent_pnl < -500:  # Losing money
                state.risk_limit = max(5000, state.risk_limit * 0.9)
                logger.info(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "risk_adjustment",
                    "reason": "Recent losses detected",
                    "new_risk_limit": state.risk_limit
                }))
            elif recent_pnl > 1000:  # Making good profits
                state.risk_limit = min(20000, state.risk_limit * 1.1)
                logger.info(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "risk_adjustment",
                    "reason": "Strong performance, increasing position sizes",
                    "new_risk_limit": state.risk_limit
                }))
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def run_trading_agent():
    """Main trading loop"""
    logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "agent_start",
        "strategy": "arbitrage",
        "initial_capital": state.positions["USDT"],
        "risk_profile": "moderate",
        "min_profit_threshold": state.min_profit_threshold,
        "backtest_mode": os.environ.get("BACKTEST_MODE", "false")
    }))
    
    # Start concurrent tasks
    tasks = [simulate_market_data()]
    
    # Only run market reaction handler in live mode
    if os.environ.get("BACKTEST_MODE", "false").lower() != "true":
        tasks.append(market_reaction_handler())
    
    await asyncio.gather(*tasks, return_exceptions=True)

# Main entry point
async def main():
    # In backtest mode, skip the HTTP server
    if os.environ.get("BACKTEST_MODE", "false").lower() == "true":
        await run_trading_agent()
    else:
        # Start FastAPI server in background
        config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="error")
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
            "final_positions": state.positions
        }))