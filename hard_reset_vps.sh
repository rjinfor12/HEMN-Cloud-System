#!/bin/bash
echo "Stooping service..."
systemctl stop hemn_cloud
echo "Killing rogue processes..."
pkill -9 uvicorn
pkill -9 python
echo "Cleaning __pycache__..."
find /var/www/hemn_cloud -name "__pycache__" -type d -exec rm -rf {} +
echo "Starting service..."
systemctl start hemn_cloud
sleep 2
systemctl is-active hemn_cloud
