cidr_block           = "10.16.0.0/21"
private_subnet_cidrs = ["10.16.0.0/24", "10.16.1.0/24"]
public_subnet_cidrs  = ["10.16.2.0/24", "10.16.3.0/24"]
availability_zones   = ["us-east-1a", "us-east-1b"]
postgres_instance_class    = "db.m6i.large"
postgres_allocated_storage = 30
api_stage_name = "prod"
