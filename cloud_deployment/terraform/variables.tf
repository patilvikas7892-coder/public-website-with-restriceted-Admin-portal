variable "aws_region" {
  description = "AWS Deployment Region"
  type        = "string"
  default     = "ap-south-1" # Mumbai Region
}

variable "environment" {
  description = "Deployment Environment"
  type        = "string"
  default     = "prod"
}

variable "college_admin_ip" {
  description = "Designated College Administration CIDR IP (Assignment 19: 203.XX.XX.XX/32)"
  type        = "string"
  default     = "203.0.113.195/32"
}

variable "instance_type" {
  description = "EC2 VM compute tier"
  type        = "string"
  default     = "t3.medium"
}
