# 🐳 OfferSense Backend - Docker & Deployment Guide

This guide covers containerization, deployment, and production setup for the OfferSense Marketing Analytics Backend.

## Table of Contents

1. [Docker Setup](#docker-setup)
2. [Local Development with Docker](#local-development-with-docker)
3. [Building Images](#building-images)
4. [Production Deployment](#production-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

---

## Docker Setup

### Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose installed (included with Docker Desktop)
- Git and this repository cloned

### Verify Installation

```bash
docker --version
docker-compose --version
```

---

## Local Development with Docker

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/manikswamy3311/offersense-marketing-analytics-backend.git
cd offersense-marketing-analytics-backend
```

2. **Start the application**
```bash
docker-compose up
```

This will:
- Build the Docker image
- Start the API service on `http://localhost:8000`
- Initialize the database
- Mount local code for hot-reload development

3. **Access the API**
- API Base: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Building Images

### Build Locally

```bash
# Build with default tag
docker build -t offersense-api:latest .

# Build with custom tag
docker build -t offersense-api:v1.0.0 .
```

### View Built Images

```bash
docker images | grep offersense
```

### Push to Registry

```bash
# Login to Docker Hub
docker login

# Tag image for registry
docker tag offersense-api:latest manikswamy3311/offersense-api:latest

# Push image
docker push manikswamy3311/offersense-api:latest
```

---

## Production Deployment

### Cloud Deployment Options

#### 1. **AWS ECS (Elastic Container Service)**

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Push to ECR (Elastic Container Registry)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ECR_URI]
docker tag offersense-api:latest [ECR_URI]/offersense-api:latest
docker push [ECR_URI]/offersense-api:latest
```

#### 2. **Heroku Deployment**

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create Heroku app
heroku create offersense-api

# Set up container registry
heroku container:login

# Push image
heroku container:push web

# Release
heroku container:release web

# View logs
heroku logs --tail
```

#### 3. **Google Cloud Run**

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Configure project
gcloud config set project [PROJECT_ID]

# Build and push
gcloud builds submit --tag gcr.io/[PROJECT_ID]/offersense-api

# Deploy
gcloud run deploy offersense-api \
  --image gcr.io/[PROJECT_ID]/offersense-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### 4. **DigitalOcean App Platform**

1. Push code to GitHub
2. Connect GitHub repository to DigitalOcean
3. Add `app.yaml` configuration:

```yaml
name: offersense-api
services:
- name: api
  github:
    repo: manikswamy3311/offersense-marketing-analytics-backend
    branch: main
  build_command: docker build -t offersense-api .
  http_port: 8000
  source_dir: .
```

#### 5. **Docker Compose on VPS (DigitalOcean, Linode, AWS EC2)**

```bash
# SSH into server
ssh root@[SERVER_IP]

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repository
git clone https://github.com/manikswamy3311/offersense-marketing-analytics-backend.git
cd offersense-marketing-analytics-backend

# Create .env file
cp .env.example .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
```

---

## Environment Configuration

### Development (.env.example)

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# Database
DATABASE_URL=offersense.db

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Production (.env)

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database (consider PostgreSQL for production)
DATABASE_URL=postgresql://user:password@db-host:5432/offersense

# CORS (restrict to your frontend domain)
CORS_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=WARNING

# Security
SECRET_KEY=use-a-strong-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Set Environment in Docker

In `docker-compose.yml` or deployment:

```bash
# Inline
docker run -e API_PORT=8000 -e LOG_LEVEL=INFO ...

# From file
docker run --env-file .env ...

# In docker-compose.yml
environment:
  - API_PORT=8000
  - LOG_LEVEL=INFO
```

---

## Container Orchestration

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: offersense-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: offersense-api
  template:
    metadata:
      labels:
        app: offersense-api
    spec:
      containers:
      - name: api
        image: offersense-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: offersense-api-service
spec:
  selector:
    app: offersense-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get services
kubectl logs -l app=offersense-api -f
```

---

## Performance Optimization

### Multi-Stage Docker Build

```dockerfile
# Build stage
FROM python:3.9 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## Monitoring & Logging

### Docker Health Checks

```bash
# Check health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View container stats
docker stats offersense-api
```

### Logging Services

- **Local**: `docker logs` command
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Datadog**: [https://www.datadoghq.com/](https://www.datadoghq.com/)
- **New Relic**: [https://newrelic.com/](https://newrelic.com/)

---

## Security Best Practices

1. **Use Environment Variables** for sensitive data
2. **Never commit secrets** to version control
3. **Use read-only file systems** in production
4. **Run as non-root user** in Dockerfile
5. **Scan images** for vulnerabilities:
   ```bash
   docker scan offersense-api:latest
   ```
6. **Use private registries** for proprietary images
7. **Keep base images updated**
8. **Implement rate limiting** and authentication

---

## Troubleshooting

### Container Won't Start

```bash
# View error logs
docker logs offersense-api

# Check Docker daemon
docker version

# Rebuild image
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 [PID]

# Or use different port
docker run -p 8001:8000 offersense-api:latest
```

### Database Connection Issues

```bash
# Check volume persistence
docker volume ls

# Verify database file
docker exec offersense-api ls -la /app/

# Reinitialize database
docker exec offersense-api python -m app.database.init_db
```

### Memory Issues

```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml or deployment config
```

---

## Summary

Your backend is now **containerized and deployment-ready**! You can:

✅ Run locally with hot-reload development  
✅ Deploy to cloud platforms (AWS, Google Cloud, Heroku, DigitalOcean)  
✅ Scale with Kubernetes  
✅ Monitor and log efficiently  
✅ Apply security best practices  

**Next Steps:**
- Deploy to your preferred cloud platform
- Set up CI/CD pipeline
- Configure monitoring and alerts
- Implement backup strategy for database

---

**Version**: 1.0.0  
**Last Updated**: June 2026
