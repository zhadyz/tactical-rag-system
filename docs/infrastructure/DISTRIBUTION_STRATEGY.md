# Distribution Infrastructure Strategy

**CLASSIFICATION**: Production Distribution Infrastructure
**COMPONENT**: Application Distribution (Online/Offline)
**DEPLOYMENT SCENARIOS**: Field/Enterprise/Public

---

## Overview

Tactical RAG Desktop supports multiple distribution strategies to accommodate different deployment scenarios:

1. **Online Distribution** (GitHub Releases + Auto-Update)
2. **Offline Distribution** (Manual installers, USB, air-gapped networks)
3. **Enterprise Distribution** (Internal update servers, managed deployments)

---

## Distribution Matrix

| Scenario | Method | Auto-Update | Internet Required | Use Case |
|----------|--------|-------------|-------------------|----------|
| **Public Release** | GitHub Releases | ✅ Yes | ✅ Yes | Standard users, open-source community |
| **Field Deployment** | USB/Portable | ❌ No | ❌ No | Military, remote locations, air-gapped |
| **Enterprise** | Internal Server | ✅ Yes | ⚠️ LAN Only | Corporate networks, classified environments |
| **Development** | Direct Binary | ❌ No | ❌ No | Development team, testing |

---

## Strategy 1: Online Distribution (GitHub Releases)

**Target Audience**: Public users, developers, organizations with internet access

### Architecture

```
┌─────────────────┐
│  User Device    │
│  (Desktop App)  │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────────────────────┐
│  GitHub Releases                │
│  https://github.com/zhadyz/     │
│    tactical-rag-system/releases │
│                                 │
│  ✅ Free hosting                │
│  ✅ CDN (global distribution)   │
│  ✅ Automatic checksums          │
│  ✅ Version history              │
└─────────────────────────────────┘
```

### Advantages

- **Zero hosting cost** (GitHub Releases is free)
- **Global CDN** (fast downloads worldwide)
- **Automatic changelog** (git tags → release notes)
- **Version history** (all releases preserved)
- **Built-in checksums** (SHA256 automatically generated)

### Setup

**Automated via GitHub Actions** (already configured):

```yaml
# .github/workflows/tauri-build-release.yml
# Creates release automatically on git tag push

# Trigger:
git tag v4.0.1
git push origin v4.0.1

# Result:
# - Builds Windows/macOS/Linux installers
# - Creates GitHub Release (draft)
# - Uploads all installers
# - Generates update manifest (latest.json)
```

### User Installation Flow

1. **Visit GitHub Releases page**:
   ```
   https://github.com/zhadyz/tactical-rag-system/releases/latest
   ```

2. **Download installer for platform**:
   - Windows: `Tactical-RAG-Setup-4.0.1.exe`
   - macOS (Intel): `Tactical-RAG-4.0.1-x64.dmg`
   - macOS (Apple Silicon): `Tactical-RAG-4.0.1-arm64.dmg`
   - Linux (AppImage): `tactical-rag_4.0.1_amd64.AppImage`
   - Linux (Debian): `tactical-rag_4.0.1_amd64.deb`
   - Linux (RPM): `tactical-rag-4.0.1-1.x86_64.rpm`

3. **Install**:
   - Windows: Run `.exe`, follow wizard
   - macOS: Open `.dmg`, drag to Applications
   - Linux: `chmod +x *.AppImage && ./tactical-rag*.AppImage`

4. **Auto-update** (subsequent updates):
   - App checks GitHub Releases every 6 hours
   - Downloads and installs updates automatically
   - User can manually check: Settings → Check for Updates

### Bandwidth Considerations

**GitHub Releases Limits:**
- File size: 2 GB max per file (Tauri apps typically 300-500 MB)
- Release size: No stated limit
- Bandwidth: No stated limit (subject to abuse prevention)

**Expected Usage:**
- 1000 downloads/month × 400 MB = 400 GB/month
- Well within GitHub's acceptable use

---

## Strategy 2: Offline Distribution (USB/Portable Media)

**Target Audience**: Field deployments, air-gapped networks, low-bandwidth environments

### Architecture

