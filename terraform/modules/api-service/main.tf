data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_kms_key" "service" {
  description             = "KMS key for API service encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "api-services-kms-key"
  }
}

resource "aws_kms_alias" "service_key_alias" {
  name          = "alias/restaurant-service-key"
  target_key_id = aws_kms_key.service.id
}

resource "aws_secretsmanager_secret" "api_key" {
  name       = "${var.api_name}-key"
  kms_key_id = aws_kms_key.service.id

  tags = {
    Name = "${var.api_name}-key"
  }
}

resource "random_password" "api_key_password" {
  length           = 64
  special          = true
  override_special = "#$%&*()-_=+[]{}<>?"
}

resource "aws_secretsmanager_secret_version" "rds_credentials_version" {
  secret_id = aws_secretsmanager_secret.api_key.id
  secret_string = jsonencode({
    apiKey = random_password.api_key_password.result
  })
}

resource "aws_lambda_function" "lambda_function" {
  function_name    = var.api_name
  description      = "backend for ${var.api_name} api gateway"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  filename         = var.lambda_zip_file
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  source_code_hash = filebase64sha256(var.lambda_zip_file)

  environment {
    variables = {
      DATABASE_CREDENTIAL_SECRET_ID = var.db_credential_secret_arn
      API_KEY_SECRET_ID             = aws_secretsmanager_secret.api_key.id
      DATABASE_ENDPOINT             = var.db_endpoint
      DATABASE_NAME                 = var.db_name
    }
  }

  vpc_config {
    security_group_ids = [aws_security_group.lambda_sg.id]
    subnet_ids         = var.subnet_ids
  }

  tags = {
    Name = var.api_name
  }
}

resource "aws_security_group" "lambda_sg" {
  name        = "${var.api_name}-lambda-sg"
  description = "Lambda security group"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.api_name}-lambda-sg"
  }
}

resource "aws_security_group_rule" "lambda_to_db_ingress" {
  type                     = "ingress"
  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  security_group_id        = var.db_security_group_id
  source_security_group_id = aws_security_group.lambda_sg.id
}

resource "aws_security_group_rule" "lambda_to_db_egress" {
  type                     = "egress"
  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  security_group_id        = aws_security_group.lambda_sg.id
  source_security_group_id = var.db_security_group_id
}

resource "aws_security_group_rule" "lambda_to_all_443" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  security_group_id = aws_security_group.lambda_sg.id
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.api_name}-lambdda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.api_name}-lambda-role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_policy" "lambda_secrets_access_policy" {
  name        = "LambdaSecretsAccessPolicy"
  description = "Policy to allow Lambda to read secrets"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = [aws_secretsmanager_secret.api_key.arn, var.db_credential_secret_arn]
      },
      {
        Effect   = "Allow",
        Action   = ["kms:Decrypt"],
        Resource = [aws_kms_key.service.arn, var.db_credential_secret_key_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_secrets_access_policy.arn
}

resource "aws_api_gateway_rest_api" "api" {
  name        = var.api_name
  description = "API gateway for restaurant recommendation service"
}

resource "aws_api_gateway_resource" "recommend_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "recommend"
}

resource "aws_api_gateway_resource" "restaurant_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "restaurant"
}

resource "aws_api_gateway_resource" "delete_restaurant_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "deleteRestaurant"
}

resource "aws_api_gateway_method" "recommend_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.recommend_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "restaurant_method_post" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.restaurant_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "restaurant_method_put" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.restaurant_resource.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "restaurant_method_delete" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.delete_restaurant_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "recommend_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.recommend_resource.id
  http_method             = aws_api_gateway_method.recommend_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_integration" "restaurant_integration_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.restaurant_resource.id
  http_method             = aws_api_gateway_method.restaurant_method_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_integration" "restaurant_integration_put" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.restaurant_resource.id
  http_method             = aws_api_gateway_method.restaurant_method_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_integration" "restaurant_integration_delete" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.delete_restaurant_resource.id
  http_method             = aws_api_gateway_method.restaurant_method_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.recommend_resource.id,
      aws_api_gateway_resource.restaurant_resource.id,
      aws_api_gateway_resource.delete_restaurant_resource.id,
      aws_api_gateway_method.recommend_method.id,
      aws_api_gateway_method.restaurant_method_post.id,
      aws_api_gateway_method.restaurant_method_put.id,
      aws_api_gateway_method.restaurant_method_delete.id,
      aws_api_gateway_integration.recommend_integration.id,
      aws_api_gateway_integration.restaurant_integration_post.id,
      aws_api_gateway_integration.restaurant_integration_put.id,
      aws_api_gateway_integration.restaurant_integration_delete.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api" {
  deployment_id        = aws_api_gateway_deployment.api.id
  rest_api_id          = aws_api_gateway_rest_api.api.id
  stage_name           = var.api_stage_name
  xray_tracing_enabled = true
}

resource "aws_api_gateway_method_settings" "api_methods" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.api.id}/*"
}
