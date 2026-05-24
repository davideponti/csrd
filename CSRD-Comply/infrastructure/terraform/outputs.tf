# CSRD Comply — Terraform Outputs

output "app_live_url" {
  value       = digitalocean_app.app.live_url
  description = "Live URL dell'applicazione"
}

output "app_url" {
  value       = "https://csrdcomply.io"
  description = "URL principale dell'applicazione"
}

output "api_url" {
  value       = "https://api.csrdcomply.io"
  description = "URL dell'API"
}

output "database_connection" {
  value       = digitalocean_database_cluster.postgres.uri
  description = "URI di connessione al database PostgreSQL"
  sensitive   = true
}

output "database_host" {
  value       = digitalocean_database_cluster.postgres.host
  description = "Host del database"
}

output "database_port" {
  value       = digitalocean_database_cluster.postgres.port
  description = "Porta del database"
}

output "spaces_reports_bucket" {
  value       = digitalocean_spaces_bucket.reports.name
  description = "Nome del bucket Spaces per i report"
}

output "spaces_exports_bucket" {
  value       = digitalocean_spaces_bucket.exports.name
  description = "Nome del bucket Spaces per le esportazioni"
}

output "project_id" {
  value       = digitalocean_project.csrd_comply.id
  description = "ID del progetto DigitalOcean"
}

output "app_id" {
  value       = digitalocean_app.app.id
  description = "ID dell'App Platform"
}

output "db_cluster_id" {
  value       = digitalocean_database_cluster.postgres.id
  description = "ID del cluster database"
}
