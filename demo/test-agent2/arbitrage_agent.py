#!/usr/bin/env python3
"""
Arbitrage Trading Agent for Arc-Verifier Demo
"""
import time
import random
import json

class ArbitrageAgent:
    def __init__(self):
        self.exchanges = {
            "binance": {"BTC": 45000},
            "coinbase": {"BTC": 45100}
        }
        self.balance = {"USD": 50000, "BTC": 0}
        self.trades = []
        
    def find_arbitrage_opportunity(self):
        """Look for price differences between exchanges"""
        binance_price = self.exchanges["binance"]["BTC"] + random.randint(-50, 50)
        coinbase_price = self.exchanges["coinbase"]["BTC"] + random.randint(-50, 50)
        
        self.exchanges["binance"]["BTC"] = binance_price
        self.exchanges["coinbase"]["BTC"] = coinbase_price
        
        spread = abs(binance_price - coinbase_price)
        spread_percentage = (spread / min(binance_price, coinbase_price)) * 100
        
        if spread_percentage > 0.1:  # 0.1% threshold
            return {
                "opportunity": True,
                "buy_exchange": "binance" if binance_price < coinbase_price else "coinbase",
                "sell_exchange": "coinbase" if binance_price < coinbase_price else "binance",
                "spread": spread,
                "spread_percentage": spread_percentage
            }
        return {"opportunity": False}
    
    def execute_arbitrage(self, opportunity):
        """Execute arbitrage trade"""
        if opportunity["opportunity"] and self.balance["USD"] > 1000:
            trade_amount = min(self.balance["USD"] * 0.2, 10000)  # Max 20% or $10k
            
            buy_price = self.exchanges[opportunity["buy_exchange"]]["BTC"]
            sell_price = self.exchanges[opportunity["sell_exchange"]]["BTC"]
            
            btc_amount = trade_amount / buy_price
            profit = (sell_price - buy_price) * btc_amount
            
            self.balance["USD"] += profit
            
            self.trades.append({
                "timestamp": time.time(),
                "type": "arbitrage",
                "buy_exchange": opportunity["buy_exchange"],
                "sell_exchange": opportunity["sell_exchange"],
                "amount": trade_amount,
                "profit": profit,
                "spread_percentage": opportunity["spread_percentage"]
            })
            
            return profit
        return 0
    
    def run(self):
        """Main agent loop"""
        print("Arbitrage Agent Started")
        print(f"Initial Balance: {self.balance}")
        
        while True:
            opportunity = self.find_arbitrage_opportunity()
            
            if opportunity["opportunity"]:
                profit = self.execute_arbitrage(opportunity)
                print(f"Arbitrage executed! Profit: ${profit:.2f}")
            
            if len(self.trades) % 20 == 0 and len(self.trades) > 0:
                total_profit = sum(t["profit"] for t in self.trades)
                print(f"Total trades: {len(self.trades)}, Total profit: ${total_profit:.2f}")
                print(f"Current balance: ${self.balance['USD']:.2f}")
            
            time.sleep(0.5)  # Check twice per second

if __name__ == "__main__":
    agent = ArbitrageAgent()
    agent.run()