```
┌──────────────────────┐
│  Build Server        │
│  (CI/CD or Local)    │
└──────────┬───────────┘
           │
           │ Copy to USB
           ▼
┌──────────────────────┐
│  USB Drive           │
│  ├── installers/     │
│  ├── README.txt      │
│  ├── VERIFY.txt      │
│  └── checksums.txt   │
└──────────┬───────────┘
           │
           │ Physical transfer
           ▼
┌──────────────────────┐
│  Air-Gapped Network  │
│  (No Internet)       │
└──────────────────────┘
```

### USB Distribution Kit Structure

```
TacticalRAG-v4.0.1-Offline/
├── README.txt                    (Installation instructions)
├── VERIFY.txt                    (Signature verification guide)
├── checksums.txt                 (SHA256 hashes)
├── LICENSE.md                    (Open-source license)
├── CHANGELOG.md                  (Version history)
│
├── installers/
│   ├── windows/
│   │   ├── Tactical-RAG-Setup-4.0.1.exe
│   │   └── Tactical-RAG-Setup-4.0.1.exe.sig
│   │
│   ├── macos/
│   │   ├── Tactical-RAG-4.0.1-x64.dmg
│   │   ├── Tactical-RAG-4.0.1-x64.dmg.sig
│   │   ├── Tactical-RAG-4.0.1-arm64.dmg
│   │   └── Tactical-RAG-4.0.1-arm64.dmg.sig
│   │
│   └── linux/
│       ├── tactical-rag_4.0.1_amd64.AppImage
│       ├── tactical-rag_4.0.1_amd64.AppImage.sig
│       ├── tactical-rag_4.0.1_amd64.deb
│       └── tactical-rag-4.0.1-1.x86_64.rpm
│
├── verification/
│   ├── tauri-public-key.txt      (Auto-update signature verification)
│   ├── gpg-public-key.asc        (Manual GPG verification)
│   └── verify-installer.sh       (Automated verification script)
│
└── documentation/
    ├── INSTALLATION_GUIDE.md
    ├── TROUBLESHOOTING.md
    └── SECURITY.md
```

### Creation Script

Create `scripts/create-offline-kit.sh`:

