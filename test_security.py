"""
Automated Security & Functionality Verification Suite
Assignment 19: Public Website with Restricted Admin Portal
Students: Vikas & Vijit | Cloud Computing Lab
"""

import unittest
import json
import io
import time
from app import app
from database import init_db, get_security_rules, get_recent_audit_logs
from storage_engine import storage
from security import is_ip_allowed_for_admin, is_ip_in_cidr

class TestSecurityGroupAndAdminPortal(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()

    # -------------------------------------------------------------------------
    # TEST SUITE 1: IP CIDR & ACCESS RESTRICTION LOGIC
    # -------------------------------------------------------------------------
    def test_01_college_ip_cidr_validation(self):
        """Verify that College IP 203.0.113.195 and College Subnet 203.0.113.0/24 pass."""
        allowed, matched = is_ip_allowed_for_admin("203.0.113.195")
        self.assertTrue(allowed, "College IP 203.0.113.195 should be authorized")

        allowed, matched = is_ip_allowed_for_admin("203.0.113.50")
        self.assertTrue(allowed, "Campus subnet 203.0.113.50 should be authorized")

        allowed, matched = is_ip_allowed_for_admin("127.0.0.1")
        self.assertTrue(allowed, "Localhost developer IP should be authorized")

    def test_02_unauthorized_external_ip_blocking(self):
        """Verify that external public internet IPs are blocked."""
        # Simulated external WAN intruder
        allowed, _ = is_ip_allowed_for_admin("198.51.100.45")
        self.assertFalse(allowed, "External public IP 198.51.100.45 must be blocked")

        # Simulated mobile ISP
        allowed, _ = is_ip_allowed_for_admin("49.37.112.89")
        self.assertFalse(allowed, "Mobile ISP IP 49.37.112.89 must be blocked")

        # Simulated cloud VM from another account
        allowed, _ = is_ip_allowed_for_admin("54.210.12.99")
        self.assertFalse(allowed, "External AWS IP 54.210.12.99 must be blocked")

    # -------------------------------------------------------------------------
    # TEST SUITE 2: PUBLIC WEBSITE (0.0.0.0/0 ACCESS)
    # -------------------------------------------------------------------------
    def test_03_public_homepage_accessible_to_world(self):
        """Verify that public homepage is 200 OK even from external untrusted IP."""
        response = self.client.get('/', headers={'X-Simulated-IP': '198.51.100.45'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Secure Enterprise Cloud Portal", response.data)
        self.assertIn(b"Assignment 19", response.data)

    def test_04_public_storage_assets_accessible(self):
        """Verify public can download static assets from S3 bucket without authentication."""
        response = self.client.get('/storage/public/campus_banner.svg', headers={'X-Simulated-IP': '49.37.112.89'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<svg", response.data)

    # -------------------------------------------------------------------------
    # TEST SUITE 3: RESTRICTED ADMIN PORTAL (HTTP 403 VS ALLOWED)
    # -------------------------------------------------------------------------
    def test_05_admin_portal_blocked_for_external_ip(self):
        """Verify accessing /admin from unauthorized IP yields HTTP 403 Forbidden with security screen."""
        response = self.client.get('/admin', headers={'X-Simulated-IP': '198.51.100.45'})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"403 Forbidden: Restricted Administration Portal", response.data)
        self.assertIn(b"SECURITY GROUP INGRESS BLOCKED", response.data)
        self.assertIn(b"198.51.100.45", response.data)

    def test_06_admin_portal_allowed_for_college_ip(self):
        """Verify accessing /admin from College IP (203.0.113.195) is allowed (redirects to login)."""
        response = self.client.get('/admin', headers={'X-Simulated-IP': '203.0.113.195'})
        # Should redirect to /admin/login because session is not yet authenticated, but NOT 403!
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])

    def test_07_admin_login_success_from_college_ip(self):
        """Verify administrator can log in when connecting from authorized College IP."""
        with self.client as c:
            # First set session IP to College IP
            c.post('/api/simulate-ip', json={'ip': '203.0.113.195'})
            login_resp = c.post('/admin/login', data={
                'username': 'vikas',
                'password': 'AdminPassword123!'
            }, follow_redirects=True)
            self.assertEqual(login_resp.status_code, 200)
            self.assertIn(b"Cloud Virtual Machine Telemetry", login_resp.data)
            self.assertIn(b"Vikas", login_resp.data)

    # -------------------------------------------------------------------------
    # TEST SUITE 4: S3 OBJECT STORAGE & PRE-SIGNED URLS
    # -------------------------------------------------------------------------
    def test_08_upload_object_to_s3_storage(self):
        """Verify admin can upload files to S3 bucket with metadata tracking."""
        fake_file = (io.BytesIO(b"Cloud lab test file content for Assignment 19."), "test_document.txt")
        with self.client as c:
            c.post('/api/simulate-ip', json={'ip': '203.0.113.195'})
            # Log in
            c.post('/admin/login', data={'username': 'vikas', 'password': 'AdminPassword123!'})
            # Upload private document
            upload_resp = c.post('/admin/upload', data={
                'file': fake_file,
                'category': 'private'
            }, follow_redirects=True)
            self.assertEqual(upload_resp.status_code, 200)
            
            # Check objects list
            objects = storage.list_objects(category="private")
            filenames = [o["filename"] for o in objects]
            self.assertIn("test_document.txt", filenames)

    def test_09_presigned_url_valid_and_invalid(self):
        """Verify S3 Pre-signed URL generates valid temporary link and rejects tampering."""
        objects = storage.list_objects(category="private")
        self.assertTrue(len(objects) > 0)
        target_obj = objects[0]

        # Generate Pre-signed URL
        presigned = storage.generate_presigned_url(target_obj["id"], expires_in_seconds=600)
        self.assertIsNotNone(presigned)
        url = presigned["url"]

        # 1. Access using valid Pre-signed URL
        resp_valid = self.client.get(url)
        self.assertEqual(resp_valid.status_code, 200)

        # 2. Access with tampered signature token
        tampered_url = url.replace("token=", "token=tampered_hacker_")
        resp_tampered = self.client.get(tampered_url)
        self.assertEqual(resp_tampered.status_code, 403)

    # -------------------------------------------------------------------------
    # TEST SUITE 5: AUDIT LOGGING & FIREWALL INTEGRITY
    # -------------------------------------------------------------------------
    def test_10_security_audit_logs_recorded(self):
        """Verify that every security decision (200, 403) is immutably logged in database."""
        # Trigger an intentional 403 block
        self.client.get('/admin', headers={'X-Simulated-IP': '198.51.100.99'})
        
        logs = get_recent_audit_logs(limit=10)
        blocked_logs = [l for l in logs if l['client_ip'] == '198.51.100.99' and l['http_status'] == 403]
        self.assertTrue(len(blocked_logs) > 0, "Audit log should contain the 403 blocked event")
        self.assertEqual(blocked_logs[0]['decision'], "BLOCKED_IP_RESTRICTION")

if __name__ == '__main__':
    unittest.main()
