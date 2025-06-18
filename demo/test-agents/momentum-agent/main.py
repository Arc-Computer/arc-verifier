#!/usr/bin/env python3
"""
Momentum Trading Agent with Market Reaction Logic
Implements trend following with dynamic position sizing based on market conditions
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Deque
from collections import deque
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

app = FastAPI(title="Momentum Trading Agent", version="1.0.0")

# Global state
class TradingState:
    def __init__(self):
        self.positions = {"BTC": 0.0, "ETH": 0.0, "USDT": 100000.0}
        self.trades = []
        self.total_pnl = 0.0
        self.price_history: Dict[str, Deque[float]] = {
            "BTC": deque(maxlen=200),
            "ETH": deque(maxlen=200)
        }
        self.momentum_scores = {"BTC": 0.0, "ETH": 0.0}
        self.market_regime = "neutral"
        self.position_limits = {"BTC": 2.0, "ETH": 10.0}  # Max position sizes
        self.stop_losses = {}  # Track stop loss levels
        self.entry_prices = {}  # Track entry prices for P&L
        
state = TradingState()

# Models
class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    total_trades: int
    total_pnl: float
    market_regime: str

class MetricsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    total_pnl: float
    current_positions: Dict[str, float]
    momentum_scores: Dict[str, float]
    win_rate: float
    avg_win: float
    avg_loss: float

# HTTP Endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for benchmarking"""
    return HealthResponse(
        status="running",
        uptime_seconds=100.0,
        total_trades=len(state.trades),
        total_pnl=state.total_pnl,
        market_regime=state.market_regime
    )

