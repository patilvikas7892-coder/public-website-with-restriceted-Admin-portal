#!/usr/bin/env bash
# ==============================================================================
# AWS CLI Cloud Deployment Script (Bash / Linux EC2)
# Assignment 19: Public Website with Restricted Admin Portal
# Students: Vikas & Vijit | Cloud Computing Lab
# ==============================================================================

set -euo pipefail

AWS_REGION="ap-south-1"
BUCKET_NAME="vikas-portal-storage-prod"
COLLEGE_IP="203.0.113.195/32"

echo "[*] Step 1: Creating Security Group in region $AWS_REGION..."
SG_ID=$(aws ec2 create-security-group \
    --group-name "vikas-portal-sg" \
    --description "Assignment 19: Public Web + Restricted Admin and SSH" \
    --region "$AWS_REGION" \
    --output text --query 'GroupId')

echo "[+] Security Group Created: $SG_ID"

echo "[*] Step 2: Authorizing Public Ingress Port 80 (HTTP) -> 0.0.0.0/0..."
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"

echo "[*] Step 3: Authorizing Public Ingress Port 443 (HTTPS) -> 0.0.0.0/0..."
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 443 --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"

echo "[*] Step 4: Restricting SSH Port 22 to College IP ($COLLEGE_IP)..."
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 22 --cidr "$COLLEGE_IP" \
    --region "$AWS_REGION"

echo "[*] Step 5: Creating AWS S3 Bucket ($BUCKET_NAME)..."
aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"

echo "[*] Step 6: Enabling S3 Versioning & Server-Side Encryption..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

echo "[✓] Deployment completed successfully!"
