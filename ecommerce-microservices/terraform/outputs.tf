output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

output "db_endpoints" {
  description = "Per-service RDS endpoints -- feed these into k8s/base/02-secret.template.yaml"
  value       = { for k, v in aws_db_instance.service_db : k => v.address }
}
