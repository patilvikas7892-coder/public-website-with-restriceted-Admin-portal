# ==============================================================================
# Terraform Cloud Infrastructure Deployment
# Assignment 19: Public Website with Restricted Admin Portal
# Students: Vikas & Vijit | Domain: Web Hosting & Cloud Security
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. AWS VPC & Subnet
resource "aws_vpc" "portal_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "vikas-portal-vpc"
    Assignment  = "19-Web-Hosting"
    Environment = "Production"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.portal_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "vikas-portal-public-subnet"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.portal_vpc.id

  tags = {
    Name = "vikas-portal-igw"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.portal_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "vikas-portal-public-route-table"
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}
