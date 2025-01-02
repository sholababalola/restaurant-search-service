terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "vpc" {
  source               = "./modules/vpc"
  vpc_name             = "${terraform.workspace}-restaurant-service"
  cidr_block           = var.cidr_block
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  availability_zones   = var.availability_zones
}

module "postgres" {
  source            = "./modules/postgres-instance"
  name              = "${terraform.workspace}-restaurant-instance"
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  db_name           = "restaurants"
  engine_version    = "17.2"
  instance_class    = var.postgres_instance_class
  allocated_storage = var.postgres_allocated_storage
}

module "api_gateway_account" {
  source = "./modules/apigateway-account"
}

module "api" {
  source                       = "./modules/api-service"
  api_name                     = "${terraform.workspace}-restaurant-service"
  api_stage_name               = var.api_stage_name
  lambda_zip_file              = "../service-api.zip"
  vpc_id                       = module.vpc.vpc_id
  subnet_ids                   = module.vpc.private_subnet_ids
  db_credential_secret_arn     = module.postgres.db_credential_secret_arn
  db_credential_secret_key_arn = module.postgres.kms_key_arn
  db_security_group_id         = module.postgres.db_security_group_id
  db_port                      = module.postgres.db_instance_port
  db_endpoint                  = module.postgres.db_instance_endpoint
  db_name                      = "restaurants"

  depends_on = [module.postgres, module.api_gateway_account]
}

module "restaurant-etl" {
  source                       = "./modules/s3-lambda-notificatiion"
  service_name              = "${terraform.workspace}-restaurant-etl"
  lambda_handler               = "etl.lambda_function.lambda_handler"
  lambda_zip_file              = "../etl.zip"
  vpc_id                       = module.vpc.vpc_id
  subnet_ids                   = module.vpc.private_subnet_ids
  db_credential_secret_arn     = module.postgres.db_credential_secret_arn
  db_credential_secret_key_arn = module.postgres.kms_key_arn
  db_security_group_id         = module.postgres.db_security_group_id
  db_port                      = module.postgres.db_instance_port
  db_endpoint                  = module.postgres.db_instance_endpoint
  db_name                      = "restaurants"

  depends_on = [module.postgres, module.api_gateway_account]
}

