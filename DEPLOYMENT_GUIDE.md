# 🚀 Complete Deployment & DevOps Guide

Comprehensive guide for deploying OfferSense Marketing Analytics Backend across multiple platforms.

## Table of Contents

1. [Quick Start - Local Development](#quick-start-local-development)
2. [Docker Setup](#docker-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployments](#cloud-deployments)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start - Local Development

### Start the application in 30 seconds:

```bash
# Clone repository
git clone https://github.com/manikswamy3311/offersense-marketing-analytics-backend.git
cd offersense-marketing-analytics-backend

# Start services
docker-compose up

# Access the application
open http://localhost:8000/docs
```

**What's running:**
- API on http://localhost:8000
- Docs on http://localhost:8000/docs
- Redis cache on localhost:6379
- Adminer DB viewer on http://localhost:8080

### Stop services:

```bash
docker-compose down
```

---

## Docker Setup

### 1. Build Docker Image

```bash
# Build with default tag
docker build -t offersense-api:latest .

# Build with version tag
docker build -t offersense-api:v1.0.0 .
```

### 2. Run Container Locally

```bash
# Simple run
docker run -p 8000:8000 offersense-api:latest

# With environment variables
docker run -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e CORS_ORIGINS=http://localhost:5173 \
  offersense-api:latest

# With volume mount
docker run -p 8000:8000 \
  -v $(pwd)/offersense.db:/app/offersense.db \
  -v $(pwd)/logs:/app/logs \
  offersense-api:latest
```

### 3. Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag image
docker tag offersense-api:latest manikswamy3311/offersense-api:latest

# Push
docker push manikswamy3311/offersense-api:latest
```

---

## Production Deployment

### Option A: Docker Compose (VPS/Dedicated Server)

**Best for:** Small-medium teams, full control, cost-effective

**Prerequisites:**
- VPS with Docker & Docker Compose installed
- Domain name (optional but recommended)
- SSL certificates (Let's Encrypt recommended)

**Setup:**

```bash
# SSH into server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/manikswamy3311/offersense-marketing-analytics-backend.git
cd offersense-marketing-analytics-backend

# Copy production env file
cp .env.production .env

# Edit .env with production values
nano .env

# Start production services
docker-compose -f docker-compose-prod.yml up -d

# View logs
docker-compose -f docker-compose-prod.yml logs -f
```

**Features included:**
- PostgreSQL database
- Nginx reverse proxy
- Redis cache
- Prometheus monitoring
- Grafana dashboards
- SSL/TLS support
- Automatic backups

### Option B: Kubernetes

**Best for:** Large-scale, high-availability, complex deployments

**Prerequisites:**
- kubectl installed
- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- helm (optional)

**Deploy:**

```bash
# Create namespace
kubectl apply -f k8s-deployment.yaml

# Check deployment status
kubectl get pods -n offersense

# Port forward for testing
kubectl port-forward -n offersense svc/offersense-api-service 8000:80

# View logs
kubectl logs -n offersense -f deployment/offersense-api

# Scale deployment
kubectl scale deployment offersense-api --replicas=5 -n offersense

# Update deployment
kubectl set image deployment/offersense-api \
  offersense-api=offersense-api:v1.1.0 \
  -n offersense
```

**High Availability Config:**
- 3 API replicas minimum
- PostgreSQL with replication
- Horizontal Pod Autoscaler (2-10 replicas)
- Health checks and readiness probes

---

## Cloud Deployments

### Heroku

```bash
# Login
heroku login
heroku container:login

# Create app
heroku create offersense-api

# Deploy
heroku container:push web
heroku container:release web

# View logs
heroku logs --tail

# Scale dynos
heroku ps:scale web=2
```

### AWS ECS (Fargate)

```bash
# Create ECR repository
aws ecr create-repository --repository-name offersense-api

# Tag and push image
docker tag offersense-api:latest [ECR_URI]/offersense-api:latest
docker push [ECR_URI]/offersense-api:latest

# Deploy with CloudFormation or Terraform
# (See AWS documentation for full setup)
```

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy offersense-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Set environment variables
gcloud run deploy offersense-api \
  --update-env-vars LOG_LEVEL=INFO,CORS_ORIGINS=https://yourdomain.com
```

### DigitalOcean App Platform

1. Push code to GitHub
2. Connect GitHub repo to DigitalOcean
3. Configure `app.yaml`:

```yaml
name: offersense-api
services:
- name: api
  github:
    repo: manikswamy3311/offersense-marketing-analytics-backend
    branch: main
  build_command: docker build -t offersense-api .
  http_port: 8000
```

4. Deploy!

### Railway.app

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

Access Prometheus at `http://localhost:9090`

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'offersense-api'
    static_configs:
      - targets: ['localhost:8000']
```

### 2. Grafana Dashboards

Access Grafana at `http://localhost:3000` (username: admin, password: admin)

- CPU & Memory usage
- Request rates
- Error rates
- Database performance

### 3. Application Logs

```bash
# View container logs
docker-compose logs api

# Follow logs in real-time
docker-compose logs -f api

# View specific timeframe
docker-compose logs --since 10m api

# Export logs
docker-compose logs api > logs.txt
```

### 4. Centralized Logging (Optional)

Setup ELK Stack (Elasticsearch, Logstash, Kibana) or CloudWatch:

```bash
# Docker Compose with ELK
docker-compose -f docker-compose-elk.yml up

# CloudWatch integration
pip install watchtower
```

---

## Backup & Recovery

### Database Backups

```bash
# PostgreSQL backup
docker-compose exec db pg_dump -U offersense offersense > backup.sql

# Restore
docker-compose exec -T db psql -U offersense offersense < backup.sql

# Automated daily backups (cron)
0 2 * * * docker-compose exec db pg_dump -U offersense offersense > /backups/db_$(date +\%Y\%m\%d).sql
```

### Volume Backups

```bash
# Backup volumes
docker run --rm -v offersense_db_data:/data -v $(pwd)/backup:/backup \
  alpine tar czf /backup/db_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v offersense_db_data:/data -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/db_backup.tar.gz -C /data
```

### S3/Cloud Storage

```bash
# Upload to S3
aws s3 cp backup.sql s3://offersense-backups/

# Download from S3
aws s3 cp s3://offersense-backups/backup.sql .
```

---

## Security Best Practices

### 1. Environment Variables

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets manager
# AWS Secrets Manager
# GitHub Secrets
# Vault
```

### 2. SSL/TLS Certificates

```bash
# Let's Encrypt with Certbot
sudo certbot certonly --standalone -d yourdomain.com

# Auto-renew
0 0 1 * * certbot renew --quiet
```

### 3. API Keys & Secrets

```bash
# Generate strong secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Rotate keys regularly
# Implement key versioning
# Store in Vault/Secrets Manager
```

### 4. Network Security

```bash
# UFW Firewall (Ubuntu)
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Rate limiting (nginx)
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

### 5. DDoS Protection

- Use Cloudflare or similar
- Implement rate limiting
- Setup WAF rules

---

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker-compose logs api
# Check for port conflicts
lsof -i :8000
```

**Database connection error:**
```bash
docker-compose exec db psql -U offersense -d offersense
# Check database service status
docker-compose ps
```

**Out of memory:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

**Slow performance:**
```bash
# Monitor logs
docker-compose logs -f api

# Check database indexes
docker-compose exec db psql -U offersense -d offersense \
  -c "SELECT * FROM pg_stat_statements;"
```

### Getting Help

- Check logs: `docker-compose logs api`
- Health endpoint: `curl http://localhost:8000/`
- GitHub Issues: [Create issue](https://github.com/manikswamy3311/offersense-marketing-analytics-backend/issues)

---

## Maintenance

### Regular Tasks

- **Daily:** Review logs, check health
- **Weekly:** Backup database
- **Monthly:** Update dependencies
- **Quarterly:** Security audit

### Update Application

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

---

**Need help?** Check the main [README.md](README.md) or open an issue on GitHub!