```bash
#!/bin/bash
# Create offline distribution kit for USB deployment

VERSION="$1"
if [ -z "$VERSION" ]; then
  echo "Usage: ./create-offline-kit.sh <version>"
  echo "Example: ./create-offline-kit.sh 4.0.1"
  exit 1
fi

OUTPUT_DIR="TacticalRAG-v${VERSION}-Offline"
INSTALLERS_DIR="tactical-rag-desktop/src-tauri/target/release/bundle"

echo "Creating offline distribution kit: $OUTPUT_DIR"

# Create directory structure
mkdir -p "$OUTPUT_DIR"/{installers/{windows,macos,linux},verification,documentation}

# Copy installers
echo "Copying Windows installers..."
cp "$INSTALLERS_DIR/nsis"/*.exe "$OUTPUT_DIR/installers/windows/" 2>/dev/null || true
cp "$INSTALLERS_DIR/nsis"/*.exe.sig "$OUTPUT_DIR/installers/windows/" 2>/dev/null || true

echo "Copying macOS installers..."
cp "$INSTALLERS_DIR/dmg"/*.dmg "$OUTPUT_DIR/installers/macos/" 2>/dev/null || true
cp "$INSTALLERS_DIR/dmg"/*.dmg.sig "$OUTPUT_DIR/installers/macos/" 2>/dev/null || true

echo "Copying Linux installers..."
cp "$INSTALLERS_DIR/appimage"/*.AppImage "$OUTPUT_DIR/installers/linux/" 2>/dev/null || true
cp "$INSTALLERS_DIR/appimage"/*.AppImage.sig "$OUTPUT_DIR/installers/linux/" 2>/dev/null || true
cp "$INSTALLERS_DIR/deb"/*.deb "$OUTPUT_DIR/installers/linux/" 2>/dev/null || true
cp "$INSTALLERS_DIR/rpm"/*.rpm "$OUTPUT_DIR/installers/linux/" 2>/dev/null || true

# Generate checksums
echo "Generating checksums..."
cd "$OUTPUT_DIR/installers"
find . -type f -not -name "*.sig" -exec sha256sum {} \; > ../checksums.txt
cd ../..

# Copy documentation
echo "Copying documentation..."
cp README.md "$OUTPUT_DIR/README.txt"
cp LICENSE.md "$OUTPUT_DIR/LICENSE.md" 2>/dev/null || echo "MIT License" > "$OUTPUT_DIR/LICENSE.md"
cp docs/CHANGELOG.md "$OUTPUT_DIR/CHANGELOG.md" 2>/dev/null || git log --oneline -20 > "$OUTPUT_DIR/CHANGELOG.md"

# Copy verification keys
echo "Copying verification keys..."
grep "pubkey" tactical-rag-desktop/src-tauri/tauri.conf.json | sed 's/.*: "\(.*\)".*/\1/' > "$OUTPUT_DIR/verification/tauri-public-key.txt"

# Create installation guide
cat > "$OUTPUT_DIR/documentation/INSTALLATION_GUIDE.md" << 'EOF'
# Tactical RAG Desktop - Offline Installation Guide

## Windows Installation

1. **Verify installer integrity**:
   ```cmd
   certutil -hashfile installers\windows\Tactical-RAG-Setup-4.0.1.exe SHA256
   ```
   Compare output with checksum in `checksums.txt`

2. **Run installer**:
   - Double-click `Tactical-RAG-Setup-4.0.1.exe`
   - If SmartScreen warning appears:
     - Click "More info" → "Run anyway"
     - (Expected for unsigned builds in Phase 1)
   - Follow installation wizard
   - Default location: `C:\Program Files\Tactical RAG`

3. **Launch application**:
   - Start Menu → "Tactical RAG"
   - Or desktop shortcut (if created during installation)

## macOS Installation

1. **Verify installer integrity**:
   ```bash
   shasum -a 256 installers/macos/Tactical-RAG-4.0.1-x64.dmg
   ```
   Compare output with checksum in `checksums.txt`

2. **Mount disk image**:
   - Double-click `Tactical-RAG-4.0.1-x64.dmg` (Intel) or `Tactical-RAG-4.0.1-arm64.dmg` (Apple Silicon)
   - Drag "Tactical RAG" to Applications folder

3. **Launch application**:
   - Open Applications folder
   - Right-click "Tactical RAG" → "Open"
   - Click "Open" in Gatekeeper dialog
   - (Required for unsigned apps in Phase 1)

## Linux Installation

### AppImage (Recommended - Universal)

1. **Verify integrity**:
   ```bash
   sha256sum installers/linux/tactical-rag_4.0.1_amd64.AppImage
   ```

2. **Make executable and run**:
   ```bash
   chmod +x installers/linux/tactical-rag_4.0.1_amd64.AppImage
   ./installers/linux/tactical-rag_4.0.1_amd64.AppImage
   ```

### Debian/Ubuntu (.deb)

```bash
sudo dpkg -i installers/linux/tactical-rag_4.0.1_amd64.deb
sudo apt-get install -f  # Install dependencies if needed
tactical-rag
```

### Fedora/RHEL (.rpm)

```bash
sudo rpm -i installers/linux/tactical-rag-4.0.1-1.x86_64.rpm
tactical-rag
```

## Verification (Optional but Recommended)

### Verify Tauri Signatures

**Requires**: Tauri CLI (`npm install -g @tauri-apps/cli`)

```bash
# Get public key
PUBLIC_KEY=$(cat verification/tauri-public-key.txt)

# Verify Windows installer
tauri signer verify installers/windows/Tactical-RAG-Setup-4.0.1.exe --public-key "$PUBLIC_KEY"

# Verify macOS DMG
tauri signer verify installers/macos/Tactical-RAG-4.0.1-x64.dmg --public-key "$PUBLIC_KEY"