@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Trading metrics endpoint"""
    winning_trades = [t for t in state.trades if t.get("pnl", 0) > 0]
    losing_trades = [t for t in state.trades if t.get("pnl", 0) < 0]
    
    win_rate = len(winning_trades) / len(state.trades) if state.trades else 0
    avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
    
    return MetricsResponse(
        total_trades=len(state.trades),
        winning_trades=len(winning_trades),
        total_pnl=state.total_pnl,
        current_positions={k: v for k, v in state.positions.items() if v != 0},
        momentum_scores=state.momentum_scores.copy(),
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss
    )

# Trading Logic
def calculate_momentum(prices: List[float]) -> float:
    """Calculate momentum score based on price history"""
    if len(prices) < 20:
        return 0.0
    
    # Short-term momentum (20 periods)
    short_return = (prices[-1] - prices[-20]) / prices[-20]
    
    # Medium-term momentum (50 periods)
    if len(prices) >= 50:
        medium_return = (prices[-1] - prices[-50]) / prices[-50]
    else:
        medium_return = short_return
    
    # Trend strength (using moving averages)
    sma_20 = np.mean(prices[-20:])
    sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
    
    trend_strength = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
    
    # Combined momentum score
    momentum = (short_return * 0.5 + medium_return * 0.3 + trend_strength * 0.2)
    
    return momentum

def detect_market_regime(btc_prices: List[float], eth_prices: List[float]) -> str:
    """Detect overall market regime"""
    if len(btc_prices) < 100:
        return "neutral"
    
    # Calculate volatility
    btc_returns = np.diff(btc_prices[-100:]) / btc_prices[-100:-1]
    eth_returns = np.diff(eth_prices[-100:]) / eth_prices[-100:-1]
    
    btc_vol = np.std(btc_returns)
    eth_vol = np.std(eth_returns)
    avg_vol = (btc_vol + eth_vol) / 2
    
    # Calculate trend
    btc_trend = (btc_prices[-1] - btc_prices[-100]) / btc_prices[-100]
    eth_trend = (eth_prices[-1] - eth_prices[-100]) / eth_prices[-100]
    avg_trend = (btc_trend + eth_trend) / 2
    
    # Classify regime
    if avg_vol > 0.03:  # High volatility
        return "high_volatility"
    elif avg_trend > 0.1:  # Strong uptrend
        return "bull_market"
    elif avg_trend < -0.1:  # Strong downtrend
        return "bear_market"
    else:
        return "neutral"

async def execute_momentum_trade(
    symbol: str,
    current_price: float,
    momentum_score: float,
    market_regime: str
):
    """Execute trades based on momentum signals"""
    current_position = state.positions.get(symbol, 0)
    
    # Adjust position sizing based on market regime
    regime_multiplier = {
        "bull_market": 1.2,
        "bear_market": 0.5,
        "high_volatility": 0.7,
        "neutral": 1.0
    }[market_regime]
    
    # Strong bullish momentum - enter or increase position
    if momentum_score > 0.05 and current_position < state.position_limits[symbol]:
        # Calculate position size
        risk_per_trade = 0.02  # 2% risk per trade
        position_value = state.positions["USDT"] * risk_per_trade * regime_multiplier
        amount = min(
            position_value / current_price,
            state.position_limits[symbol] - current_position
        )
        
        if amount > 0.01:  # Minimum trade size
            # Execute buy
            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "momentum_entry",
                "symbol": symbol,
                "side": "buy",
                "price": current_price,
                "amount": amount,
                "momentum_score": momentum_score,
                "market_regime": market_regime,
                "reason": f"Strong momentum signal: {momentum_score:.3f}"
            }
            
            # Update positions
            state.positions["USDT"] -= amount * current_price * 1.001  # Fee
            state.positions[symbol] += amount
            state.entry_prices[symbol] = current_price
            state.stop_losses[symbol] = current_price * 0.95  # 5% stop loss
            
            logger.info(json.dumps(trade))
            state.trades.append(trade)
    
    # Weak/negative momentum or stop loss hit - exit position
    elif (momentum_score < -0.02 or 
          (symbol in state.stop_losses and current_price < state.stop_losses[symbol])) \
          and current_position > 0:
        
        # Calculate P&L
        entry_price = state.entry_prices.get(symbol, current_price)
        pnl = current_position * (current_price - entry_price) - \
              (current_position * current_price * 0.002)  # Fees
        
        reason = "Stop loss triggered" if current_price < state.stop_losses.get(symbol, 0) \
                else f"Momentum reversal: {momentum_score:.3f}"
        
        # Execute sell
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "momentum_exit",
            "symbol": symbol,
            "side": "sell",
            "price": current_price,
            "amount": current_position,
            "pnl": pnl,
            "momentum_score": momentum_score,
            "reason": reason
        }
        
        # Update positions
        state.positions["USDT"] += current_position * current_price * 0.999  # Fee
        state.positions[symbol] = 0
        state.total_pnl += pnl
        
        # Clear tracking
        if symbol in state.stop_losses:
            del state.stop_losses[symbol]
        if symbol in state.entry_prices:
            del state.entry_prices[symbol]
        
        logger.info(json.dumps(trade))
        state.trades.append(trade)
    
    # Trail stop loss for profitable positions
    elif current_position > 0 and symbol in state.entry_prices:
        entry_price = state.entry_prices[symbol]
        if current_price > entry_price * 1.05:  # 5% profit
            # Trail stop to breakeven or higher
            new_stop = max(
                entry_price * 1.01,  # At least 1% above entry
                current_price * 0.95  # 5% below current
            )
            if new_stop > state.stop_losses.get(symbol, 0):
                state.stop_losses[symbol] = new_stop
                logger.info(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "stop_loss_update",
                    "symbol": symbol,
                    "new_stop": new_stop,
                    "current_price": current_price,
                    "reason": "Trailing stop to lock in profits"
                }))

async def simulate_market_data():
    """Simulate realistic market data with trends"""
    # Initialize with real-like prices
    prices = {"BTC": 65000.0, "ETH": 3500.0}
    trends = {"BTC": 0.0, "ETH": 0.0}
    
    while True:
        for symbol in ["BTC", "ETH"]:
            # Update trend (mean-reverting random walk)
            trends[symbol] += np.random.normal(0, 0.002)
            trends[symbol] *= 0.98  # Mean reversion
            
            # Apply trend and noise to price
            price_change = trends[symbol] + np.random.normal(0, 0.001)
            prices[symbol] *= (1 + price_change)
            
            # Store price history
            state.price_history[symbol].append(prices[symbol])
            
            # Calculate momentum if enough history
            if len(state.price_history[symbol]) >= 20:
                state.momentum_scores[symbol] = calculate_momentum(
                    list(state.price_history[symbol])
                )
                
                # Execute trades based on momentum
                await execute_momentum_trade(
                    symbol,
                    prices[symbol],
                    state.momentum_scores[symbol],
                    state.market_regime
                )
        
        # Update market regime periodically
        if len(state.price_history["BTC"]) >= 100:
            state.market_regime = detect_market_regime(
                list(state.price_history["BTC"]),
                list(state.price_history["ETH"])
            )
        
        await asyncio.sleep(1)  # Update every second

async def risk_manager():
    """Monitor and manage portfolio risk"""
    while True:
        # Calculate portfolio metrics
        total_value = state.positions["USDT"]
        for symbol in ["BTC", "ETH"]:
            if symbol in state.price_history and state.price_history[symbol]:
                total_value += state.positions[symbol] * state.price_history[symbol][-1]
        
        # Check drawdown
        if total_value < 90000:  # 10% drawdown
            logger.info(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "risk_alert",
                "reason": "Portfolio drawdown exceeds 10%",
                "total_value": total_value,
                "response": "Reducing position limits"
            }))
            
            # Reduce position limits
            state.position_limits["BTC"] *= 0.8
            state.position_limits["ETH"] *= 0.8
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def run_trading_agent():
    """Main trading loop"""
    logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "agent_start",
        "strategy": "momentum",
        "initial_capital": state.positions["USDT"],
        "risk_profile": "moderate-aggressive",
        "position_limits": state.position_limits
    }))
    
    # Start concurrent tasks
    await asyncio.gather(
        simulate_market_data(),
        risk_manager(),
        return_exceptions=True
    )

# Main entry point
async def main():
    # Start FastAPI server in background
    config = uvicorn.Config(app, host="0.0.0.0", port=8002, log_level="error")
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
            "final_momentum_scores": state.momentum_scores
        }))