# Cloud Web Hosting with Restricted Admin Portal (Assignment 19)

**Student Engineers**: Vikas & Vijit  
**Course**: Cloud Computing & Virtualization Laboratory  
**Assignment No**: 19  
**Application Domain**: Web Hosting & Cloud Security  
**Cloud Components**: Cloud Linux VM + AWS S3 Object Storage + Security Groups & IP Whitelisting  

---

## 🚀 Quick Start Guide

### Option 1: One-Click Local Launch
Double-click [`run.bat`](file:///C:/Users/patil/.gemini/antigravity/scratch/public-website-restricted-admin/run.bat):
```cmd
run.bat
```
- Local URL: **[http://localhost:5000](http://localhost:5000)**
- LAN / Campus Wi-Fi URL: **http://172.20.3.86:5000** (Any phone or laptop on the same Wi-Fi can open this!)

### Option 2: One-Click Start & Make Public to Internet
Double-click [`run_and_share_public.bat`](file:///C:/Users/patil/.gemini/antigravity/scratch/public-website-restricted-admin/run_and_share_public.bat):
```cmd
run_and_share_public.bat
```
This automatically starts `python app.py` and establishes an instant public HTTPS tunnel (e.g. `https://xxxxxx.a.pinggy.link`) so anyone worldwide can access it.

### Option 3: Separate Tunnel Tool
If your app is already running, double-click [`share_public.bat`](file:///C:/Users/patil/.gemini/antigravity/scratch/public-website-restricted-admin/share_public.bat) to choose between Pinggy, Cloudflare, or Localtunnel.

---

## 🔑 Login & Demonstration Credentials

- **Admin Username**: `vikas`
- **Admin Password**: `AdminPassword123!`
- **Authorized College IP**: `203.0.113.195` (Subnet: `203.0.113.0/24`)

---

## 🎯 How to Demonstrate to Faculty / Examiner

1. **Step 1: Test Public Website (0.0.0.0/0)**
   - Open [http://localhost:5000](http://localhost:5000).
   - Anyone from the public internet can view the homepage, announcements, and S3-hosted static graphics (`public-assets/campus_banner.svg`).

2. **Step 2: Demonstrate Blocked Admin Access (External IP Simulation)**
   - Look at the **Top Black Bar** (Security Simulator).
   - Click the red button: **`External WAN (198.51.100.45)`**.
   - Now click **`Restricted Admin Portal`** in the top navigation.
   - 🛑 **Observe the HTTP 403 Forbidden Firewall Barrier**: The page explains that the Security Group blocked the connection because `198.51.100.45` is not in the allowed College IP range (`203.0.113.195/32`).

3. **Step 3: Demonstrate Authorized Admin Access (College IP Simulation)**
   - In the top bar, click the green button: **`College IP (203.0.113.195)`**.
   - Navigate to `/admin`.
   - Access is immediately granted!
   - Log in with `vikas` / `AdminPassword123!`.

4. **Step 4: Explore Cloud Admin Console**
   - **Dashboard**: View live EC2 Linux VM telemetry, CPU load, memory, and uptime.
   - **S3 Object Storage**: Upload new files, choose between `public-read` (public assets) and `private` (confidential documents).
   - **Pre-Signed URLs**: Click the key icon on any private file to generate an expiring 15-minute temporary link.
   - **Security Groups**: View and toggle stateful inbound/outbound firewall rules (HTTP 80 redirect, HTTPS 443, Port 22 SSH).
   - **Audit Logs**: Inspect the real-time forensics access log recording all 200 OK and 403 Blocked attempts.

---

## 🧪 Automated Security Test Suite

Run the full automated test suite verifying all 13 security assertions:
```cmd
python test_security.py
```
Expected output:
```
Ran 10 tests in 0.743s
OK
```

---

## 📁 Project Structure

```
public-website-restricted-admin/
├── app.py                      # Core Flask web server & IP restriction middleware
├── security.py                 # CIDR validation engine & security presets
├── storage_engine.py           # AWS S3 Object Storage emulation & pre-signed URLs
├── database.py                 # SQLite database for announcements, rules & audit logs
├── test_security.py            # Automated security unit tests
├── requirements.txt            # Python dependencies
├── run.bat                     # One-click Windows launch script
├── PROJECT_REPORT.md           # 8-Page Comprehensive University Academic Report
├── templates/                  # Modern Jinja2 HTML templates
│   ├── base.html               # Main layout + interactive top IP simulation bar
│   ├── index.html              # Public homepage (0.0.0.0/0)
│   ├── about.html              # System architecture & cloud network topology
│   ├── announcements.html      # Public campus announcements
│   ├── gallery.html            # Public S3 static assets explorer
│   ├── 403_restricted.html     # AWS WAF / Security Group 403 barrier screen
│   ├── admin_login.html        # Admin login (College IP verified)
│   ├── admin_dashboard.html    # Cloud VM telemetry & administration console
│   ├── admin_storage.html      # S3 Object Storage manager (upload, ACL, pre-signed URLs)
│   ├── admin_security.html     # Security Groups & Firewall rule manager
│   ├── admin_audit.html        # Security forensics & audit stream
│   └── admin_announcements.html# Content management publisher
├── static/
│   ├── css/styles.css          # Sleek modern styling & responsive design
│   └── js/app.js               # Interactive IP switcher, pre-signed URL copier, modals
├── s3_bucket/                  # Local S3 Object Storage repository
│   └── vikas-portal-storage/
│       ├── public-assets/      # Open to 0.0.0.0/0 (SVGs, brochures)
│       ├── admin-docs/         # Restricted to College IP
│       └── bucket_metadata.json# S3 object metadata, ETags, and versioning
└── cloud_deployment/           # Production cloud configuration deliverables
    ├── terraform/              # Terraform IaC for VPC, EC2, S3, and Security Groups
    ├── nginx/                  # Nginx reverse proxy with TLS 1.3 & IP whitelisting
    ├── ssl/                    # X.509 TLS certificate generation & technical report
    └── aws_cli/                # Shell & Batch scripts for AWS CLI provisioning
```
