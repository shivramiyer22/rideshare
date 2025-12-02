#!/bin/bash

# Dynamic Pricing Solutions - Frontend Installation Script
# This script sets up the frontend application

set -e

echo "🚀 Dynamic Pricing Solutions - Frontend Installation"
echo "=================================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚠️  .env.local not found. It should already exist."
    echo "   If missing, create it with:"
    echo "   NEXT_PUBLIC_API_URL=http://localhost:8000"
    echo "   NEXT_PUBLIC_WS_URL=ws://localhost:8000"
else
    echo "✅ Environment file found"
fi

echo ""
echo "=================================================="
echo "✅ Installation Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Development mode:"
echo "   npm run dev"
echo "   Then open http://localhost:3000"
echo ""
echo "2. Production build:"
echo "   npm run build"
echo "   npm start"
echo ""
echo "3. Deploy with PM2:"
echo "   npm run build"
echo "   pm2 start ../deployment/pm2/ecosystem.config.js"
echo ""
echo "📚 Read QUICKSTART.md for detailed instructions"
echo "📚 Read README.md for full documentation"
echo ""

