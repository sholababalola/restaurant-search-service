cidr_block                 = "10.16.8.0/21"
private_subnet_cidrs       = ["10.16.8.0/24", "10.16.9.0/24"]
public_subnet_cidrs        = ["10.16.10.0/24", "10.16.11.0/24"]
availability_zones         = ["us-east-1a", "us-east-1b"]
postgres_instance_class    = "db.t3.micro"
postgres_allocated_storage = 10
api_stage_name = "dev"
