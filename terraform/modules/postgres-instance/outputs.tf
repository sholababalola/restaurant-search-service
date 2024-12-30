output "db_instance_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "db_instance_port" {
  value = aws_db_instance.postgres.port
}

output "db_security_group_id" {
  value = aws_security_group.rds.id
}

output "kms_key_arn" {
  value = aws_kms_key.rds.arn
}

output "db_credential_secret_arn" {
  value = aws_db_instance.postgres.master_user_secret[0].secret_arn
}
