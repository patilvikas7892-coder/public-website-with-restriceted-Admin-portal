import os
import time
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, send_file, abort, g, make_response
)
from werkzeug.security import check_password_hash

from database import (
    init_db, get_db_connection, log_audit_event, get_recent_audit_logs,
    get_security_rules, toggle_rule_status, add_security_rule,
    get_all_announcements, add_announcement, delete_announcement
)
from security import (
    is_ip_allowed_for_admin, get_effective_client_ip, get_ip_tag,
    DEFAULT_ALLOWED_ADMIN_CIDRS, DEMO_IP_PRESETS
)
from storage_engine import storage

app = Flask(__name__)
app.secret_key = "cloud-security-secret-key-assignment-19-vikas-vijit"
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload

# Initialize database schema and pre-seeded records
init_db()

@app.before_request
def security_inspection_middleware():
    """
    Core Security Group / WAF & IP Filter Middleware.
    Enforces the Assignment 19 rules:
    - Public Access: 0.0.0.0/0 allowed for website content and static storage.
    - Admin Access: Strictly restricted to College IP (203.XX.XX.XX/32).
    """
    client_ip = get_effective_client_ip(request, session)
    ip_tag = get_ip_tag(client_ip)
    
    # Store in Flask global context
    g.client_ip = client_ip
    g.ip_tag = ip_tag
    g.demo_presets = DEMO_IP_PRESETS
    g.allowed_cidrs = DEFAULT_ALLOWED_ADMIN_CIDRS

    path = request.path

    # Check if the requested URI belongs to the restricted Administration Domain
    if path.startswith("/admin"):
        allowed, matched_cidr = is_ip_allowed_for_admin(client_ip)
        
        if not allowed:
            # Denied: Client IP is outside the College IP range
            log_audit_event(
                client_ip=client_ip,
                ip_tag=ip_tag,
                method=request.method,
                endpoint=path,
                http_status=403,
                decision="BLOCKED_IP_RESTRICTION",
                rule_triggered="SG-INBOUND-ADMIN-01: Deny All except College IP 203.0.113.195/32",
                user_agent=request.headers.get("User-Agent", "")
            )
            return render_template(
                "403_restricted.html",
                client_ip=client_ip,
                ip_tag=ip_tag,
                required_subnet="203.0.113.195/32 (College Network Only)",
                attempted_path=path,
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            ), 403
        
        # IP is allowed under College CIDR!
        # Check authentication for protected admin pages (except /admin/login and /admin/logout)
        if path not in ["/admin/login", "/admin/logout"] and not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=path))

# ----------------- PUBLIC WEBSITE ROUTES (0.0.0.0/0) -----------------

@app.route("/")
def index():
    """Public Homepage - Accessible by the entire World (0.0.0.0/0)"""
    client_ip = g.client_ip
    log_audit_event(
        client_ip=client_ip,
        ip_tag=g.ip_tag,
        method="GET",
        endpoint="/",
        http_status=200,
        decision="ALLOWED_PUBLIC",
        rule_triggered="SG-IN-02: 0.0.0.0/0 Public Ingress (Port 443)",
        user_agent=request.headers.get("User-Agent", "")
    )
    
    # Fetch public assets and campus announcements
    public_assets = storage.list_objects(category="public")
    announcements = get_all_announcements()
    bucket_stats = storage.get_bucket_stats()
    
    return render_template(
        "index.html",
        public_assets=public_assets,
        announcements=announcements,
        bucket_stats=bucket_stats
    )

@app.route("/about")
def about():
    """About & Academic Assignment Overview"""
    return render_template("about.html")

@app.route("/announcements")
def announcements():
    """Public Campus Announcements"""
    all_announcements = get_all_announcements()
    return render_template("announcements.html", announcements=all_announcements)

@app.route("/gallery")
def gallery():
    """Public Object Storage Static Assets Gallery"""
    public_assets = storage.list_objects(category="public")
    bucket_stats = storage.get_bucket_stats()
    return render_template("gallery.html", assets=public_assets, bucket_stats=bucket_stats)

@app.route("/storage/public/<filename>")
def serve_public_storage(filename):
    """
    Public static file serving endpoint from the S3 Object Storage Bucket.
    Mimics AWS CloudFront / Direct S3 Public Bucket Read.
    """
    physical_path = os.path.join(storage.public_path, filename)
    if os.path.exists(physical_path):
        return send_file(physical_path)
    abort(404, description="Public Object not found in storage bucket.")

