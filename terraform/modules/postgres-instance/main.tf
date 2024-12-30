resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.name}-kms-key"
  }
}

resource "aws_kms_alias" "service_key_alias" {
  name          = "alias/${var.name}-key"
  target_key_id = aws_kms_key.rds.id
}

resource "aws_security_group" "rds" {
  name        = "${var.name}-rds-sg"
  description = "Security group for RDS instance"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name}-rds-sg"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                      = var.name
  engine                          = "postgres"
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  copy_tags_to_snapshot           = true
  deletion_protection             = terraform.workspace == "prod" ? true : false
  db_name                         = var.db_name
  engine_version                  = var.engine_version
  instance_class                  = var.instance_class
  allocated_storage               = var.allocated_storage
  storage_encrypted               = true
  kms_key_id                      = aws_kms_key.rds.arn
  manage_master_user_password     = true
  master_user_secret_kms_key_id   = aws_kms_key.rds.arn
  username                        = var.username
  vpc_security_group_ids          = [aws_security_group.rds.id]
  db_subnet_group_name            = aws_db_subnet_group.rds.name
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${var.name}-${uuid()}"
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  max_allocated_storage           = 200


  tags = {
    Name = var.name
  }
}

resource "aws_db_subnet_group" "rds" {
  name       = "${var.name}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.name}-db-subnet-group"
  }
}
