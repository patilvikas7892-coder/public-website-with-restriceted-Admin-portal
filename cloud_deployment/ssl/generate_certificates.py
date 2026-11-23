"""
Generate SSL/TLS Certificates and Certificate Details Report
Assignment 19: Public Website with Restricted Admin Portal
Deliverable 5: HTTPS Certificate Details
"""

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ipaddress

SSL_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SSL_DIR, "portal_cloudtech_cert.pem")
KEY_FILE = os.path.join(SSL_DIR, "portal_cloudtech_key.pem")
REPORT_FILE = os.path.join(SSL_DIR, "CERTIFICATE_DETAILS.txt")

def generate_self_signed_cert():
    print("[*] Generating 2048-bit RSA Private Key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Subject & Issuer Information
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Karnataka"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Bengaluru"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "National Institute of Cloud Technology"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Cloud Computing Lab - Assignment 19"),
        x509.NameAttribute(NameOID.COMMON_NAME, "portal.cloudtech.edu"),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)
    valid_until = now + datetime.timedelta(days=365)

    # Subject Alternative Names (SAN)
    san_list = [
        x509.DNSName("portal.cloudtech.edu"),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv4Address("203.0.113.195"))
    ]

    print("[*] Building X.509 v3 Certificate with SAN & TLS Server Authentication...")
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(valid_until)
        .add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Write Private Key
    with open(KEY_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write Certificate
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Generate Detailed Technical Report (Deliverable 5)
    report_content = f"""================================================================================
HTTPS CERTIFICATE SPECIFICATION & TECHNICAL DETAILS
Assignment 19: Public Website with Restricted Admin Portal
Students: Vikas & Vijit
================================================================================

1. CERTIFICATE OVERVIEW:
   Common Name (CN): portal.cloudtech.edu
   Organization: National Institute of Cloud Technology (NICTE)
   Organizational Unit: Cloud Computing Lab - Assignment 19
   Country / Locality: IN / Bengaluru, Karnataka
   Certificate Format: X.509 v3 (PEM Encoded)
   Serial Number: {cert.serial_number}

2. CRYPTOGRAPHIC ALGORITHMS:
   Signature Algorithm: SHA-256 with RSA Encryption (sha256WithRSAEncryption)
   Key Pair Type: RSA
   Public Key Length: 2048 bits
   Exponent: 65537 (0x10001)

3. VALIDITY PERIOD:
   Issued On: {now.strftime("%Y-%m-%d %H:%M:%S UTC")}
   Expires On: {valid_until.strftime("%Y-%m-%d %H:%M:%S UTC")}
   Duration: 365 Days (1 Year)

4. SUBJECT ALTERNATIVE NAMES (SAN):
   - DNS: portal.cloudtech.edu
   - DNS: localhost
   - IP Address: 127.0.0.1 (Loopback Dev)
   - IP Address: 203.0.113.195 (Authorized College Admin IP)

5. CIPHER SUITE & TRANSPORT SECURITY (TLS 1.3):
   Supported Protocols: TLSv1.2, TLSv1.3
   Recommended Modern Cipher Suites:
     - TLS_AES_128_GCM_SHA256 (TLS 1.3)
     - TLS_AES_256_GCM_SHA384 (TLS 1.3)
     - ECDHE-RSA-AES128-GCM-SHA256 (TLS 1.2)
     - ECDHE-RSA-AES256-GCM-SHA384 (TLS 1.2)
   HTTP Strict Transport Security (HSTS): Enabled (max-age=31536000; includeSubDomains)

6. SECURITY GROUP / PORT MAPPING:
   - Port 80 (HTTP): Ingress 0.0.0.0/0 -> Redirect 301 to Port 443
   - Port 443 (HTTPS): Ingress 0.0.0.0/0 -> TLS Encrypted Traffic
================================================================================
"""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[+] Certificate written to: {CERT_FILE}")
    print(f"[+] Private Key written to: {KEY_FILE}")
    print(f"[+] Technical Report written to: {REPORT_FILE}")

if __name__ == "__main__":
    generate_self_signed_cert()
