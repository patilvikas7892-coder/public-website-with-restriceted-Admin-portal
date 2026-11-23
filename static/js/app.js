// IP Simulation and Live Demonstration Helpers

function simulateIP(ip) {
  fetch('/api/simulate-ip', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ip: ip })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload();
    } else {
      alert("Failed to simulate IP: " + (data.error || "Unknown error"));
    }
  })
  .catch(err => {
    console.error("Error setting simulated IP:", err);
    alert("Connection error while setting simulated IP.");
  });
}

function simulateIPAndRedirect(ip, targetUrl) {
  fetch('/api/simulate-ip', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ip: ip })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.href = targetUrl || '/admin/login';
    } else {
      alert("Error: " + data.error);
    }
  })
  .catch(err => {
    console.error("Redirect error:", err);
  });
}

function applyCustomIP() {
  const input = document.getElementById('customIpInput');
  const ip = input ? input.value.trim() : '';
  if (!ip) {
    alert("Please enter a valid IP address (e.g. 203.0.113.195 or 198.51.100.45)");
    return;
  }
  simulateIP(ip);
}

// Modal Handlers
function openUploadModal() {
  const modal = document.getElementById('uploadModal');
  if (modal) modal.style.display = 'flex';
}

function closeUploadModal() {
  const modal = document.getElementById('uploadModal');
  if (modal) modal.style.display = 'none';
}

function openRuleModal() {
  const modal = document.getElementById('ruleModal');
  if (modal) modal.style.display = 'flex';
}

function closeRuleModal() {
  const modal = document.getElementById('ruleModal');
  if (modal) modal.style.display = 'none';
}

function openPresignedModal() {
  const modal = document.getElementById('presignedModal');
  if (modal) modal.style.display = 'flex';
}

function closePresignedModal() {
  const modal = document.getElementById('presignedModal');
  if (modal) modal.style.display = 'none';
}

// Pre-Signed URL Generator
function generatePresigned(fileId, filename) {
  fetch(`/admin/generate-presigned/${fileId}`)
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      const fullUrl = window.location.origin + data.data.url;
      document.getElementById('presignedFilename').innerText = filename;
      document.getElementById('presignedUrlInput').value = fullUrl;
      document.getElementById('testPresignedLink').href = fullUrl;
      openPresignedModal();
    } else {
      alert("Error generating pre-signed URL: " + data.error);
    }
  })
  .catch(err => {
    console.error("Presigned URL error:", err);
    alert("Failed to fetch pre-signed URL.");
  });
}

function copyPresignedUrl() {
  const input = document.getElementById('presignedUrlInput');
  if (input) {
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value);
    alert("Pre-signed URL copied to clipboard! (Valid for 15 minutes)");
  }
}

// Close modals when clicking backdrop
window.onclick = function(event) {
  if (event.target.classList.contains('modal-backdrop')) {
    event.target.style.display = 'none';
  }
};
