#!/usr/bin/env python3
"""
Sample Trading Agent for Arc-Verifier Demo
"""
import time
import random
import json

class TradingAgent:
    def __init__(self):
        self.portfolio = {"BTC": 0, "USD": 100000}
        self.trades = []
        
    def analyze_market(self):
        """Simulate market analysis"""
        # Simulated price
        price = 45000 + random.randint(-1000, 1000)
        trend = random.choice(["bullish", "bearish", "neutral"])
        return price, trend
        
    def execute_trade(self, price, trend):
        """Execute trading decision"""
        if trend == "bullish" and self.portfolio["USD"] > 1000:
            # Buy
            amount = self.portfolio["USD"] * 0.1
            btc_amount = amount / price
            self.portfolio["USD"] -= amount
            self.portfolio["BTC"] += btc_amount
            self.trades.append({
                "action": "buy",
                "price": price,
                "amount": btc_amount,
                "timestamp": time.time()
            })
        elif trend == "bearish" and self.portfolio["BTC"] > 0.01:
            # Sell
            btc_amount = self.portfolio["BTC"] * 0.1
            usd_amount = btc_amount * price
            self.portfolio["BTC"] -= btc_amount
            self.portfolio["USD"] += usd_amount
            self.trades.append({
                "action": "sell",
                "price": price,
                "amount": btc_amount,
                "timestamp": time.time()
            })
    
    def run(self):
        """Main agent loop"""
        print("Trading Agent Started")
        print(f"Initial Portfolio: {self.portfolio}")
        
        while True:
            price, trend = self.analyze_market()
            self.execute_trade(price, trend)
            
            if len(self.trades) % 10 == 0 and len(self.trades) > 0:
                print(f"Trades executed: {len(self.trades)}")
                print(f"Current portfolio: {self.portfolio}")
            
            time.sleep(1)

if __name__ == "__main__":
    agent = TradingAgent()
    agent.run()