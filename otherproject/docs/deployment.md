# Deployment Guide

## Overview

Comprehensive deployment procedures for the Digital Rental Contract Management System, covering development, staging, and production environments.

## Prerequisites

### System Requirements
- Docker 20.10+ and Docker Compose 2.0+
- PostgreSQL 13+ (production)
- Python 3.10+ (development)
- 2GB RAM minimum, 4GB recommended
- 10GB storage minimum

### Required Accounts
- eSignatures.com API account with API key
- Domain name and SSL certificate (production)
- Cloud provider account (optional)

## Development Deployment

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd Online-Mietvertrag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from db.database import create_tables; create_tables()"

# Run application
streamlit run app.py
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Deployment

### Option 1: Docker Compose Production

#### 1. Prepare Production Environment
```bash
# Create production directory
mkdir -p /opt/mietvertrag
cd /opt/mietvertrag

# Clone repository
git clone <repository-url> .
git checkout main
```

#### 2. Configure Environment
```bash
# Create production environment file
cp .env.example .env.production

# Edit configuration
nano .env.production

# Key production settings:
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://user:password@db:5432/mietvertrag
ESIGNATURES_SANDBOX=false
SECURE_COOKIES=true
```

#### 3. Setup SSL/TLS
```bash
# Create SSL directory
mkdir -p ssl

# Copy SSL certificates
cp /path/to/cert.pem ssl/
cp /path/to/key.pem ssl/
```

#### 4. Deploy with Docker Compose
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose exec app python -c "from db.database import create_tables; create_tables()"

# Verify deployment
docker-compose ps
docker-compose logs app
```

### Option 2: Kubernetes Deployment

#### 1. Create Kubernetes Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mietvertrag

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mietvertrag-secrets
  namespace: mietvertrag
type: Opaque
data:
  secret-key: <base64-encoded-secret-key>
  esignatures-api-key: <base64-encoded-api-key>
  jwt-secret-key: <base64-encoded-jwt-secret>

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mietvertrag-config
  namespace: mietvertrag
data:
  APP_ENV: "production"
  DEBUG: "false"
  HOST: "0.0.0.0"
  PORT: "8501"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mietvertrag-app
  namespace: mietvertrag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mietvertrag
  template:
    metadata:
      labels:
        app: mietvertrag
    spec:
      containers:
      - name: app
        image: your-registry/mietvertrag:latest
        ports:
        - containerPort: 8501
        envFrom:
        - configMapRef:
            name: mietvertrag-config
        - secretRef:
            name: mietvertrag-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mietvertrag-service
  namespace: mietvertrag
spec:
  selector:
    app: mietvertrag
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mietvertrag-ingress
  namespace: mietvertrag
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: mietvertrag-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mietvertrag-service
            port:
              number: 80
```

#### 2. Deploy to Kubernetes
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n mietvertrag
kubectl get services -n mietvertrag
kubectl get ingress -n mietvertrag

# View logs
kubectl logs -f deployment/mietvertrag-app -n mietvertrag
```

## Database Migration

### SQLite to PostgreSQL Migration
```bash
# 1. Export SQLite data
sqlite3 app.db .dump > backup.sql

# 2. Convert SQLite dump to PostgreSQL format
sed -i 's/INTEGER PRIMARY KEY AUTOINCREMENT/SERIAL PRIMARY KEY/g' backup.sql
sed -i 's/DATETIME DEFAULT CURRENT_TIMESTAMP/TIMESTAMP DEFAULT CURRENT_TIMESTAMP/g' backup.sql

# 3. Import to PostgreSQL
psql -h localhost -U username -d mietvertrag < backup.sql

# 4. Update environment configuration
DATABASE_URL=postgresql://username:password@localhost:5432/mietvertrag
```

### Database Backup Strategy
```bash
# Automated PostgreSQL backup script
#!/bin/bash
# backup.sh

DB_NAME="mietvertrag"
DB_USER="username"
DB_HOST="localhost"
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Schedule with cron: 0 2 * * * /path/to/backup.sh
```

## Monitoring and Health Checks

### Health Check Endpoints
```python
# health.py
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/ready")
async def readiness_check():
    """Readiness check including database connectivity."""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        
        # Check external services
        # ... eSignatures.com API check ...
        
        return {"status": "ready", "checks": {"database": "ok", "external_api": "ok"}}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
```

### Monitoring Setup
```bash
# Prometheus metrics endpoint
pip install prometheus-client

# Add to requirements.txt
echo "prometheus-client==0.16.0" >> requirements.txt

# Grafana dashboard configuration available in /monitoring/grafana-dashboard.json
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet
```

### Manual SSL Certificate
```bash
# Create SSL directory
mkdir -p /opt/mietvertrag/ssl

# Copy certificates
cp yourdomain.com.crt /opt/mietvertrag/ssl/
cp yourdomain.com.key /opt/mietvertrag/ssl/

# Set permissions
chmod 600 /opt/mietvertrag/ssl/*
chown root:root /opt/mietvertrag/ssl/*
```

## Security Hardening

### Production Security Checklist
- [ ] Enable firewall (UFW/iptables)
- [ ] Configure fail2ban for SSH protection
- [ ] Set up SSL/TLS certificates
- [ ] Enable security headers
- [ ] Configure CORS properly
- [ ] Use secrets management
- [ ] Set up log monitoring
- [ ] Regular security updates
- [ ] Database access restrictions
- [ ] File system permissions

### Firewall Configuration
```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## Scaling Considerations

### Horizontal Scaling
```yaml
# Update deployment replicas
spec:
  replicas: 5  # Scale to 5 instances

# Auto-scaling configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mietvertrag-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mietvertrag-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Load Balancing
```nginx
# nginx.conf
upstream mietvertrag_backend {
    server app1:8501;
    server app2:8501;
    server app3:8501;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://mietvertrag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Rollback Procedures

### Application Rollback
```bash
# Docker Compose rollback
docker-compose down
git checkout previous-stable-tag
docker-compose up -d

# Kubernetes rollback
kubectl rollout undo deployment/mietvertrag-app -n mietvertrag
kubectl rollout status deployment/mietvertrag-app -n mietvertrag
```

### Database Rollback
```bash
# Restore from backup
gunzip -c backup_20240101_020000.sql.gz | psql -h localhost -U username -d mietvertrag
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose logs app

# Check environment variables
docker-compose exec app env | grep -E "(SECRET_KEY|DATABASE_URL|ESIGNATURES)"

# Test database connection
docker-compose exec app python -c "from db.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U username -d mietvertrag -c "SELECT 1;"

# Check network connectivity
docker-compose exec app nc -zv db 5432
```

#### eSignatures.com API Issues
```bash
# Test API connectivity
curl -H "Authorization: Bearer $ESIGNATURES_API_KEY" \
     https://api.esignatures.com/v1/health

# Check API quotas and limits in eSignatures.com dashboard
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check database performance
psql -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Monitor application metrics
curl http://localhost:9090/metrics
```
