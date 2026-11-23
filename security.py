import ipaddress
import time
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Default Authorized CIDRs for Admin Portal (Assignment 19: College IP 203.XX.XX.XX/32)
# We include 203.0.113.195/32 (College Dedicated Static IP), 203.0.113.0/24 (College Campus Subnet),
# and 127.0.0.1/32, ::1 for local development loopback.
DEFAULT_ALLOWED_ADMIN_CIDRS = [
    "203.0.113.195/32",  # College Static Public IP (as per assignment requirement 203.XX.XX.XX/32)
    "203.0.113.0/24",    # College Campus Subnet
    "127.0.0.1/32",      # Localhost IPv4 loopback
    "::1/128"            # Localhost IPv6 loopback
]

# Preset IP Scenarios for Interactive Demonstration
DEMO_IP_PRESETS = [
    {
        "ip": "203.0.113.195",
        "label": "College Campus Network (203.0.113.195)",
        "network_type": "Authorized Subnet",
        "expected": "ALLOWED",
        "description": "Designated College Administration IP (203.XX.XX.XX/32)"
    },
    {
        "ip": "127.0.0.1",
        "label": "Localhost Developer (127.0.0.1)",
        "network_type": "Development Loopback",
        "expected": "ALLOWED",
        "description": "Host VM internal access"
    },
    {
        "ip": "198.51.100.45",
        "label": "External Public Internet (198.51.100.45)",
        "network_type": "Untrusted Public WAN",
        "expected": "BLOCKED (403)",
        "description": "Simulated external intruder or off-campus user"
    },
    {
        "ip": "49.37.112.89",
        "label": "Untrusted Mobile Hotspot (49.37.112.89)",
        "network_type": "Cellular ISP",
        "expected": "BLOCKED (403)",
        "description": "Simulated off-campus mobile connection"
    }
]

def get_ip_tag(ip_str):
    """Categorize an IP address for reporting and UI badges."""
    try:
        ip_obj = ipaddress.ip_address(ip_str.strip())
        if ip_obj.is_loopback:
            return "Localhost (Loopback)"
        if ip_str.startswith("203.0.113."):
            return "College Campus Network (Authorized)"
        if ip_obj.is_private:
            return "Private VPC Subnet"
        return "Public Internet (External/Untrusted)"
    except Exception:
        return "Unknown Network"

def is_ip_in_cidr(ip_str, cidr_str):
    """Check if an IP string belongs to a CIDR block."""
    try:
        # Strip potential port if passed
        clean_ip = ip_str.split(':')[0].strip()
        ip_obj = ipaddress.ip_address(clean_ip)
        network_obj = ipaddress.ip_network(cidr_str.strip(), strict=False)
        return ip_obj in network_obj
    except Exception:
        return False

def is_ip_allowed_for_admin(client_ip, allowed_cidrs=None):
    """
    Validate whether the client IP is authorized to access the restricted admin portal.
    Rule: Public Website is 0.0.0.0/0, but Admin is strictly College IP (203.XX.XX.XX/32).
    """
    if allowed_cidrs is None:
        allowed_cidrs = DEFAULT_ALLOWED_ADMIN_CIDRS
    
    clean_ip = client_ip.split(':')[0].strip()
    for cidr in allowed_cidrs:
        if is_ip_in_cidr(clean_ip, cidr):
            return True, cidr
    return False, None

def get_effective_client_ip(request, session=None):
    """
    Extract the effective client IP.
    Priority order:
    1. Interactive Session Simulation (allows live testing in browser UI)
    2. Header simulation: 'X-Simulated-IP'
    3. Proxy header: 'X-Forwarded-For'
    4. Direct socket address: request.remote_addr
    """
    if session and "simulated_ip" in session:
        return session["simulated_ip"]
    
    simulated_header = request.headers.get("X-Simulated-IP")
    if simulated_header:
        return simulated_header.strip()
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    return request.remote_addr or "127.0.0.1"
