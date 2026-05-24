# CSRD Comply — Terraform Variables

variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT Secret Key for auth tokens"
  type        = string
  sensitive   = true
}

variable "spaces_access_key" {
  description = "DigitalOcean Spaces Access Key"
  type        = string
  sensitive   = true
}

variable "spaces_secret_key" {
  description = "DigitalOcean Spaces Secret Key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key per AI engine"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API Key per AI engine"
  type        = string
  sensitive   = true
  default     = ""
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "csrd-comply"
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
