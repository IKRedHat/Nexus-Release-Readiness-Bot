provider "google" {
  project = "nexus-release-bot"
  region  = "us-central1"
}

# Artifact Registry for Docker Images
resource "google_artifact_registry_repository" "nexus_repo" {
  location      = "us-central1"
  repository_id = "nexus-repo"
  format        = "DOCKER"
}

# Cloud SQL for Persistence
resource "google_sql_database_instance" "master" {
  name             = "nexus-db-instance"
  database_version = "POSTGRES_14"
  region           = "us-central1"
  settings {
    tier = "db-f1-micro"
  }
}
