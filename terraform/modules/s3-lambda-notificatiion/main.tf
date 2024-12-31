resource "aws_kms_key" "service" {
  description             = "KMS key used to encrypt S3 data API"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "${var.service_name}"
  }
}

resource "aws_kms_alias" "service_key_alias" {
  name          = "alias/${var.service_name}-s3-notification"
  target_key_id = aws_kms_key.service.id
}

resource "aws_s3_bucket" "private_bucket" {
  bucket        = "${var.service_name}-notification-bucket"
  force_destroy = terraform.workspace != "prod"

  tags = {
    Name = var.service_name
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "private_bucket" {
  bucket = aws_s3_bucket.private_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.service.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_lambda_function" "lambda_function" {
  function_name    = var.service_name
  description      = "Lambda trigerred by ${var.service_name} S3 bucket"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_role.arn
  handler          = var.lambda_handler
  filename         = var.lambda_zip_file
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  source_code_hash = filebase64sha256(var.lambda_zip_file)

  environment {
    variables = {
      DATABASE_CREDENTIAL_SECRET_ID = var.db_credential_secret_arn
      DATABASE_ENDPOINT             = var.db_endpoint
      DATABASE_NAME                 = var.db_name
    }
  }

  vpc_config {
    security_group_ids = [aws_security_group.lambda_sg.id]
    subnet_ids         = var.subnet_ids
  }

  tags = {
    Name = var.service_name
  }
}

resource "aws_security_group" "lambda_sg" {
  name        = "${var.service_name}-lambda-sg"
  description = "${var.service_name} Lambda security group"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.service_name}-lambda-sg"
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
  name = "${var.service_name}-lambdda-role"

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
    Name = "${var.service_name}-lambda-role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_policy" "lambda_access_policy" {
  name        = "AccessPolicy"
  description = "Policy to allow Lambda to read secrets"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = [var.db_credential_secret_arn]
      },
      {
        Effect   = "Allow",
        Action   = ["kms:Encrypt", "kms:Generate*", "kms:Decrypt"],
        Resource = [aws_kms_key.service.arn, var.db_credential_secret_key_arn]
      },
      {
        Effect : "Allow",
        Action : ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        Resource : [
          "${aws_s3_bucket.private_bucket.arn}",
          "${aws_s3_bucket.private_bucket.arn}/*"
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_access_policy.arn
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.private_bucket.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.private_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "create/"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "update/"
  }

   lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "delete/"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}
