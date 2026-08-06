# syntax=docker/dockerfile:1.7
FROM node:20-bookworm-slim

WORKDIR /usr/src/app

# Install deps first (package.json only) for better caching
COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

# Copy application code
COPY . .

ENV NEXT_PUBLIC_API_BASE_URL="/api/v1"
ENV NEXT_PUBLIC_API_HOST="http://backend:5000"

EXPOSE 3000

CMD ["npm", "run", "dev"]