@app.route("/storage/secure-download/<file_id>")
def serve_secure_download(file_id):
    """
    Pre-Signed URL temporary download endpoint for private admin files.
    Validates token and timestamp expiration.
    """
    token = request.args.get("token")
    expires = request.args.get("expires")
    
    if not token or not expires:
        abort(403, description="Access Denied: Missing Pre-Signed Signature")
    
    valid, message = storage.verify_presigned_token(file_id, token, expires)
    if not valid:
        abort(403, description=f"Access Denied: {message}")
    
    obj = storage.get_object(file_id)
    if not obj:
        abort(404, description="Object not found")
        
    physical_path = storage.get_physical_path(obj)
    if not os.path.exists(physical_path):
        abort(404, description="Storage binary missing")
        
    log_audit_event(
        client_ip=g.client_ip,
        ip_tag=g.ip_tag,
        method="GET",
        endpoint=f"/storage/secure-download/{file_id}",
        http_status=200,
        decision="ALLOWED_PRESIGNED",
        rule_triggered="S3-PRESIGNED-SIGNATURE-VERIFIED",
        user_agent=request.headers.get("User-Agent", "")
    )
    return send_file(physical_path, as_attachment=True, download_name=obj["filename"])

# ----------------- SIMULATION & TESTING APIs -----------------

@app.route("/api/simulate-ip", methods=["POST"])
def simulate_ip():
    """Set active simulated client IP for real-time live demonstration."""
    data = request.get_json(silent=True) or request.form
    target_ip = data.get("ip", "").strip()
    if target_ip:
        session["simulated_ip"] = target_ip
        return jsonify({"success": True, "simulated_ip": target_ip, "ip_tag": get_ip_tag(target_ip)})
    return jsonify({"success": False, "error": "Invalid IP address"}), 400

@app.route("/api/reset-ip", methods=["POST"])
def reset_ip():
    """Reset IP simulation back to the natural socket address."""
    session.pop("simulated_ip", None)
    return jsonify({"success": True, "reset": True})

