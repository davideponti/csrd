# CSRD Comply — Terraform Deployment
# Infrastruttura su DigitalOcean per deployment SaaS multi-tenant
#
# Servizi:
#   - PostgreSQL (DB) — Managed Database
#   - App Platform — Backend FastAPI + Frontend Next.js
#   - Spaces (S3-compatible) — Storage report/esportazioni
#   - Nginx — Reverse proxy con rate limiting

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
  backend "s3" {
    bucket = "csrd-comply-tfstate"
    key    = "infrastructure/terraform.tfstate"
    region = "fra1"
  }
}

provider "digitalocean" {
  token = var.do_token
}

# ── Variables ───────────────────────────────────────────────────

variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "csrd-comply"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "fra1"
}

variable "db_node_size" {
  description = "Database node size"
  type        = string
  default     = "db-s-2vcpu-4gb"
}

variable "app_plan" {
  description = "App Platform plan"
  type        = string
  default     = "professional-xs"
}

# ── Project ─────────────────────────────────────────────────────

resource "digitalocean_project" "csrd_comply" {
  name        = var.project_name
  description = "CSRD Comply — SaaS di conformità CSRD/ESG"
  purpose     = "SaaS Application"
  environment = var.environment
}

# ── PostgreSQL Database ─────────────────────────────────────────

resource "digitalocean_database_cluster" "postgres" {
  name       = "${var.project_name}-db"
  engine     = "pg"
  version    = "16"
  size       = var.db_node_size
  region     = var.region
  node_count = 1

  maintenance_window {
    day  = "sunday"
    hour = "03:00"
  }

  backup_restore {
    database_name = var.project_name
  }
}

resource "digitalocean_database_db" "csrd_comply_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "csrd_comply"
}

resource "digitalocean_database_user" "app_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "csrd_app"
}

resource "digitalocean_database_firewall" "app_access" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "app"
    value = digitalocean_app.app.id
  }
}

# ── Spaces (Object Storage) ────────────────────────────────────

resource "digitalocean_spaces_bucket" "reports" {
  name   = "${var.project_name}-reports-${var.environment}"
  region = var.region
  acl    = "private"

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
        allowed_origins = ["https://csrdcomply.com"]
    max_age_seconds = 3600
  }
}

resource "digitalocean_spaces_bucket" "exports" {
  name   = "${var.project_name}-exports-${var.environment}"
  region = var.region
  acl    = "private"
}

# ── App Platform ────────────────────────────────────────────────

resource "digitalocean_app" "app" {
  spec {
    name   = var.project_name
    region = var.region

    # Backend — FastAPI
    service {
      name               = "backend"
      environment_slug   = "python"
      instance_count     = 2
      instance_size_slug = var.app_plan

      git {
        repo_clone_url = var.repo_clone_url
        branch         = "main"
      }

      source_dir = "backend"

      env {
        key   = "DATABASE_URL"
        value = digitalocean_database_cluster.postgres.uri
        type  = "SECRET"
      }
      env {
        key   = "ENVIRONMENT"
        value = var.environment
      }
      env {
        key   = "ENABLE_MULTITENANCY"
        value = "true"
      }
      env {
        key   = "SECRET_KEY"
        type  = "SECRET"
        value = var.jwt_secret
      }
      env {
        key   = "SPACES_ENDPOINT"
        value = "${var.region}.digitaloceanspaces.com"
      }
      env {
        key   = "SPACES_KEY"
        type  = "SECRET"
        value = var.spaces_access_key
      }
      env {
        key   = "SPACES_SECRET"
        type  = "SECRET"
        value = var.spaces_secret_key
      }

      health_check {
        http_path = "/health"
      }

      routes {
        path = "/api"
        preserve_path_prefix = true
      }
    }

    # Frontend — Next.js
    service {
      name               = "frontend"
      environment_slug   = "node-js"
      instance_count     = 2
      instance_size_slug = var.app_plan

      git {
        repo_clone_url = var.repo_clone_url
        branch         = "main"
      }

      source_dir = "frontend"

      env {
        key   = "NEXT_PUBLIC_API_URL"
        value = "https://api.csrdcomply.com/api/v1"
      }
      env {
        key   = "NODE_ENV"
        value = var.environment
      }

      health_check {
        http_path = "/"
      }
    }

    # Domains
    domain {
      name = "csrdcomply.com"
      type = "DEFAULT"
    }

    domain {
      name = "api.csrdcomply.com"
    }

    # Ingress rules
    ingress {
      rule {
        component {
          name = "frontend"
        }
      }
    }
  }
}

# ── Outputs ─────────────────────────────────────────────────────

output "app_url" {
  value       = "https://csrdcomply.com"
  description = "Application URL"
}

output "api_url" {
  value       = "https://api.csrdcomply.com"
  description = "API URL"
}

output "database_url" {
  value       = digitalocean_database_cluster.postgres.uri
  description = "PostgreSQL connection string"
  sensitive   = true
}

output "spaces_reports_bucket" {
  value       = digitalocean_spaces_bucket.reports.name
  description = "Reports storage bucket"
}

output "live_url" {
  value       = digitalocean_app.app.live_url
  description = "Live App URL"
}
