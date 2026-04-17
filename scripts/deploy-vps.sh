#!/bin/bash
# ============================================
# GE Question Bank - VPS Deployment Script
# Run this on your Hostinger VPS
# ============================================

set -e

echo "=== GE Question Bank - VPS Setup ==="

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# 2. Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 3. Clone or pull repo
if [ ! -d "/opt/ge" ]; then
    echo "Cloning repository..."
    git clone https://github.com/rg412tp/ge.git /opt/ge
else
    echo "Pulling latest changes..."
    cd /opt/ge
    git pull origin main
fi

cd /opt/ge

# 4. Create production env files if not exist
if [ ! -f "backend/.env.production" ]; then
    echo "Creating backend .env.production..."
    echo "Please edit /opt/ge/backend/.env.production with your credentials"
    cp backend/.env.example backend/.env.production
fi

if [ ! -f ".env" ]; then
    echo "Creating root .env..."
    echo "Please edit /opt/ge/.env with your credentials"
    cp .env.example .env
fi

# 5. Build and start
echo "Building containers..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: http://$(hostname -I | awk '{print $1}')"
echo "Backend:  http://$(hostname -I | awk '{print $1}'):8001/api/"
echo ""
echo "NEXT STEPS:"
echo "1. Edit /opt/ge/backend/.env.production with your Gemini key and MongoDB password"
echo "2. Edit /opt/ge/.env with your MongoDB password and domain"
echo "3. Run: cd /opt/ge && docker-compose restart"
echo "4. Point apps.geniuseducation.co.uk DNS to this server IP"
