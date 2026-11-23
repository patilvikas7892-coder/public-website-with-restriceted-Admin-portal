import os
import hashlib
import json
import time
import uuid
import mimetypes
from werkzeug.utils import secure_filename

BASE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s3_bucket")
BUCKET_NAME = "vikas-portal-storage"
BUCKET_DIR = os.path.join(BASE_STORAGE_DIR, BUCKET_NAME)
PUBLIC_PREFIX = "public-assets"
ADMIN_PREFIX = "admin-docs"
METADATA_FILE = os.path.join(BUCKET_DIR, "bucket_metadata.json")

class CloudObjectStorage:
    def __init__(self, bucket_name=BUCKET_NAME):
        self.bucket_name = bucket_name
        self.bucket_path = os.path.join(BASE_STORAGE_DIR, bucket_name)
        self.public_path = os.path.join(self.bucket_path, PUBLIC_PREFIX)
        self.admin_path = os.path.join(self.bucket_path, ADMIN_PREFIX)
        self.metadata_file = os.path.join(self.bucket_path, "bucket_metadata.json")
        self._ensure_storage_structure()
        self._seed_default_assets()

    def _ensure_storage_structure(self):
        os.makedirs(self.public_path, exist_ok=True)
        os.makedirs(self.admin_path, exist_ok=True)
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump({"bucket": self.bucket_name, "created_at": time.time(), "objects": {}}, f, indent=2)

    def _load_metadata(self):
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"bucket": self.bucket_name, "created_at": time.time(), "objects": {}}

    def _save_metadata(self, data):
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _calculate_etag(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def upload_file(self, file_obj, category="public", uploaded_by="admin_vikas"):
        """
        Uploads a file object into the S3 Object Storage bucket.
        category: 'public' -> stored under public-assets/ with ACL 'public-read'
                  'private' -> stored under admin-docs/ with ACL 'private'
        """
        filename = secure_filename(file_obj.filename)
        if not filename:
            filename = f"file_{int(time.time())}.bin"
        
        file_id = str(uuid.uuid4())[:8]
        prefix = PUBLIC_PREFIX if category == "public" else ADMIN_PREFIX
        unique_name = f"{file_id}_{filename}"
        target_dir = self.public_path if category == "public" else self.admin_path
        target_path = os.path.join(target_dir, unique_name)
        
        file_obj.save(target_path)
        size = os.path.getsize(target_path)
        etag = self._calculate_etag(target_path)
        mime_type, _ = mimetypes.guess_type(target_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        key = f"{prefix}/{unique_name}"
        obj_meta = {
            "id": file_id,
            "key": key,
            "filename": filename,
            "stored_filename": unique_name,
            "prefix": prefix,
            "category": category,
            "size_bytes": size,
            "size_formatted": self._format_size(size),
            "content_type": mime_type,
            "acl": "public-read" if category == "public" else "private",
            "etag": f'"{etag}"',
            "version_id": f"v1.{int(time.time() % 10000)}",
            "uploaded_by": uploaded_by,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "is_public": (category == "public")
        }

        metadata = self._load_metadata()
        metadata["objects"][file_id] = obj_meta
        self._save_metadata(metadata)
        return obj_meta

    def list_objects(self, category=None):
        """Returns list of objects stored in bucket, optionally filtered by category."""
        metadata = self._load_metadata()
        objects = list(metadata.get("objects", {}).values())
        if category:
            objects = [obj for obj in objects if obj.get("category") == category]
        # Sort by uploaded_at descending
        objects.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        return objects

    def get_object(self, file_id):
        metadata = self._load_metadata()
        return metadata.get("objects", {}).get(file_id)

    def get_physical_path(self, obj_meta):
        if obj_meta["category"] == "public":
            return os.path.join(self.public_path, obj_meta["stored_filename"])
        return os.path.join(self.admin_path, obj_meta["stored_filename"])

    def delete_object(self, file_id):
        metadata = self._load_metadata()
        if file_id in metadata.get("objects", {}):
            obj = metadata["objects"][file_id]
            physical_path = self.get_physical_path(obj)
            if os.path.exists(physical_path):
                os.remove(physical_path)
            del metadata["objects"][file_id]
            self._save_metadata(metadata)
            return True
        return False

    def generate_presigned_url(self, file_id, expires_in_seconds=900):
        """Generates a simulated S3 Pre-Signed URL for secure temporary download."""
        obj = self.get_object(file_id)
        if not obj:
            return None
        expires_at = int(time.time()) + expires_in_seconds
        token_src = f"{file_id}_{expires_at}_s3_secret_key"
        token = hashlib.sha256(token_src.encode("utf-8")).hexdigest()[:16]
        url = f"/storage/secure-download/{file_id}?token={token}&expires={expires_at}"
        return {
            "url": url,
            "expires_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expires_at)),
            "expires_in_minutes": int(expires_in_seconds / 60)
        }

    def verify_presigned_token(self, file_id, token, expires_str):
        try:
            expires_at = int(expires_str)
            if time.time() > expires_at:
                return False, "Pre-signed URL has expired"
            expected_src = f"{file_id}_{expires_at}_s3_secret_key"
            expected_token = hashlib.sha256(expected_src.encode("utf-8")).hexdigest()[:16]
            if token == expected_token:
                return True, "Valid"
            return False, "Invalid signature token"
        except Exception as e:
            return False, str(e)

    def get_bucket_stats(self):
        objects = self.list_objects()
        total_size = sum(o.get("size_bytes", 0) for o in objects)
        public_count = sum(1 for o in objects if o.get("category") == "public")
        private_count = sum(1 for o in objects if o.get("category") == "private")
        return {
            "bucket_name": self.bucket_name,
            "region": "ap-south-1 (AWS Mumbai)",
            "total_objects": len(objects),
            "public_objects": public_count,
            "private_objects": private_count,
            "total_size_bytes": total_size,
            "total_size_formatted": self._format_size(total_size),
            "storage_class": "STANDARD (Object Storage)",
            "versioning": "Enabled",
            "encryption": "AES-256 (SSE-S3)"
        }

    def _format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def _seed_default_assets(self):
        """Seed sample public static files and private admin files if empty."""
        metadata = self._load_metadata()
        if metadata.get("objects"):
            return

        # 1. Create a Public Campus Banner SVG
        banner_content = '''<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e3a8a" />
      <stop offset="100%" stop-color="#3b82f6" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)" />
  <circle cx="700" cy="80" r="120" fill="rgba(255,255,255,0.08)" />
  <circle cx="100" cy="350" r="180" fill="rgba(255,255,255,0.06)" />
  <text x="400" y="180" font-family="'Segoe UI', Arial, sans-serif" font-size="34" font-weight="bold" fill="#ffffff" text-anchor="middle">National Institute of Cloud Computing</text>
  <text x="400" y="230" font-family="'Segoe UI', Arial, sans-serif" font-size="20" fill="#bfdbfe" text-anchor="middle">Autonomous Engineering Campus &bull; NAAC A++ Accredited</text>
  <rect x="260" y="270" width="280" height="45" rx="22" fill="#38bdf8" />
  <text x="400" y="299" font-family="'Segoe UI', Arial, sans-serif" font-size="16" font-weight="bold" fill="#0f172a" text-anchor="middle">S3 Object Storage Hosted Asset</text>
</svg>'''
        banner_path = os.path.join(self.public_path, "campus_banner.svg")
        with open(banner_path, "w", encoding="utf-8") as f:
            f.write(banner_content)
        
        # 2. Create Public Brochure text
        brochure_content = """NATIONAL INSTITUTE OF CLOUD COMPUTING & ENGINEERING
CAMPUS INFORMATION BROCHURE (ACADEMIC YEAR 2026-2027)

Domain: Web Hosting & Secure Cloud Architectures
Student Assignment 19: Public Website with Restricted Admin Portal
Architect: Vikas & Vijit

Highlights:
- High performance Cloud VM Infrastructure (AWS EC2 / Ubuntu Linux)
- High availability Object Storage (AWS S3 Bucket: vikas-portal-storage)
- Military-Grade Network Security Groups & IP Filtering
- Public Access (0.0.0.0/0) for Homepage and Static Assets
- Strict Admin Subnet Restriction (203.0.113.195/32 - College Only)
"""
        brochure_path = os.path.join(self.public_path, "campus_brochure_2026.txt")
        with open(brochure_path, "w", encoding="utf-8") as f:
            f.write(brochure_content)

        # 3. Create Private Admin Confidential Security Audit Report
        admin_doc_content = """CONFIDENTIAL CLOUD SECURITY AUDIT REPORT
Target: AWS EC2 Instance (i-08a9f23e41b) & S3 Storage (s3://vikas-portal-storage)
Prepared by: Vikas (Cloud Security Engineer)
Status: STRICT ACCESS ONLY (College Subnet CIDR 203.0.113.195/32)

Firewall Rules Summary:
- Port 80 (HTTP): Open to 0.0.0.0/0 (301 Redirect to HTTPS 443)
- Port 443 (HTTPS): Open to 0.0.0.0/0 (Public Website)
- Port 22 (SSH): Restricted to 203.0.113.195/32 (Admin Station)
- URI /admin: Protected by Security Group & Application IP Filter Middleware
"""
        admin_doc_path = os.path.join(self.admin_path, "confidential_security_audit.txt")
        with open(admin_doc_path, "w", encoding="utf-8") as f:
            f.write(admin_doc_content)

        # Register metadata
        objects = {
            "pub001": {
                "id": "pub001",
                "key": f"{PUBLIC_PREFIX}/campus_banner.svg",
                "filename": "campus_banner.svg",
                "stored_filename": "campus_banner.svg",
                "prefix": PUBLIC_PREFIX,
                "category": "public",
                "size_bytes": len(banner_content),
                "size_formatted": self._format_size(len(banner_content)),
                "content_type": "image/svg+xml",
                "acl": "public-read",
                "etag": f'"{hashlib.md5(banner_content.encode("utf-8")).hexdigest()}"',
                "version_id": "v1.0.1",
                "uploaded_by": "vikas (admin)",
                "uploaded_at": "2026-11-20 10:00:00 UTC",
                "is_public": True
            },
            "pub002": {
                "id": "pub002",
                "key": f"{PUBLIC_PREFIX}/campus_brochure_2026.txt",
                "filename": "campus_brochure_2026.txt",
                "stored_filename": "campus_brochure_2026.txt",
                "prefix": PUBLIC_PREFIX,
                "category": "public",
                "size_bytes": len(brochure_content),
                "size_formatted": self._format_size(len(brochure_content)),
                "content_type": "text/plain",
                "acl": "public-read",
                "etag": f'"{hashlib.md5(brochure_content.encode("utf-8")).hexdigest()}"',
                "version_id": "v1.0.1",
                "uploaded_by": "vikas (admin)",
                "uploaded_at": "2026-11-21 14:30:00 UTC",
                "is_public": True
            },
            "priv001": {
                "id": "priv001",
                "key": f"{ADMIN_PREFIX}/confidential_security_audit.txt",
                "filename": "confidential_security_audit.txt",
                "stored_filename": "confidential_security_audit.txt",
                "prefix": ADMIN_PREFIX,
                "category": "private",
                "size_bytes": len(admin_doc_content),
                "size_formatted": self._format_size(len(admin_doc_content)),
                "content_type": "text/plain",
                "acl": "private",
                "etag": f'"{hashlib.md5(admin_doc_content.encode("utf-8")).hexdigest()}"',
                "version_id": "v1.0.0",
                "uploaded_by": "vikas (admin)",
                "uploaded_at": "2026-11-22 09:15:00 UTC",
                "is_public": False
            }
        }
        self._save_metadata({"bucket": self.bucket_name, "created_at": time.time(), "objects": objects})

# Global storage instance
storage = CloudObjectStorage()
