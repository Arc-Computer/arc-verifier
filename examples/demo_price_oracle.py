#!/usr/bin/env python3
"""Demo price oracle agent for testing Arc-Verifier simulation."""

import os
import time
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s", "action":"%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def fetch_eth_price():
    """Fetch ETH price from mock API."""
    # Check if we're in mock mode
    if os.getenv('MOCK_MODE') == 'true':
        api_url = os.getenv('API_BINANCE_URL', 'http://localhost:8888/api/binance')
    else:
        api_url = 'https://api.binance.com/api/v3/ticker/price'
    
    # Log the price fetch action
    logging.info(json.dumps({
        "type": "fetch_price",
        "details": {"source": "binance", "url": api_url}
    }))
    
    # In a real agent, this would make an HTTP request
    # For demo, we'll simulate with a mock price
    price = 3000.0
    
    # Log successful price retrieval
    logging.info(json.dumps({
        "type": "price_retrieved", 
        "details": {"price": price, "timestamp": datetime.now().isoformat()}
    }))
    
    return price

def update_oracle_price(price):
    """Update on-chain oracle with new price."""
    # Log update action
    logging.info(json.dumps({
        "type": "update_price",
        "details": {"new_price": price, "contract": "price-oracle.near"}
    }))
    
    # In a real agent, this would send a transaction
    # For demo, we'll just log success
    time.sleep(1)
    
    logging.info(json.dumps({
        "type": "price_updated",
        "details": {"success": True, "tx_hash": f"0x{'a'*64}"}
    }))

def main():
    """Main oracle loop."""
    logging.info(json.dumps({
        "type": "agent_started",
        "details": {"agent_type": "price_oracle", "version": "1.0.0"}
    }))
    
    while True:
        try:
            # Fetch current price
            price = fetch_eth_price()
            
            # Update oracle
            update_oracle_price(price)
            
            # Wait before next update
            time.sleep(30)
            
        except Exception as e:
            # Log error handling
            logging.info(json.dumps({
                "type": "error_handled",
                "details": {"error": str(e), "action": "retry"}
            }))
            time.sleep(5)

if __name__ == "__main__":
    main()