# ----------------- RESTRICTED ADMIN PORTAL ROUTES -----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """
    Admin Portal Login.
    Already protected by IP Whitelisting (College IP 203.0.113.195/32).
    """
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin_users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["admin_logged_in"] = True
            session["admin_username"] = user["username"]
            session["admin_role"] = user["role"]
            session["admin_name"] = user["full_name"]
            
            log_audit_event(
                client_ip=g.client_ip,
                ip_tag=g.ip_tag,
                method="POST",
                endpoint="/admin/login",
                http_status=200,
                decision="ALLOWED_COLLEGE_IP",
                rule_triggered="ADMIN_AUTH_SUCCESS: Login verified from College Subnet",
                user_agent=request.headers.get("User-Agent", "")
            )
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid administrator username or password credentials."
            log_audit_event(
                client_ip=g.client_ip,
                ip_tag=g.ip_tag,
                method="POST",
                endpoint="/admin/login",
                http_status=401,
                decision="AUTH_FAILURE",
                rule_triggered="ADMIN_AUTH_FAILED: Invalid Credentials",
                user_agent=request.headers.get("User-Agent", "")
            )

    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    session.pop("admin_role", None)
    session.pop("admin_name", None)
    return redirect(url_for("index"))

@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():
    """Main Administrator Console Dashboard."""
    bucket_stats = storage.get_bucket_stats()
    all_objects = storage.list_objects()
    security_rules = get_security_rules()
    recent_logs = get_recent_audit_logs(limit=10)
    announcements_count = len(get_all_announcements())

    # Simulated VM metrics for assignment cloud dashboard
    vm_metrics = {
        "instance_id": "i-09df13a298c4b195",
        "instance_type": "t3.medium (2 vCPU, 4GB RAM)",
        "cloud_provider": "AWS EC2 Linux (Ubuntu 24.04 LTS)",
        "public_ip": "13.234.180.92",
        "private_ip": "172.31.24.110",
        "region": "ap-south-1 (Mumbai)",
        "vpc_id": "vpc-07b140921ec5",
        "security_group_id": "sg-091a19f9b418",
        "cpu_utilization": "14.2%",
        "memory_used": "1.2 GB / 4.0 GB (30%)",
        "uptime": "14 days, 6 hours, 22 mins",
        "status": "Running (Healthy)"
    }

    return render_template(
        "admin_dashboard.html",
        vm_metrics=vm_metrics,
        bucket_stats=bucket_stats,
        objects=all_objects,
        security_rules=security_rules,
        recent_logs=recent_logs,
        announcements_count=announcements_count
    )

@app.route("/admin/storage")
def admin_storage():
    """Object Storage Asset Management Console."""
    category_filter = request.args.get("category")
    objects = storage.list_objects(category=category_filter)
    bucket_stats = storage.get_bucket_stats()
    return render_template("admin_storage.html", objects=objects, bucket_stats=bucket_stats, active_cat=category_filter)

@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    """Upload asset into Object Storage Bucket."""
    if "file" not in request.files:
        return redirect(url_for("admin_storage"))
    file = request.files["file"]
    if file.filename == "":
        return redirect(url_for("admin_storage"))
    
    category = request.form.get("category", "public")
    obj_meta = storage.upload_file(file, category=category, uploaded_by=f"admin_{session.get('admin_username', 'vikas')}")
    
    log_audit_event(
        client_ip=g.client_ip,
        ip_tag=g.ip_tag,
        method="POST",
        endpoint="/admin/upload",
        http_status=201,
        decision="ALLOWED_COLLEGE_IP",
        rule_triggered=f"S3_PUT_OBJECT: Stored in {obj_meta['key']} (ACL: {obj_meta['acl']})",
        user_agent=request.headers.get("User-Agent", "")
    )
    return redirect(url_for("admin_storage"))

@app.route("/admin/delete-file/<file_id>", methods=["POST"])
def admin_delete_file(file_id):
    """Delete an asset from the Object Storage Bucket."""
    obj = storage.get_object(file_id)
    if obj:
        key_name = obj.get("key")
        storage.delete_object(file_id)
        log_audit_event(
            client_ip=g.client_ip,
            ip_tag=g.ip_tag,
            method="POST",
            endpoint=f"/admin/delete-file/{file_id}",
            http_status=200,
            decision="ALLOWED_COLLEGE_IP",
            rule_triggered=f"S3_DELETE_OBJECT: Removed {key_name}",
            user_agent=request.headers.get("User-Agent", "")
        )
    return redirect(url_for("admin_storage"))

@app.route("/admin/generate-presigned/<file_id>")
def admin_generate_presigned(file_id):
    """API to generate pre-signed URL."""
    presigned = storage.generate_presigned_url(file_id, expires_in_seconds=900)
    if presigned:
        return jsonify({"success": True, "data": presigned})
    return jsonify({"success": False, "error": "Object not found"}), 404

@app.route("/admin/security-groups")
def admin_security_groups():
    """Security Group and Firewall Rules Management."""
    rules = get_security_rules()
    return render_template("admin_security.html", rules=rules)

@app.route("/admin/toggle-rule/<rule_id>", methods=["POST"])
def admin_toggle_rule(rule_id):
    toggle_rule_status(rule_id)
    log_audit_event(
        client_ip=g.client_ip,
        ip_tag=g.ip_tag,
        method="POST",
        endpoint=f"/admin/toggle-rule/{rule_id}",
        http_status=200,
        decision="ALLOWED_COLLEGE_IP",
        rule_triggered=f"SG_MODIFY_RULE: Toggled status of rule {rule_id}",
        user_agent=request.headers.get("User-Agent", "")
    )
    return redirect(url_for("admin_security_groups"))

@app.route("/admin/add-rule", methods=["POST"])
def admin_add_rule():
    rule_id = request.form.get("rule_id", f"SG-CUSTOM-{int(time.time() % 1000)}")
    direction = request.form.get("direction", "INBOUND")
    protocol = request.form.get("protocol", "TCP")
    port_range = request.form.get("port_range", "8080")
    source_cidr = request.form.get("source_cidr", "203.0.113.195/32")
    purpose = request.form.get("purpose", "Custom Security Rule")
    scope = request.form.get("scope", "Restricted Admin")

    add_security_rule(rule_id, direction, protocol, port_range, source_cidr, purpose, scope)
    log_audit_event(
        client_ip=g.client_ip,
        ip_tag=g.ip_tag,
        method="POST",
        endpoint="/admin/add-rule",
        http_status=201,
        decision="ALLOWED_COLLEGE_IP",
        rule_triggered=f"SG_AUTHORIZE_INGRESS: Added {rule_id} for {source_cidr}",
        user_agent=request.headers.get("User-Agent", "")
    )
    return redirect(url_for("admin_security_groups"))

@app.route("/admin/audit-logs")
def admin_audit_logs():
    """Full Access and Security Audit Trail."""
    logs = get_recent_audit_logs(limit=100)
    return render_template("admin_audit.html", logs=logs)

@app.route("/admin/announcements", methods=["GET", "POST"])
def admin_announcements():
    """Manage Public Announcements."""
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category", "General")
        badge = request.form.get("badge", "News")
        summary = request.form.get("summary")
        content = request.form.get("content")
        author = session.get("admin_name", "Vikas (Admin)")

        if title and summary and content:
            add_announcement(title, category, summary, content, badge, author)
            return redirect(url_for("admin_announcements"))

    all_announcements = get_all_announcements()
    return render_template("admin_announcements.html", announcements=all_announcements)

@app.route("/admin/delete-announcement/<int:item_id>", methods=["POST"])
def admin_delete_announcement(item_id):
    delete_announcement(item_id)
    return redirect(url_for("admin_announcements"))

if __name__ == "__main__":
    print("==================================================================")
    print("Assignment 19: Public Website with Restricted Admin Portal")
    print("Students: Vikas & Vijit | Domain: Web Hosting & Cloud Security")
    print("Security Architecture:")
    print(" - Public Content: Accessible from anywhere (0.0.0.0/0)")
    print(" - Restricted Admin: College IP Only (203.0.113.195/32, 127.0.0.1/32)")
    print(" - Object Storage: AWS S3 Bucket (vikas-portal-storage)")
    print("Server running on: http://127.0.0.1:5000")
    print("==================================================================")
    app.run(host="0.0.0.0", port=5000, debug=False)
