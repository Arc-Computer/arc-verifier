FROM node:18-slim

WORKDIR /app

COPY package.json .
RUN npm install

COPY market_maker.js .

CMD ["node", "market_maker.js"]