# Verify Linux AppImage
tauri signer verify installers/linux/tactical-rag_4.0.1_amd64.AppImage --public-key "$PUBLIC_KEY"
```

## Troubleshooting

See `documentation/TROUBLESHOOTING.md` for common issues.
EOF

# Create verification script
cat > "$OUTPUT_DIR/verification/verify-installer.sh" << 'EOF'
#!/bin/bash
# Automated installer verification script

echo "Tactical RAG Installer Verification"
echo "===================================="
echo ""

CHECKSUMS_FILE="../checksums.txt"

if [ ! -f "$CHECKSUMS_FILE" ]; then
  echo "❌ ERROR: checksums.txt not found"
  exit 1
fi

cd ../installers

echo "Verifying checksums..."
while IFS= read -r line; do
  expected_hash=$(echo "$line" | awk '{print $1}')
  file_path=$(echo "$line" | awk '{print $2}')

  if [ -f "$file_path" ]; then
    actual_hash=$(sha256sum "$file_path" | awk '{print $1}')

    if [ "$expected_hash" == "$actual_hash" ]; then
      echo "✅ $file_path"
    else
      echo "❌ $file_path (CHECKSUM MISMATCH)"
      exit 1
    fi
  fi
done < "$CHECKSUMS_FILE"

echo ""
echo "✅ All installers verified successfully"
EOF

chmod +x "$OUTPUT_DIR/verification/verify-installer.sh"

# Create archive
echo "Creating archive..."
tar -czf "${OUTPUT_DIR}.tar.gz" "$OUTPUT_DIR"
zip -r "${OUTPUT_DIR}.zip" "$OUTPUT_DIR" -q

echo ""
echo "=================================================="
echo "✅ Offline distribution kit created!"
echo "=================================================="
echo ""
echo "Directory: $OUTPUT_DIR/"
echo "Archive (Linux/macOS): ${OUTPUT_DIR}.tar.gz"
echo "Archive (Windows): ${OUTPUT_DIR}.zip"
echo ""
echo "Distribution methods:"
echo "1. USB drive (copy entire directory)"
echo "2. Internal file server (upload archive)"
echo "3. Physical media (burn to DVD)"
```

### Usage

```bash
# After building release
./scripts/create-offline-kit.sh 4.0.1

# Output:
# TacticalRAG-v4.0.1-Offline/
# TacticalRAG-v4.0.1-Offline.tar.gz (Linux/macOS)
# TacticalRAG-v4.0.1-Offline.zip (Windows)

# Transfer to USB
cp -r TacticalRAG-v4.0.1-Offline /media/usb/

# Or burn to DVD
growisofs -Z /dev/dvd -R -J TacticalRAG-v4.0.1-Offline/
```

---

## Strategy 3: Enterprise Distribution (Internal Update Server)

**Target Audience**: Enterprises, classified networks, LAN-only deployments

### Architecture

```
┌─────────────────┐
│  User Device    │
│  (Desktop App)  │
└────────┬────────┘
         │
         │ HTTPS (LAN)
         ▼
┌─────────────────────────────────┐
│  Internal Update Server         │
│  https://updates.company.local  │
│                                 │
│  ├── latest.json                │
│  ├── Tactical-RAG-Setup.exe     │
│  ├── Tactical-RAG.dmg           │
│  └── tactical-rag.AppImage      │
└─────────────────────────────────┘
         │
         │ Periodic sync
         ▼
┌─────────────────────────────────┐
│  GitHub Releases (Optional)     │
│  (If internet access allowed)   │
└─────────────────────────────────┘
```

### Setup

**Option 1: Static File Server (Nginx)**

```nginx
# /etc/nginx/sites-available/tactical-rag-updates

server {
    listen 443 ssl http2;
    server_name updates.tactical-rag.local;

    ssl_certificate /etc/ssl/certs/tactical-rag.crt;
    ssl_certificate_key /etc/ssl/private/tactical-rag.key;

    root /var/www/tactical-rag-updates;
    autoindex on;  # Directory listing

    # CORS headers (required for Tauri updater)
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type";

    location / {
        try_files $uri $uri/ =404;
    }

    # Update manifest
    location = /latest.json {
        add_header Content-Type application/json;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Logging
    access_log /var/log/nginx/tactical-rag-updates-access.log;
    error_log /var/log/nginx/tactical-rag-updates-error.log;
}
```

