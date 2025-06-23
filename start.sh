#!/bin/bash

# MLTC Enumerator Start Script
# This script builds and starts the entire application stack

set -e

echo "🚀 Starting MLTC Enumerator..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Error: docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

echo "🔧 Building and starting services..."

# Stop any existing containers
docker-compose down

# Build and start the services
docker-compose up --build

echo "✅ Services started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/"

# Keep the script running to show logs
echo "Press Ctrl+C to stop all services" 