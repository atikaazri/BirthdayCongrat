# BDVoucher Deployment Guide

## Overview

This guide covers deploying the simplified BDVoucher system in various environments, from development to production.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 256MB RAM
- **Storage**: 100MB free space
- **Network**: Internet access for WhatsApp API
- **Camera**: For QR code scanning (optional)

### Optional Requirements
- **Docker**: For containerized deployment
- **Nginx**: For reverse proxy and SSL termination

## Development Deployment

### 1. Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd BDVoucher

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create .env file with your settings (see Configuration section)

# Test the system
python test_simple.py
```

### 2. Start Development Server

```bash
# Start the application
python app.py
```

### 3. Access Services
- **Web Interface**: http://localhost:5000
- **QR Code Scanner**: Built-in camera scanning
- **System Status**: Live statistics and history

## Production Deployment

### 1. Server Setup

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx

# Create application user
sudo useradd -m -s /bin/bash bdvoucher
sudo usermod -aG sudo bdvoucher
```

#### CentOS/RHEL
```bash
# Update system
sudo yum update -y

# Install Python and dependencies
sudo yum install python3 python3-pip nginx
```

### 2. Application Deployment

```bash
# Switch to application user
sudo su - bdvoucher

# Clone repository
git clone <repository-url>
cd BDVoucher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create .env file with production settings
nano .env
```

### 3. Data Setup

#### CSV Data Configuration
```bash
# Ensure data directory exists
mkdir -p data

# Create employee data file
nano data/employees.csv
# Add your employee data in CSV format

# Create voucher history file
touch data/voucher_history.csv
```

### 4. Systemd Service Configuration

#### Main Service
Create `/etc/systemd/system/bdvoucher.service`:
```ini
[Unit]
Description=BDVoucher Application
After=network.target

[Service]
Type=exec
User=bdvoucher
Group=bdvoucher
WorkingDirectory=/home/bdvoucher/BDVoucher
Environment=PATH=/home/bdvoucher/BDVoucher/venv/bin
ExecStart=/home/bdvoucher/BDVoucher/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable bdvoucher
sudo systemctl start bdvoucher
sudo systemctl status bdvoucher
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/bdvoucher`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Main application
    location / {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enable WebSocket support for camera access
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (if any)
    location /static/ {
        alias /home/bdvoucher/BDVoucher/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/bdvoucher /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Configuration

#### Using Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Docker Deployment

### 1. Dockerfile
Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 bdvoucher && chown -R bdvoucher:bdvoucher /app
USER bdvoucher

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "app.py"]
```

### 2. Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      CAFE_NAME: "Your Cafe Name"
      CAFE_LOCATION: "Your Location"
      VOUCHER_REWARD: "FREE Drink"
      VOUCHER_VALUE: "$15"
      VOUCHER_VALIDITY_HOURS: 24
      MESSAGING_SERVICE: ultramsg
      ULTRAMSG_INSTANCE_ID: your_instance_id
      ULTRAMSG_TOKEN: your_token
      PORT: 5000
      DEBUG: False
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
```

### 3. Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Kubernetes Deployment

### 1. Namespace
Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bdvoucher
```

### 2. ConfigMap
Create `k8s/configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bdvoucher-config
  namespace: bdvoucher
data:
  DATA_SOURCE_TYPE: "postgresql"
  CAFE_NAME: "Your Cafe Name"
  VOUCHER_REWARD: "FREE Drink"
```

### 3. Secret
Create `k8s/secret.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bdvoucher-secrets
  namespace: bdvoucher
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
  ULTRAMSG_TOKEN: <base64-encoded-token>
```

### 4. Deployment
Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bdvoucher
  namespace: bdvoucher
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bdvoucher
  template:
    metadata:
      labels:
        app: bdvoucher
    spec:
      containers:
      - name: api
        image: bdvoucher:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: bdvoucher-config
        - secretRef:
            name: bdvoucher-secrets
      - name: web
        image: bdvoucher:latest
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: bdvoucher-config
        - secretRef:
            name: bdvoucher-secrets
```

## Monitoring and Logging

### 1. Log Management
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/bdvoucher

# Add:
/home/bdvoucher/BDVoucher/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 bdvoucher bdvoucher
}
```

### 2. Health Checks
```bash
# Create health check script
cat > /home/bdvoucher/health_check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:5000/ || exit 1
EOF

chmod +x /home/bdvoucher/health_check.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /home/bdvoucher/health_check.sh
```

### 3. Monitoring with Prometheus
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'bdvoucher'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Backup and Recovery

### 1. Database Backup
```bash
# Create backup script
cat > /home/bdvoucher/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U bdvoucher birthday_vouchers > /home/bdvoucher/backups/db_$DATE.sql
find /home/bdvoucher/backups -name "db_*.sql" -mtime +7 -delete
EOF

chmod +x /home/bdvoucher/backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/bdvoucher/backup.sh
```

### 2. Application Backup
```bash
# Backup application data
tar -czf /home/bdvoucher/backups/app_$(date +%Y%m%d).tar.gz \
  /home/bdvoucher/BDVoucher/data/ \
  /home/bdvoucher/BDVoucher/.env
```

## Security Considerations

### 1. Firewall Configuration
```bash
# UFW configuration
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Application Security
- Use environment variables for sensitive data
- Implement API rate limiting
- Enable HTTPS with valid certificates
- Regular security updates
- Monitor access logs

### 3. Database Security
- Use strong passwords
- Limit database access
- Enable SSL connections
- Regular security patches

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status bdvoucher-api
sudo journalctl -u bdvoucher-api -f

# Check logs
tail -f /home/bdvoucher/BDVoucher/*.log
```

#### Database Connection Issues
```bash
# Test database connection
psql -h localhost -U bdvoucher -d birthday_vouchers

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### API Not Responding
```bash
# Check if port is listening
netstat -tlnp | grep :8000

# Test API endpoint
curl http://localhost:8000/health
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_employees_birthday ON employees (EXTRACT(MONTH FROM date_of_birth), EXTRACT(DAY FROM date_of_birth));
CREATE INDEX idx_vouchers_expires ON vouchers (expires_at);
CREATE INDEX idx_vouchers_redeemed ON vouchers (redeemed);
```

#### Application Optimization
- Use connection pooling
- Implement caching
- Optimize database queries
- Use async operations where possible

## Maintenance

### Regular Tasks
- Monitor disk space
- Check log files
- Update dependencies
- Backup data
- Security patches
- Performance monitoring

### Update Procedure
```bash
# Stop services
sudo systemctl stop bdvoucher-api bdvoucher-web

# Backup current version
cp -r /home/bdvoucher/BDVoucher /home/bdvoucher/BDVoucher.backup

# Update code
cd /home/bdvoucher/BDVoucher
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations (if any)
python src/database/database_setup.py

# Start services
sudo systemctl start bdvoucher-api bdvoucher-web
```

This deployment guide provides comprehensive instructions for deploying BDVoucher in various environments. Choose the deployment method that best fits your infrastructure and requirements.
