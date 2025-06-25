#!/bin/bash

# MLTC Enumerator Frontend - Development Startup Script

set -e

echo "🚀 Starting MLTC Enumerator Frontend in Development Mode..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create network if it doesn't exist
if ! docker network ls | grep -q mltc-network; then
    echo "📡 Creating Docker network: mltc-network"
    docker network create mltc-network
fi

# Build and start the development container
echo "🔨 Building development container..."
docker-compose -f docker-compose.dev.yml up --build

echo "✅ Frontend development server should be running at http://localhost:3000" 