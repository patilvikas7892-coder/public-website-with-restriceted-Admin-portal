import sqlite3
import os
import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portal_data.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Admin Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Administrator',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Campus Announcements (Public Content)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        summary TEXT NOT NULL,
        content TEXT NOT NULL,
        badge TEXT NOT NULL DEFAULT 'General',
        published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        author TEXT NOT NULL DEFAULT 'Vikas (Admin)'
    )
    ''')

    # 3. Cloud Security Group / Firewall Rules Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_rules (
        id TEXT PRIMARY KEY,
        direction TEXT NOT NULL, -- INBOUND or OUTBOUND
        protocol TEXT NOT NULL,  -- TCP, UDP, ICMP
        port_range TEXT NOT NULL, -- 80, 443, 22
        source_cidr TEXT NOT NULL, -- 0.0.0.0/0, 203.0.113.195/32
        purpose TEXT NOT NULL,
        scope TEXT NOT NULL,     -- Public vs Restricted Admin
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 4. Security Audit & Access Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        client_ip TEXT NOT NULL,
        ip_tag TEXT NOT NULL,
        request_method TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        http_status INTEGER NOT NULL,
        decision TEXT NOT NULL, -- ALLOWED_PUBLIC, ALLOWED_COLLEGE_IP, BLOCKED_IP_RESTRICTION
        rule_triggered TEXT NOT NULL,
        user_agent TEXT
    )
    ''')

    conn.commit()

    # Pre-seed initial data
    _seed_data(cursor, conn)
    conn.close()

def _seed_data(cursor, conn):
    # Seed default Admin users (Vikas & Vijit)
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        pw_hash = generate_password_hash("AdminPassword123!")
        cursor.execute('''
            INSERT INTO admin_users (username, full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("vikas", "Vikas (Cloud Security Lead)", "vikas@cloudtech.edu", pw_hash, "SuperAdmin"))
        cursor.execute('''
            INSERT INTO admin_users (username, full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("vijit", "Vijit (Cloud Infrastructure Eng)", "vijit@cloudtech.edu", pw_hash, "Admin"))

    # Seed Announcements
    cursor.execute("SELECT COUNT(*) FROM announcements")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO announcements (title, category, summary, content, badge, author)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "Annual Cloud Computing & Cyber Defense Summit 2026",
            "Conferences",
            "Registrations are now open for the International Summit on Cloud Infrastructure and Security Architecture.",
            "Join key industry leaders from AWS, Google Cloud, and Azure as we explore Next-Gen Zero Trust Architecture, IP Whitelisting, and Object Storage Lakes.",
            "Important",
            "Vikas (Admin)"
        ))
        cursor.execute('''
            INSERT INTO announcements (title, category, summary, content, badge, author)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "Semester 6 Cloud Architecture Lab Assignments Published",
            "Academics",
            "All batches must review their assigned domains, VMs, and object storage requirements for practical evaluation.",
            "Assignment 19 requires students Vikas & Vijit to implement a Public Website with an IP-restricted Admin Portal using AWS Security Groups and S3 Storage.",
            "Academic",
            "Vijit & Vikas"
        ))
        cursor.execute('''
            INSERT INTO announcements (title, category, summary, content, badge, author)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "Campus Security Notice: Strict IP Filtering Active on Administrative Services",
            "Security Alert",
            "Administrative interfaces are isolated strictly behind College IP 203.0.113.195/32 to prevent external brute-force attacks.",
            "All faculty and administrators must connect via the dedicated campus leased line or authorized college subnet to reach administrative management panels.",
            "Security",
            "Vikas (Cloud Admin)"
        ))

    # Seed Security Group Rules (Assignment 19 Specification)
    cursor.execute("SELECT COUNT(*) FROM security_rules")
    if cursor.fetchone()[0] == 0:
        rules = [
            ("SG-IN-01", "INBOUND", "TCP", "80", "0.0.0.0/0", "HTTP Web Traffic (Auto redirects to HTTPS)", "Public", "ACTIVE"),
            ("SG-IN-02", "INBOUND", "TCP", "443", "0.0.0.0/0", "HTTPS Public Portal & Static Asset Access", "Public", "ACTIVE"),
            ("SG-IN-03", "INBOUND", "TCP", "22", "203.0.113.195/32", "SSH Bastion / Terminal (Restricted to Administrator IP)", "Restricted Admin", "ACTIVE"),
            ("SG-IN-04", "INBOUND", "TCP", "443 /admin", "203.0.113.195/32", "Admin Portal URI (College Network Subnet Only)", "Restricted Admin", "ACTIVE"),
            ("SG-IN-05", "INBOUND", "TCP", "443 /admin", "127.0.0.1/32", "Admin Portal URI (Localhost Loopback Dev)", "Restricted Admin", "ACTIVE"),
            ("SG-OUT-01", "OUTBOUND", "ALL", "ALL", "0.0.0.0/0", "Outbound Internet Gateway (OS Updates, S3 API, NTP)", "Public", "ACTIVE"),
            ("SG-OUT-02", "OUTBOUND", "TCP", "443", "s3.ap-south-1.amazonaws.com", "AWS S3 Object Storage API Endpoint Gateway", "Internal", "ACTIVE")
        ]
        cursor.executemany('''
            INSERT INTO security_rules (id, direction, protocol, port_range, source_cidr, purpose, scope, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', rules)

    conn.commit()

def log_audit_event(client_ip, ip_tag, method, endpoint, http_status=200, decision="ALLOWED", rule_triggered="", user_agent="", status_code=None):
    if status_code is not None:
        http_status = status_code
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO security_audit_logs (timestamp, client_ip, ip_tag, request_method, endpoint, http_status, decision, rule_triggered, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now_str, client_ip, ip_tag, method, endpoint, http_status, decision, rule_triggered, user_agent[:200]))
    conn.commit()
    conn.close()

def get_recent_audit_logs(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM security_audit_logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_security_rules():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM security_rules ORDER BY direction, id')
    rows = cursor.fetchall()
    conn.close()
    return rows

def toggle_rule_status(rule_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM security_rules WHERE id = ?', (rule_id,))
    row = cursor.fetchone()
    if row:
        new_status = 'DISABLED' if row['status'] == 'ACTIVE' else 'ACTIVE'
        cursor.execute('UPDATE security_rules SET status = ? WHERE id = ?', (new_status, rule_id))
        conn.commit()
    conn.close()

def add_security_rule(rule_id, direction, protocol, port_range, source_cidr, purpose, scope):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO security_rules (id, direction, protocol, port_range, source_cidr, purpose, scope, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
    ''', (rule_id, direction, protocol, port_range, source_cidr, purpose, scope))
    conn.commit()
    conn.close()

def get_all_announcements():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM announcements ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_announcement(title, category, summary, content, badge, author):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO announcements (title, category, summary, content, badge, author)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, category, summary, content, badge, author))
    conn.commit()
    conn.close()

def delete_announcement(announcement_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))
    conn.commit()
    conn.close()
