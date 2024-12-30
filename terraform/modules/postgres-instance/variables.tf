variable "name" {
  description = "Name for the RDS instance and related resources"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the RDS instance will be created"
  type        = string
}

variable "db_name" {
  description = "Name of the default database"
  type        = string
}
variable "subnet_ids" {
  description = "List of subnet IDs for the RDS instance"
  type        = list(string)
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "allocated_storage" {
  description = "The size of the RDS instance storage in GB"
  type        = number
}

variable "username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "theadmin"
}

variable "db_port" {
  description = "Port for the PostgreSQL instance"
  type        = number
  default     = 5432
}
