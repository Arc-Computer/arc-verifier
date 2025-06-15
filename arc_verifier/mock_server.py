"""Mock API server for agent simulation."""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web
from rich.console import Console


class MockAPIServer:
    """Mock API server that simulates external services during agent testing."""

    def __init__(self, port: int = 8888):
        self.console = Console()
        self.port = port
        self.app = web.Application()
        self.current_scenario_data = {}
        self.api_call_log = []
        self.setup_routes()

    def setup_routes(self):
        """Configure API routes to simulate various services."""
        # Price API endpoints
        self.app.router.add_get(
            "/api/binance/api/v3/ticker/price", self.handle_binance_price
        )
        self.app.router.add_get(
            "/api/coinbase/v2/prices/{pair}/spot", self.handle_coinbase_price
        )

        # Blockchain RPC endpoint
        self.app.router.add_post("/rpc", self.handle_blockchain_rpc)

        # DEX price endpoints for arbitrage testing
        self.app.router.add_get("/api/dex/uniswap/price/{pair}", self.handle_dex_price)
        self.app.router.add_get(
            "/api/dex/sushiswap/price/{pair}", self.handle_dex_price
        )

        # DeFi protocol endpoints
        self.app.router.add_get("/api/aave/markets", self.handle_defi_markets)
        self.app.router.add_get("/api/compound/rates", self.handle_defi_rates)

        # Control endpoints for test orchestration
        self.app.router.add_post("/control/scenario", self.update_scenario)
        self.app.router.add_get("/control/logs", self.get_logs)

    async def handle_binance_price(self, request):
        """Mock Binance price API."""
        symbol = request.query.get("symbol", "ETHUSDT")

        # Log the API call
        self.log_api_call("binance", symbol)

        # Check for configured failures
        if self.current_scenario_data.get("inject_failure") == "api_timeout":
            await asyncio.sleep(10)  # Simulate timeout

        if self.current_scenario_data.get("inject_failure") == "invalid_data":
            return web.json_response({"error": "Invalid response"}, status=500)

        # Return price based on scenario
        price = self.current_scenario_data.get("eth_price", 3000.0)

        return web.json_response({"symbol": symbol, "price": str(price)})

    async def handle_coinbase_price(self, request):
        """Mock Coinbase price API."""
        pair = request.match_info["pair"]

        # Log the API call
        self.log_api_call("coinbase", pair)

        # Check for configured failures
        if self.current_scenario_data.get("inject_failure") == "api_timeout":
            await asyncio.sleep(10)

        if self.current_scenario_data.get("inject_failure") == "invalid_data":
            return web.json_response(
                {"errors": [{"message": "Service unavailable"}]}, status=503
            )

        # Return price based on scenario
        price = self.current_scenario_data.get("eth_price", 3000.0)

        return web.json_response(
            {"data": {"base": "ETH", "currency": "USD", "amount": str(price)}}
        )

    async def handle_dex_price(self, request):
        """Mock DEX price API for arbitrage testing."""
        dex = request.path.split("/")[3]  # Extract DEX name
        pair = request.match_info["pair"]

        self.log_api_call(f"dex_{dex}", pair)

        # Return different prices for different DEXes to simulate arbitrage
        if dex == "uniswap":
            price = self.current_scenario_data.get("eth_price_dex_a", 3000.0)
        else:
            price = self.current_scenario_data.get("eth_price_dex_b", 3000.0)

        return web.json_response(
            {"pair": pair, "price": price, "liquidity": 1000000, "volume24h": 5000000}
        )

    async def handle_defi_markets(self, request):
        """Mock DeFi lending markets data."""
        self.log_api_call("aave", "markets")

        # Simulate lending market data
        markets = [
            {
                "asset": "USDT",
                "apy": self.current_scenario_data.get("usdt_apy", 5.2),
                "utilization": 0.82,
            },
            {
                "asset": "USDC",
                "apy": self.current_scenario_data.get("usdc_apy", 4.8),
                "utilization": 0.75,
            },
            {
                "asset": "DAI",
                "apy": self.current_scenario_data.get("dai_apy", 6.1),
                "utilization": 0.88,
            },
        ]

        return web.json_response({"markets": markets})

    async def handle_defi_rates(self, request):
        """Mock DeFi protocol rates."""
        self.log_api_call("compound", "rates")

        rates = {
            "USDT": {
                "supply_rate": self.current_scenario_data.get("usdt_supply_rate", 4.5),
                "borrow_rate": self.current_scenario_data.get("usdt_borrow_rate", 6.2),
            },
            "ETH": {
                "supply_rate": self.current_scenario_data.get("eth_supply_rate", 2.1),
                "borrow_rate": self.current_scenario_data.get("eth_borrow_rate", 3.8),
            },
        }

        return web.json_response(rates)

    async def handle_blockchain_rpc(self, request):
        """Mock blockchain RPC endpoint."""
        data = await request.json()
        method = data.get("method")

        self.log_api_call("blockchain_rpc", method)

        # Simulate different RPC methods
        if method == "eth_gasPrice":
            gas_price = self.current_scenario_data.get("gas_price", 30)
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": data.get("id", 1),
                    "result": hex(gas_price * 10**9),  # Convert to wei
                }
            )

        elif method == "eth_getBalance":
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": data.get("id", 1),
                    "result": "0x" + "1" * 16,  # Mock balance
                }
            )

        elif method == "eth_sendTransaction":
            # Log transaction attempt
            tx_data = data.get("params", [{}])[0]
            self.log_api_call("transaction", tx_data)

            # Return mock transaction hash
            return web.json_response(
                {"jsonrpc": "2.0", "id": data.get("id", 1), "result": "0x" + "a" * 64}
            )

        return web.json_response(
            {
                "jsonrpc": "2.0",
                "id": data.get("id", 1),
                "error": {"code": -32601, "message": "Method not found"},
            }
        )

    async def update_scenario(self, request):
        """Update current scenario data for mock responses."""
        self.current_scenario_data = await request.json()
        self.console.print(
            f"[green]Scenario updated: {self.current_scenario_data}[/green]"
        )
        return web.json_response({"status": "updated"})

    async def get_logs(self, request):
        """Return API call logs for analysis."""
        return web.json_response(
            {"logs": self.api_call_log, "total_calls": len(self.api_call_log)}
        )

    def log_api_call(self, service: str, endpoint: str):
        """Log API calls for behavioral analysis."""
        log_entry = {
            "service": service,
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "scenario_data": self.current_scenario_data.copy(),
        }
        self.api_call_log.append(log_entry)
        self.console.print(f"[dim]API Call: {service} - {endpoint}[/dim]")

    async def start(self):
        """Start the mock server."""
        self.console.print(
            f"[green]Starting mock API server on port {self.port}[/green]"
        )
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()

    async def stop(self):
        """Stop the mock server."""
        await self.app.shutdown()
        await self.app.cleanup()


class MockServerManager:
    """Manages mock server lifecycle for testing."""

    def __init__(self):
        self.server = MockAPIServer()
        self.server_task = None

    async def start(self):
        """Start mock server in background."""
        await self.server.start()

    async def update_scenario(self, scenario_data: Dict[str, Any]):
        """Update scenario data directly."""
        # Since we're in the same process, update directly instead of via HTTP
        self.server.current_scenario_data.update(scenario_data)

    async def get_logs(self) -> Dict[str, Any]:
        """Retrieve API call logs directly."""
        return {"logs": self.server.api_call_log}

    def run_in_background(self):
        """Run server in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.server.start())
        loop.run_forever()


if __name__ == "__main__":
    # Run mock server standalone for testing
    server = MockAPIServer()
    asyncio.run(server.start())

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock server...")
