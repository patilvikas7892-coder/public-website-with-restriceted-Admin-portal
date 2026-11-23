# ==============================================================================
# AWS Security Group Configuration (Assignment 19)
# Public Access: 0.0.0.0/0 (Website Content Only)
# Admin Access: College IP Only (203.0.113.195/32)
# ==============================================================================

resource "aws_security_group" "web_and_admin_firewall" {
  name        = "vikas-portal-security-group"
  description = "Assignment 19: Public HTTP/HTTPS and Restricted Admin/SSH"
  vpc_id      = aws_vpc.portal_vpc.id

  # --------------------------------------------------------------------------
  # 1. PUBLIC INGRESS RULES (0.0.0.0/0)
  # --------------------------------------------------------------------------
  
  # Port 80 (HTTP) -> Nginx automatically performs 301 Permanent Redirect to HTTPS 443
  ingress {
    description = "Public HTTP Traffic (Redirects to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 443 (HTTPS) -> Public Website & S3 Hosted Static Assets
  ingress {
    description = "Public Secure HTTPS Web Traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # --------------------------------------------------------------------------
  # 2. RESTRICTED ADMIN INGRESS RULES (College IP Only: 203.0.113.195/32)
  # --------------------------------------------------------------------------

  # Port 22 (SSH) -> Strictly isolated to Administrator / College IP
  ingress {
    description = "Restricted Administrator SSH Terminal Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.college_admin_ip] # e.g. "203.0.113.195/32"
  }

  # Optional Port 8443 / Admin Direct Socket (if isolated port is used)
  ingress {
    description = "Restricted Admin Management Port (College Subnet)"
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = [var.college_admin_ip]
  }

  # --------------------------------------------------------------------------
  # 3. OUTBOUND EGRESS RULES
  # --------------------------------------------------------------------------
  
  # Outbound Internet Access for Package Updates, S3 API endpoints, DNS
  egress {
    description = "Full Outbound Egress to Internet Gateway"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "vikas-portal-sg"
    Author      = "Vikas & Vijit"
    Assignment  = "19"
  }
}
