@echo off
REM ==============================================================================
REM AWS CLI Cloud Deployment Script (Windows Batch)
REM Assignment 19: Public Website with Restricted Admin Portal
REM Students: Vikas & Vijit | Cloud Computing Lab
REM ==============================================================================

set AWS_REGION=ap-south-1
set BUCKET_NAME=vikas-portal-storage-prod
set COLLEGE_IP=203.0.113.195/32

echo [*] Starting AWS Security Group and S3 Provisioning for Assignment 19...

REM 1. Create AWS Security Group
echo [*] Step 1: Creating Security Group...
aws ec2 create-security-group ^
    --group-name vikas-portal-sg ^
    --description "Assignment 19: Public Web + Restricted Admin and SSH" ^
    --region %AWS_REGION%

REM 2. Ingress Rule: Public Port 80 (HTTP) -> 0.0.0.0/0
echo [*] Step 2: Authorizing Public Port 80 (HTTP)...
aws ec2 authorize-security-group-ingress ^
    --group-name vikas-portal-sg ^
    --protocol tcp ^
    --port 80 ^
    --cidr 0.0.0.0/0 ^
    --region %AWS_REGION%

REM 3. Ingress Rule: Public Port 443 (HTTPS) -> 0.0.0.0/0
echo [*] Step 3: Authorizing Public Port 443 (HTTPS)...
aws ec2 authorize-security-group-ingress ^
    --group-name vikas-portal-sg ^
    --protocol tcp ^
    --port 443 ^
    --cidr 0.0.0.0/0 ^
    --region %AWS_REGION%

REM 4. Ingress Rule: Restricted SSH Port 22 -> College IP Only (203.0.113.195/32)
echo [*] Step 4: Authorizing Restricted SSH (Port 22) for College IP %COLLEGE_IP%...
aws ec2 authorize-security-group-ingress ^
    --group-name vikas-portal-sg ^
    --protocol tcp ^
    --port 22 ^
    --cidr %COLLEGE_IP% ^
    --region %AWS_REGION%

REM 5. Create S3 Object Storage Bucket
echo [*] Step 5: Creating S3 Object Storage Bucket: %BUCKET_NAME%...
aws s3api create-bucket ^
    --bucket %BUCKET_NAME% ^
    --region %AWS_REGION% ^
    --create-bucket-configuration LocationConstraint=%AWS_REGION%

REM 6. Enable S3 Bucket Encryption
echo [*] Step 6: Enabling AES-256 Server-Side Encryption...
aws s3api put-bucket-encryption ^
    --bucket %BUCKET_NAME% ^
    --server-side-encryption-configuration "{\"Rules\": [{\"ApplyServerSideEncryptionByDefault\": {\"SSEAlgorithm\": \"AES256\"}}]}"

echo [✓] AWS Cloud Resources Provisioned Successfully!
pause
