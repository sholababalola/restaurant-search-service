variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "postgres_instance_class" {
  description = "Postgres instance class"
  type        = string
}

variable "postgres_allocated_storage" {
  description = "initial storage size for database"
  type = number
}

variable "api_stage_name" {
  description = "Api stage namee"
  type        = string
}
variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets"
  type        = list(string)
}

variable "availability_zones" {
  description = "List of availability zones for the private subnets"
  type        = list(string)
}