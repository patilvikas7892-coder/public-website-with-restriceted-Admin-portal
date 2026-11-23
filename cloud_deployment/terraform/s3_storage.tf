# ==============================================================================
# AWS S3 Object Storage Architecture (Assignment 19)
# Bucket: vikas-portal-storage
# Prefixes: public-assets/ (0.0.0.0/0) & admin-docs/ (Restricted Admin)
# ==============================================================================

resource "aws_s3_bucket" "portal_bucket" {
  bucket        = "vikas-portal-storage-${var.environment}"
  force_destroy = false

  tags = {
    Name        = "vikas-portal-storage"
    Assignment  = "19"
    Domain      = "Web Hosting"
    Lead        = "Vikas"
  }
}

# 1. Enable Bucket Object Versioning
resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.portal_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 2. Server-Side Encryption at Rest (SSE-S3 AES-256)
resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.portal_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 3. S3 Bucket Policy: Public Read on public-assets/ and Deny All on admin-docs/
resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.portal_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowPublicReadForPublicAssets"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = "${aws_s3_bucket.portal_bucket.arn}/public-assets/*"
      },
      {
        Sid       = "DenyExternalAccessToAdminDocs"
        Effect    = "Deny"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = "${aws_s3_bucket.portal_bucket.arn}/admin-docs/*"
        Condition = {
          NotIpAddress = {
            "aws:SourceIp" = [var.college_admin_ip]
          }
        }
      }
    ]
  })
}

# 4. IAM Role for Cloud Linux VM (EC2) to Access S3
resource "aws_iam_role" "ec2_s3_role" {
  name = "vikas-portal-ec2-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_access_policy" {
  name = "vikas-portal-s3-policy"
  role = aws_iam_role.ec2_s3_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.portal_bucket.arn,
          "${aws_s3_bucket.portal_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "vikas-portal-instance-profile"
  role = aws_iam_role.ec2_s3_role.name
}