**Directory Structure**:

```
/var/www/tactical-rag-updates/
├── latest.json
├── v4.0.0/
│   ├── Tactical-RAG-Setup-4.0.0.exe
│   ├── Tactical-RAG-4.0.0.dmg
│   └── tactical-rag_4.0.0_amd64.AppImage
└── v4.0.1/
    ├── Tactical-RAG-Setup-4.0.1.exe
    ├── Tactical-RAG-4.0.1.dmg
    └── tactical-rag_4.0.1_amd64.AppImage
```

**Update Manifest** (`latest.json`):

```json
{
  "version": "4.0.1",
  "notes": "Security patch and performance improvements",
  "pub_date": "2025-10-21T16:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6...",
      "url": "https://updates.tactical-rag.local/v4.0.1/Tactical-RAG-Setup-4.0.1.exe"
    },
    "darwin-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6...",
      "url": "https://updates.tactical-rag.local/v4.0.1/Tactical-RAG-4.0.1-x64.dmg"
    },
    "darwin-aarch64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6...",
      "url": "https://updates.tactical-rag.local/v4.0.1/Tactical-RAG-4.0.1-arm64.dmg"
    },
    "linux-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6...",
      "url": "https://updates.tactical-rag.local/v4.0.1/tactical-rag_4.0.1_amd64.AppImage"
    }
  }
}
```

**Tauri Configuration**:

```json
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://updates.tactical-rag.local/latest.json",
        "https://updates.tactical-rag.backup.local/latest.json",
        "https://github.com/zhadyz/tactical-rag-system/releases/latest/download/latest.json"
      ],
      "pubkey": "YOUR_PUBLIC_KEY"
    }
  }
}
```

**Sync Script** (GitHub Releases → Internal Server):

```bash
#!/bin/bash
# Sync latest release from GitHub to internal server

GITHUB_REPO="zhadyz/tactical-rag-system"
DEST_DIR="/var/www/tactical-rag-updates"

# Get latest release
LATEST_RELEASE=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest")
VERSION=$(echo "$LATEST_RELEASE" | jq -r .tag_name | sed 's/v//')

echo "Syncing version $VERSION..."

# Create version directory
mkdir -p "$DEST_DIR/v$VERSION"

# Download installers
echo "$LATEST_RELEASE" | jq -r '.assets[] | select(.name | test("\\.(exe|dmg|AppImage)$")) | .browser_download_url' | while read -r url; do
  filename=$(basename "$url")
  echo "Downloading $filename..."
  curl -L -o "$DEST_DIR/v$VERSION/$filename" "$url"
done

# Download update manifest
curl -L -o "$DEST_DIR/latest.json" "https://github.com/$GITHUB_REPO/releases/latest/download/latest.json"

# Update URLs in manifest to point to internal server
sed -i "s|https://github.com/$GITHUB_REPO/releases/download/v$VERSION|https://updates.tactical-rag.local/v$VERSION|g" "$DEST_DIR/latest.json"

echo "✅ Sync complete: v$VERSION"
```

---

## Distribution Decision Matrix

### When to Use Each Strategy

**GitHub Releases (Online)**:
- ✅ Public releases
- ✅ Open-source distribution
- ✅ Users with reliable internet
- ✅ Automatic updates desired
- ❌ Air-gapped networks
- ❌ Bandwidth-constrained environments

