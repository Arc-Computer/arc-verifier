#!/usr/bin/env node
/**
 * Market Maker Agent for Arc-Verifier Demo
 */

class MarketMakerAgent {
    constructor() {
        this.orderBook = {
            bids: [],
            asks: []
        };
        this.balance = {
            USD: 100000,
            BTC: 2
        };
        this.spread = 0.002; // 0.2% spread
        this.orders = [];
    }

    updateOrderBook() {
        // Simulate market price
        const midPrice = 45000 + (Math.random() - 0.5) * 200;
        
        // Create bid/ask orders
        this.orderBook.bids = [
            { price: midPrice * (1 - this.spread), amount: 0.1 },
            { price: midPrice * (1 - this.spread * 2), amount: 0.2 },
            { price: midPrice * (1 - this.spread * 3), amount: 0.3 }
        ];
        
        this.orderBook.asks = [
            { price: midPrice * (1 + this.spread), amount: 0.1 },
            { price: midPrice * (1 + this.spread * 2), amount: 0.2 },
            { price: midPrice * (1 + this.spread * 3), amount: 0.3 }
        ];
    }

    placeOrders() {
        // Place limit orders on both sides
        const newOrders = [];
        
        this.orderBook.bids.forEach(bid => {
            if (this.balance.USD >= bid.price * bid.amount) {
                newOrders.push({
                    side: 'buy',
                    price: bid.price,
                    amount: bid.amount,
                    timestamp: Date.now()
                });
            }
        });
        
        this.orderBook.asks.forEach(ask => {
            if (this.balance.BTC >= ask.amount) {
                newOrders.push({
                    side: 'sell',
                    price: ask.price,
                    amount: ask.amount,
                    timestamp: Date.now()
                });
            }
        });
        
        this.orders = this.orders.concat(newOrders);
        return newOrders;
    }

    simulateFills() {
        // Simulate some orders getting filled
        const filledOrders = [];
        
        this.orders.forEach(order => {
            if (Math.random() < 0.1) { // 10% chance of fill
                if (order.side === 'buy') {
                    this.balance.USD -= order.price * order.amount;
                    this.balance.BTC += order.amount;
                } else {
                    this.balance.USD += order.price * order.amount;
                    this.balance.BTC -= order.amount;
                }
                filledOrders.push(order);
            }
        });
        
        // Remove filled orders
        this.orders = this.orders.filter(o => !filledOrders.includes(o));
        
        return filledOrders;
    }

    run() {
        console.log('Market Maker Agent Started');
        console.log(`Initial Balance: USD: $${this.balance.USD}, BTC: ${this.balance.BTC}`);
        
        let totalFills = 0;
        
        setInterval(() => {
            this.updateOrderBook();
            const newOrders = this.placeOrders();
            const fills = this.simulateFills();
            
            totalFills += fills.length;
            
            if (totalFills % 10 === 0 && totalFills > 0) {
                console.log(`Total fills: ${totalFills}`);
                console.log(`Current balance: USD: $${this.balance.USD.toFixed(2)}, BTC: ${this.balance.BTC.toFixed(4)}`);
                console.log(`Active orders: ${this.orders.length}`);
            }
        }, 1000);
    }
}

// Start the agent
const agent = new MarketMakerAgent();
agent.run();