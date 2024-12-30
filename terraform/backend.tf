terraform {
  backend "s3" {
    bucket         = "restaurant-terraform-state-bucket"
    key            = "state/restaurant-service/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}