**USB/Offline Distribution**:
- ✅ Field deployments (military, remote)
- ✅ Air-gapped networks
- ✅ Low/no internet connectivity
- ✅ Secure environments (no external downloads)
- ❌ Frequent updates required
- ❌ Large user base (manual distribution doesn't scale)

**Internal Update Server (Enterprise)**:
- ✅ Corporate/enterprise deployments
- ✅ Classified networks (LAN access, no internet)
- ✅ Controlled update rollout
- ✅ Compliance requirements (no external downloads)
- ❌ Small deployments (infrastructure overhead)
- ❌ Public releases (unnecessary complexity)

---

## Security Considerations

### Signature Verification (All Strategies)

**Critical**: All installers must be signed with Tauri private key

```bash
# Sign installer (CI/CD or local build)
tauri signer sign Tactical-RAG-Setup-4.0.1.exe \
  --private-key ~/.tauri/tactical-rag.key \
  --password "$TAURI_KEY_PASSWORD"

# Output: Tactical-RAG-Setup-4.0.1.exe.sig

# Verify signature
tauri signer verify Tactical-RAG-Setup-4.0.1.exe \
  --public-key "YOUR_PUBLIC_KEY"
```

**Users cannot disable signature verification** (Tauri enforced).

### Checksum Verification (Offline Distribution)

```bash
# Generate checksums
sha256sum installers/**/* > checksums.txt

# User verification
sha256sum -c checksums.txt
```

### HTTPS Enforcement (Online/Enterprise)

- GitHub Releases: HTTPS enforced (GitHub infrastructure)
- Internal Server: Configure SSL/TLS certificates
- No HTTP fallback (Tauri updater requires HTTPS)

---

## Bandwidth Optimization

### Differential Updates

**Tauri supports differential updates**:
- Only changed files downloaded (not entire installer)
- Reduces bandwidth usage by ~70-90%
- Automatic (no configuration required)

**Example**:
- Full installer: 400 MB
- Differential update (4.0.0 → 4.0.1): 40 MB (90% reduction)

### CDN Caching (GitHub Releases)

- GitHub Releases uses CDN (CloudFlare)
- Cached globally (low latency worldwide)
- No action required (automatic)

---

## Monitoring & Analytics

### Track Download Statistics

**GitHub Releases**:
```bash
# Get download counts
curl -s "https://api.github.com/repos/zhadyz/tactical-rag-system/releases/latest" | jq '.assets[] | {name: .name, downloads: .download_count}'

# Output:
# {
#   "name": "Tactical-RAG-Setup-4.0.1.exe",
#   "downloads": 1234
# }
```

**Internal Server** (Nginx):
```bash
# Parse access logs
cat /var/log/nginx/tactical-rag-updates-access.log | \
  grep ".exe\|.dmg\|.AppImage" | \
  awk '{print $7}' | \
  sort | uniq -c | sort -rn

# Output:
#  456 /v4.0.1/Tactical-RAG-Setup-4.0.1.exe
#  123 /v4.0.1/Tactical-RAG-4.0.1.dmg
#   89 /v4.0.1/tactical-rag_4.0.1_amd64.AppImage
```

---

## Testing Distribution Channels

### Test Checklist

- [ ] **Online (GitHub Releases)**:
  - [ ] Create test release (v4.0.0-test)
  - [ ] Download installer from GitHub
  - [ ] Install on clean VM
  - [ ] Verify auto-update detects new version (v4.0.1-test)
  - [ ] Verify update installs successfully

- [ ] **Offline (USB)**:
  - [ ] Create offline kit with `create-offline-kit.sh`
  - [ ] Copy to USB drive
  - [ ] Test on air-gapped VM (no network)
  - [ ] Verify checksum verification script
  - [ ] Verify signature verification (Tauri CLI)

- [ ] **Enterprise (Internal Server)**:
  - [ ] Setup Nginx with SSL
  - [ ] Upload installers and `latest.json`
  - [ ] Configure Tauri updater endpoint
  - [ ] Test update check from LAN device
  - [ ] Verify CORS headers (browser DevTools)

---

## Production Checklist

Before production release:

- [ ] GitHub Releases configured (automated via GitHub Actions)
- [ ] Offline distribution kit creation script tested
- [ ] Internal update server setup (if enterprise deployment)
- [ ] Signature verification documented and tested
- [ ] Bandwidth usage estimated and acceptable
- [ ] Rollback procedure documented (for failed updates)
- [ ] User documentation updated (installation guides)
- [ ] Support team trained (common installation issues)

---

## References

- [Tauri Updater Configuration](https://tauri.app/v1/guides/distribution/updater/)
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
- [Nginx Configuration Best Practices](https://nginx.org/en/docs/)

---

**Last Updated**: 2025-10-21
**Maintained By**: ZHADYZ DevOps Orchestrator
**Classification**: Production Distribution Infrastructure
