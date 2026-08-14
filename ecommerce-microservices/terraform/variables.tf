variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix applied to resource names/tags"
  type        = string
  default     = "ecommerce"
}

variable "environment" {
  description = "Deployment environment (staging/production)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "cluster_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.31"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 3
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 6
}

variable "db_instance_class" {
  description = "RDS instance class -- one per microservice, sized small since each owns a narrow slice of data"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_services" {
  description = "One RDS Postgres instance per service, matching the microservices' per-service-owns-its-database boundary"
  type        = list(string)
  default     = ["auth", "catalog", "orders", "payments", "notifications"]
}

variable "db_username" {
  type      = string
  default   = "ecommerce_app"
  sensitive = true
}
