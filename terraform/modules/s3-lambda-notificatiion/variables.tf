variable "service_name" {
  description = "Name for the api service"
  type        = string
}

variable "lambda_handler" {
  description = "Service python lambda handler"
  type        = string
}

variable "lambda_zip_file" {
  description = "Path to the Lambda zip file"
  type        = string
}

variable "lambda_memory_size" {
  description = "Memory of the lambda"
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 900
}

variable "vpc_id" {
  description = "VPC ID where the Lambda will be created"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets for the Lambda function"
  type        = list(string)
}

variable "db_credential_secret_arn" {
  description = "Database credential seecret arn"
  type        = string
}

variable "db_credential_secret_key_arn" {
  description = "key arn used to encrypt the Database credential"
  type        = string
}

variable "db_security_group_id" {
  description = "Security group ID for the database"
  type        = string
}

variable "db_port" {
  description = "Database port number"
  type        = number
}

variable "db_endpoint" {
  description = "Database endpint"
  type        = string
}

variable "db_name" {
  description = "Name of service database"
  type        = string
}
