FROM node:18-alpine

# Add Shade agent markers
LABEL shade.agent="true"
LABEL arc.protocol="shade"
LABEL agent.type="trading"

# Environment variables that indicate a Shade agent
ENV SHADE_API_KEY=placeholder
ENV ARC_AGENT_VERSION=1.0.0
ENV AGENT_STRATEGY=arbitrage

# Add some typical agent dependencies
RUN npm install -g web3 ethers axios

# Add agent configuration
WORKDIR /app
RUN echo '{"agent": "shade", "version": "1.0.0", "strategy": "arbitrage"}' > config.json

# Copy agent script
COPY agent.js .

# Typical agent entry point
CMD ["node", "agent.js"]