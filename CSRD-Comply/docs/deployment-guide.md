# CSRD Comply — Deployment Guide (Non-DO Environments)

> **Note**: DigitalOcean deployment is configured via Terraform in `infrastructure/terraform/`.
> This guide covers deployment to **AWS**, **Azure**, **GCP**, and **on-premises** environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Docker-based Deployment (All Platforms)](#docker-based-deployment-all-platforms)
4. [AWS Deployment](#aws-deployment)
5. [Azure Deployment](#azure-deployment)
6. [GCP Deployment](#gcp-deployment)
7. [On-Premises / Self-Hosted](#on-premises--self-hosted)
8. [Database Setup](#database-setup)
9. [Monitoring & Observability](#monitoring--observability)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **PostgreSQL 15+** (managed or self-hosted)
- **Python 3.11+** for backend
- **Node.js 18+** for frontend
- **SMTP server** for transactional emails (optional)
- **Sentry DSN** for error tracking (optional)

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ENVIRONMENT` | No | `development`, `staging`, or `production` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `SENTRY_DSN` | No | Sentry error tracking (recommended in production) |
| `OPENAI_API_KEY` | No | For AI-powered features |
| `ANTHROPIC_API_KEY` | No | For AI-powered features (Claude) |


---

## Docker-based Deployment (All Platforms)

The easiest way to deploy is using the provided `docker-compose.yml`:

```bash
# 1. Build and start all services
docker compose -f infrastructure/docker-compose.yml up -d

# 2. Run database migrations
docker compose exec backend alembic upgrade head

# 3. Verify health
curl http://localhost:8000/health
```

### Docker Compose Services

- **backend**: FastAPI application (port 8000)
- **frontend**: Next.js application (port 3000)
- **nginx**: Reverse proxy with HTTPS termination (port 443)
- **postgres**: Database (if not using managed DB)

---

## AWS Deployment

### Option A: ECS (Elastic Container Service)

1. **Build and push Docker images to ECR:**

```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.eu-west-1.amazonaws.com

docker build -t csrd-backend backend/
docker tag csrd-backend:latest <account>.dkr.ecr.eu-west-1.amazonaws.com/csrd-backend:latest
docker push <account>.dkr.ecr.eu-west-1.amazonaws.com/csrd-backend:latest

docker build -t csrd-frontend frontend/
docker tag csrd-frontend:latest <account>.dkr.ecr.eu-west-1.amazonaws.com/csrd-frontend:latest
docker push <account>.dkr.ecr.eu-west-1.amazonaws.com/csrd-frontend:latest
```

2. **Create ECS task definitions** using the JSON from `infrastructure/` (adapt as needed).

3. **Set up RDS PostgreSQL** (recommended: db.t3.medium minimum for production).

4. **Configure ALB** (Application Load Balancer) with HTTPS certificate via ACM.

5. **Set environment variables** in ECS task definition or Parameter Store.

### Option B: EC2 + Docker Compose

```bash
# On EC2 instance
scp -r infrastructure/ ec2-user@<ip>:/home/ec2-user/
ssh ec2-user@<ip>

# Install Docker & docker-compose
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable docker && sudo systemctl start docker
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy
cd /home/ec2-user
docker compose -f infrastructure/docker-compose.yml up -d
```

**Security groups**: Open ports 443 (HTTPS), 80 (HTTP → redirect to HTTPS), and 5432 (only from app tier).

### Option C: Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application in infrastructure/beanstalk directory
mkdir -p infrastructure/beanstalk
cd infrastructure/beanstalk
eb init csrd-comply --platform docker --region eu-west-1

# Deploy
eb create csrd-comply-prod
```

---

## Azure Deployment

### Option A: Azure Container Apps

1. **Build and push to Azure Container Registry (ACR):**

```bash
az acr login --name <registry>
docker build -t <registry>.azurecr.io/csrd-backend:latest backend/
docker push <registry>.azurecr.io/csrd-backend:latest

docker build -t <registry>.azurecr.io/csrd-frontend:latest frontend/
docker push <registry>.azurecr.io/csrd-frontend:latest
```

2. **Create Container Apps** via Azure Portal or CLI:

```bash
az containerapp create \
  --name csrd-backend \
  --resource-group csrd-rg \
  --image <registry>.azurecr.io/csrd-backend:latest \
  --environment csrd-env \
  --ingress external \
  --target-port 8000 \
  --env-vars DATABASE_URL=<value> SECRET_KEY=<value>
```

3. **Set up Azure Database for PostgreSQL Flexible Server** — ensure SSL enforcement is enabled.

4. **Configure custom domain** and **managed SSL certificate** in Azure Container Apps.

### Option B: Azure Kubernetes Service (AKS)

Deploy using the Kubernetes manifests (adapt `infrastructure/` as needed):

```bash
az aks get-credentials --resource-group csrd-rg --name csrd-aks
kubectl apply -f k8s/
```

### Option C: App Service

```bash
az webapp up \
  --name csrd-comply \
  --resource-group csrd-rg \
  --runtime "PYTHON:3.11" \
  --sku P1V2
```

---

## GCP Deployment

### Option A: Cloud Run

1. **Build and push to Artifact Registry:**

```bash
gcloud builds submit backend/ --tag europe-west1-docker.pkg.dev/<project>/csrd/backend
gcloud builds submit frontend/ --tag europe-west1-docker.pkg.dev/<project>/csrd/frontend
```

2. **Deploy backend:**

```bash
gcloud run deploy csrd-backend \
  --image europe-west1-docker.pkg.dev/<project>/csrd/backend \
  --region europe-west1 \
  --add-cloudsql-instances <instance> \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@//cloudsql/<instance>/csrd,SECRET_KEY=<value>"
```

3. **Set up Cloud SQL for PostgreSQL** — use private IP for security.

4. **Configure Cloud Run domain mapping** for custom domain with managed SSL.

### Option B: Google Kubernetes Engine (GKE)

```bash
gcloud container clusters create csrd-cluster --region europe-west1
kubectl apply -f k8s/
```

### Option C: Compute Engine + Docker

Similar to AWS EC2 approach — deploy using `docker-compose` on a Compute Engine VM instance.

---

## On-Premises / Self-Hosted

### Requirements

- Linux server (Ubuntu 22.04 LTS or Debian 12 recommended)
- PostgreSQL 15+
- Python 3.11+, Node.js 18+
- Nginx or Apache (for reverse proxy)
- systemd (for process management)

### Installation Steps

```bash
# 1. System dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-venv nodejs nginx postgresql

# 2. Clone repository
git clone https://github.com/davideponti/csrd.git /opt/csrd-comply

# 3. Backend setup
cd /opt/csrd-comply/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings

# 4. Database setup
sudo -u postgres psql -c "CREATE DATABASE csrd_comply;"
sudo -u postgres psql -c "CREATE USER csrd WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE csrd_comply TO csrd;"
alembic upgrade head

# 5. Frontend setup
cd /opt/csrd-comply/frontend
npm install
npm run build

# 6. Systemd service (backend)
cat > /etc/systemd/system/csrd-backend.service << 'EOF'
[Unit]
Description=CSRD Comply Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/csrd-comply/backend
ExecStart=/opt/csrd-comply/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/opt/csrd-comply/backend/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable csrd-backend
sudo systemctl start csrd-backend

# 7. Nginx reverse proxy
sudo ln -s /opt/csrd-comply/infrastructure/nginx/default.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. SSL certificate (Let's Encrypt)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Backup Strategy

```bash
# Daily database backup
pg_dump -U csrd csrd_comply | gzip > /var/backups/csrd/db_$(date +%Y%m%d).sql.gz

# Rotate backups (keep 30 days)
find /var/backups/csrd/ -name "db_*.sql.gz" -mtime +30 -delete
```

---

## Database Setup

All environments require PostgreSQL 15+:

```sql
CREATE DATABASE csrd_comply;
CREATE USER csrd WITH PASSWORD '<strong-password>';
GRANT ALL PRIVILEGES ON DATABASE csrd_comply TO csrd;

-- For production, restrict permissions further:
GRANT CONNECT ON DATABASE csrd_comply TO csrd;
GRANT USAGE ON SCHEMA public TO csrd;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO csrd;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO csrd;
```

Run migrations:

```bash
alembic upgrade head
```

---

## Monitoring & Observability

### Sentry (Error Tracking)

Set `SENTRY_DSN` in your `.env` file. The backend already includes Sentry integration via `app/core/monitoring.py`.

### Health Check Endpoint

```
GET /health
```

Returns `{"status": "ok", "version": "1.0.0"}` when the service is running correctly.

### Logging

Logs are structured via `app/core/logging.py`. In production, use a centralized logging solution:

- **AWS**: CloudWatch Logs
- **Azure**: Log Analytics Workspace
- **GCP**: Cloud Logging
- **On-prem**: ELK Stack (Elasticsearch, Logstash, Kibana) or Loki + Grafana

### Metrics

The application exposes health metrics. For full observability, set up:

1. **Prometheus** + **Grafana** for metrics visualization
2. **Uptime monitoring** (e.g., Pingdom, UptimeRobot, or Grafana Cloud)
3. **Database monitoring** (pg_stat_statements, pgbadger)

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|---|---|
| Database connection refused | Check `DATABASE_URL` and firewall/security group rules |
| Migrations fail | Run `alembic upgrade head` manually; check for conflicting migrations |
| CORS errors | Update `CORS_ORIGINS` in `.env` to include your frontend domain |
| SSL certificate expired | Run `certbot renew` (auto-renewal recommended via cron/systemd timer) |
| Out of memory | Increase container/instance memory allocation |
| High database load | Enable connection pooling (PgBouncer recommended) |

### Health Checks

```bash
# Test backend
curl https://yourdomain.com/health

# Test database connection
docker compose exec backend python -c "from app.core.database import SessionLocal; db = SessionLocal(); db.execute('SELECT 1'); db.close(); print('DB OK')"

# Check logs
docker compose logs -f backend
```

---

## Security Checklist

- [x] JWT tokens stored in HttpOnly cookies (XSS-safe)
- [x] Password hashing via bcrypt
- [x] CORS restricted to specific origins
- [x] SQL injection protection (SQLAlchemy ORM)
- [x] Input validation (Pydantic schemas)
- [ ] Enable `secure` flag on cookies (HTTPS required)
- [ ] Set up WAF (Web Application Firewall)
- [ ] Enable database encryption at rest
- [ ] Configure DDoS protection
- [ ] Regular security updates (Docker images, dependencies)
- [ ] Database backup automation
- [ ] Monitoring & alerting configured
- [ ] SSL/TLS enforcement (HTTPS redirect)

---

## Related Documentation

- [Implementation Plan (30 Steps)](./0-1.md)
- [Security Improvements Plan](./SECURITY_IMPROVEMENT_PLAN.md)
- [Terraform Configuration](../infrastructure/terraform/main.tf)
- [Docker Compose Configuration](../infrastructure/docker-compose.yml)
- [Nginx Configuration](../infrastructure/nginx/default.conf)
