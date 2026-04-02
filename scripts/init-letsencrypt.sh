#!/bin/bash

# Script to initialize Let's Encrypt SSL certificates
# Run this once on the VPS to obtain initial certificates

DOMAIN="election.thevrstation.co.uk"
EMAIL="admin@thevrstation.co.uk"  # Change this to your email
STAGING=0  # Set to 1 for testing (to avoid rate limits)

# Create required directories
mkdir -p certbot/conf
mkdir -p certbot/www

# Stop any running containers
docker-compose -f docker-compose.prod.yml down

# Start nginx with initial config (no SSL)
echo "Starting nginx with initial configuration..."
cp nginx/nginx-init.conf nginx/nginx.conf.bak
cp nginx/nginx-init.conf nginx/nginx.conf

docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to start
sleep 5

# Request certificate
echo "Requesting Let's Encrypt certificate for $DOMAIN..."

if [ $STAGING -eq 1 ]; then
    STAGING_ARG="--staging"
else
    STAGING_ARG=""
fi

docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    $STAGING_ARG \
    -d $DOMAIN

# Check if certificate was obtained
if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "Certificate obtained successfully!"
    
    # Restore full nginx config with SSL
    mv nginx/nginx.conf.bak nginx/nginx.conf
    
    # Restart all services
    echo "Restarting all services with SSL..."
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --build
    
    echo ""
    echo "=========================================="
    echo "SSL setup complete!"
    echo "Your site is now available at:"
    echo "  https://$DOMAIN"
    echo "  https://$DOMAIN/docs (API documentation)"
    echo "=========================================="
else
    echo "ERROR: Failed to obtain certificate!"
    echo "Check the certbot logs for details."
    # Restore original config
    mv nginx/nginx.conf.bak nginx/nginx.conf
    exit 1
fi
