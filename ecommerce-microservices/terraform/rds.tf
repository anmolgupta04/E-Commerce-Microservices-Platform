resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "${local.name_prefix}-db-subnets" }
}

resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from EKS nodes only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_eks_cluster.main.vpc_config[0].cluster_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-rds-sg" }
}

resource "random_password" "db_password" {
  for_each = toset(var.db_services)
  length   = 24
  special  = false
}

# One instance per service -- deliberately not one shared RDS instance
# with 5 schemas, so a noisy-neighbor or a bad migration in one service
# can never take another service's database down with it.
resource "aws_db_instance" "service_db" {
  for_each = toset(var.db_services)

  identifier             = "${local.name_prefix}-${each.value}-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  storage_encrypted      = true
  db_name                = "${each.value}_db"
  username               = var.db_username
  password               = random_password.db_password[each.value].result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = var.environment == "production"
  backup_retention_period = 7
  skip_final_snapshot    = var.environment != "production"
  deletion_protection    = var.environment == "production"

  tags = { Name = "${local.name_prefix}-${each.value}-db", Service = each.value }
}

# Passwords land in Secrets Manager, not in tfstate-adjacent output files --
# the k8s ExternalSecret / CI render step reads from here.
resource "aws_secretsmanager_secret" "db_password" {
  for_each = toset(var.db_services)
  name     = "${local.name_prefix}/${each.value}/db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  for_each      = toset(var.db_services)
  secret_id     = aws_secretsmanager_secret.db_password[each.value].id
  secret_string = random_password.db_password[each.value].result
}
