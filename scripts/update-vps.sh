#!/bin/bash
# ============================================
# GE Question Bank - Update Script
# Run this after pushing changes to GitHub
# ============================================

set -e

cd /opt/ge

echo "=== Pulling latest changes ==="
git pull origin main

echo "=== Rebuilding containers ==="
docker-compose build

echo "=== Restarting services ==="
docker-compose down
docker-compose up -d

echo "=== Update complete ==="
docker-compose ps
