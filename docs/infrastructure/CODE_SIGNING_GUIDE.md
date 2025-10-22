# Code Signing Infrastructure Guide

**CLASSIFICATION**: Production Security Infrastructure
**COMPONENT**: Code Signing & Trust Establishment
**SECURITY LEVEL**: Critical

---

## Overview

Code signing establishes trust with operating systems and users by cryptographically proving that:
1. The application comes from a verified publisher (you)
2. The application has not been tampered with since signing

**Without code signing:**
- Windows SmartScreen shows "Unknown Publisher" warnings
- macOS Gatekeeper blocks application launch (requires right-click > Open)
- Linux users may distrust unsigned binaries

**With code signing:**
- Windows shows verified publisher name
- macOS applications launch without warnings
- Users can verify binary authenticity

---

## Platform-Specific Requirements

### Windows Code Signing

**Certificate Types:**

1. **Standard Code Signing Certificate** ($200-400/year):
   - Validates organization identity
   - Shows publisher name in SmartScreen
   - **Limitation**: SmartScreen reputation starts at zero
   - **Recommendation**: For internal/field deployments

2. **Extended Validation (EV) Code Signing Certificate** ($300-600/year):
   - Requires hardware security module (HSM) or USB token
   - **Immediate SmartScreen reputation** (no "unknown publisher" warnings)
   - Stronger identity verification (business registration, D&B number)
   - **Recommendation**: For public releases

**Certificate Providers:**
- DigiCert (most trusted, highest cost)
- Sectigo (good balance of trust and cost)
- SSL.com (budget-friendly)
- Entrust
- GlobalSign

**Requirements:**
- Registered business entity (LLC, Corporation, etc.)
- Dun & Bradstreet (D&B) number (for EV certificates)
- Business validation documents (Articles of Incorporation, Tax ID)
- Verified phone number and address

**Acquisition Timeline:**
- Standard: 1-3 business days
- EV: 3-7 business days (business verification required)

---

### macOS Code Signing

**Certificate Types:**

1. **Apple Developer ID Application Certificate** ($99/year):
   - Part of Apple Developer Program membership
   - Required for Gatekeeper approval
   - Enables notarization (malware scan by Apple)

**Requirements:**
- Apple Developer Program membership ($99/year)
- Apple ID
- Xcode Command Line Tools (for signing)

**Acquisition Timeline:**
- Instant (upon Apple Developer Program enrollment)

**Notarization Process:**
- After signing, submit app to Apple for malware scan
- Apple returns notarization ticket (typically 5-15 minutes)
- Staple ticket to app bundle
- macOS Gatekeeper allows installation without warnings

---

### Linux Code Signing

**Status**: No centralized code signing infrastructure

**Trust Mechanisms:**
1. **GPG signatures** (manual verification by users)
2. **Repository signing** (if distributing via APT/RPM repos)
3. **Checksums** (SHA256 hashes published on website)

**Recommendation**: Publish SHA256 checksums and GPG signatures for verification

---

## Phase 1 Approach (Development/MVP)

**Skip code signing initially:**
- Users will see warnings (expected and documented)
- Reduces initial infrastructure complexity
- Allows rapid iteration without certificate costs

**User Communication:**
```markdown
### Security Notice (Phase 1)

Tactical RAG Desktop is currently unsigned during alpha/beta testing.

**Windows Users:**
- You will see "Windows protected your PC" (SmartScreen warning)
- Click "More info" → "Run anyway"
- This is expected for unsigned applications

**macOS Users:**
- Right-click the app → Select "Open"
- Click "Open" in the dialog
- Alternatively: System Preferences > Security & Privacy > "Open Anyway"

**Why is it unsigned?**
- Code signing certificates cost $300-600/year
- Requires business registration and verification
- We will add code signing in production release (Phase 5)

**How to verify integrity:**
- Download from official GitHub Releases only
- Verify SHA256 checksum (see SECURITY.md)
- Auto-update signatures are enforced (Tauri updater)
```

---

## Phase 5 Approach (Production)

### Windows Code Signing Setup

**Step 1: Acquire Certificate**

1. **Choose provider** (DigiCert recommended for EV):
   ```
   DigiCert EV Code Signing Certificate:
   - Cost: ~$474/year
   - Includes: Hardware token (YubiKey-like device)
   - Validation: 3-7 business days
   - Immediate SmartScreen reputation
   ```

2. **Complete business verification**:
   - Submit business registration documents
   - Verify phone number and address
   - Obtain Dun & Bradstreet (D&B) number (free)
   - Wait for validation callback from provider

3. **Receive hardware token**:
   - USB token shipped to verified business address
   - Install token drivers (SafeNet Authentication Client)
   - Set PIN for token access

**Step 2: Configure Local Signing**

```powershell
# Install certificate (imports from hardware token)
certutil -csp "eToken Base Cryptographic Provider" -importpfx tactical-rag-cert.pfx

# Verify certificate installed
Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert

# Get certificate thumbprint
$cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
$thumbprint = $cert.Thumbprint
Write-Output "Thumbprint: $thumbprint"
```

**Step 3: Configure Tauri**

Update `tauri.conf.json`:

```json
{
  "tauri": {
    "bundle": {
      "windows": {
        "certificateThumbprint": "YOUR_CERTIFICATE_THUMBPRINT",
        "digestAlgorithm": "sha256",
        "timestampUrl": "http://timestamp.digicert.com"
      }
    }
  }
}
```

**Step 4: Sign Locally**

```bash
# Build and sign
cd tactical-rag-desktop
npm run tauri build

# Tauri automatically signs using configured certificate
# Verify signature
signtool verify /pa /v "src-tauri\target\release\bundle\nsis\Tactical-RAG-Setup.exe"
```

**Step 5: Configure GitHub Actions**

```yaml
# .github/workflows/tauri-build-release.yml

- name: Import code signing certificate (Windows)
  if: matrix.platform.os == 'windows-latest'
  env:
    CERTIFICATE_BASE64: ${{ secrets.WINDOWS_CERTIFICATE }}
    CERTIFICATE_PASSWORD: ${{ secrets.WINDOWS_CERTIFICATE_PASSWORD }}
  shell: pwsh
  run: |
    # Decode certificate
    $certBytes = [Convert]::FromBase64String($env:CERTIFICATE_BASE64)
    $certPath = "$env:TEMP\cert.pfx"
    [IO.File]::WriteAllBytes($certPath, $certBytes)

    # Import certificate
    Import-PfxCertificate `
      -FilePath $certPath `
      -CertStoreLocation Cert:\CurrentUser\My `
      -Password (ConvertTo-SecureString -String $env:CERTIFICATE_PASSWORD -AsPlainText -Force)

    # Clean up
    Remove-Item $certPath

- name: Build Tauri application (Windows)
  if: matrix.platform.os == 'windows-latest'
  uses: tauri-apps/tauri-action@v0
  env:
    TAURI_PRIVATE_KEY: ${{ secrets.TAURI_PRIVATE_KEY }}
    TAURI_KEY_PASSWORD: ${{ secrets.TAURI_KEY_PASSWORD }}
    # Certificate is already imported, Tauri will detect it
```

**GitHub Secrets Configuration:**

```bash
# Export certificate to base64
$cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert | Select-Object -First 1
$certPath = "$env:TEMP\tactical-rag-cert.pfx"
$password = Read-Host -AsSecureString "Enter certificate password"

Export-PfxCertificate `
  -Cert $cert `
  -FilePath $certPath `
  -Password $password

# Base64 encode
$certBytes = [IO.File]::ReadAllBytes($certPath)
$certBase64 = [Convert]::ToBase64String($certBytes)

# Copy to clipboard
Set-Clipboard $certBase64

# Add to GitHub Secrets:
# WINDOWS_CERTIFICATE: <paste from clipboard>
# WINDOWS_CERTIFICATE_PASSWORD: <password>
```

---

### macOS Code Signing Setup

**Step 1: Enroll in Apple Developer Program**

1. Visit https://developer.apple.com/programs/
2. Enroll ($99/year)
3. Complete identity verification (1-2 business days)

**Step 2: Create Developer ID Certificate**

1. Open Xcode → Preferences → Accounts
2. Add Apple ID
3. Manage Certificates → Create "Developer ID Application"
4. Certificate auto-downloads to Keychain

**Step 3: Configure Tauri**

```json
{
  "tauri": {
    "bundle": {
      "macOS": {
        "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)"
      }
    }
  }
}
```

**Step 4: Notarization Script**

Create `scripts/notarize-macos.sh`:

```bash
#!/bin/bash
# Notarize macOS application

APP_PATH="$1"  # Path to .dmg or .app
BUNDLE_ID="com.tactical-rag.desktop"
APPLE_ID="your-apple-id@example.com"
TEAM_ID="YOUR_TEAM_ID"

# Create app-specific password at appleid.apple.com
# Store in keychain
xcrun notarytool store-credentials "tactical-rag-notarization" \
  --apple-id "$APPLE_ID" \
  --team-id "$TEAM_ID" \
  --password "APP_SPECIFIC_PASSWORD"

# Submit for notarization
xcrun notarytool submit "$APP_PATH" \
  --keychain-profile "tactical-rag-notarization" \
  --wait

# Staple notarization ticket
xcrun stapler staple "$APP_PATH"

# Verify
spctl -a -vv "$APP_PATH"
```

**Step 5: Configure GitHub Actions**

```yaml
- name: Import Apple certificates (macOS)
  if: matrix.platform.os == 'macos-latest'
  env:
    APPLE_CERTIFICATE: ${{ secrets.APPLE_CERTIFICATE }}
    APPLE_CERTIFICATE_PASSWORD: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}
  run: |
    # Import certificate to keychain
    echo "$APPLE_CERTIFICATE" | base64 --decode > certificate.p12
    security create-keychain -p actions build.keychain
    security default-keychain -s build.keychain
    security unlock-keychain -p actions build.keychain
    security import certificate.p12 \
      -k build.keychain \
      -P "$APPLE_CERTIFICATE_PASSWORD" \
      -T /usr/bin/codesign
    security set-key-partition-list \
      -S apple-tool:,apple: \
      -s -k actions build.keychain

- name: Build Tauri application (macOS)
  if: matrix.platform.os == 'macos-latest'
  uses: tauri-apps/tauri-action@v0
  env:
    APPLE_SIGNING_IDENTITY: ${{ secrets.APPLE_SIGNING_IDENTITY }}

- name: Notarize application (macOS)
  if: matrix.platform.os == 'macos-latest'
  env:
    APPLE_ID: ${{ secrets.APPLE_ID }}
    APPLE_PASSWORD: ${{ secrets.APPLE_PASSWORD }}
    APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
  run: |
    DMG_PATH=$(find target/release/bundle/dmg -name "*.dmg" | head -1)
    xcrun notarytool submit "$DMG_PATH" \
      --apple-id "$APPLE_ID" \
      --password "$APPLE_PASSWORD" \
      --team-id "$APPLE_TEAM_ID" \
      --wait
    xcrun stapler staple "$DMG_PATH"
```

**GitHub Secrets Configuration:**

```bash
# Export Developer ID certificate
security find-identity -v -p codesigning

# Export certificate
security export -k login.keychain \
  -t identities \
  -f pkcs12 \
  -P "YOUR_EXPORT_PASSWORD" \
  -o tactical-rag-cert.p12

# Base64 encode
base64 -i tactical-rag-cert.p12 | pbcopy

# Add to GitHub Secrets:
# APPLE_CERTIFICATE: <paste from clipboard>
# APPLE_CERTIFICATE_PASSWORD: <export password>
# APPLE_SIGNING_IDENTITY: "Developer ID Application: Your Name (TEAM_ID)"
# APPLE_ID: your-apple-id@example.com
# APPLE_PASSWORD: <app-specific password>
# APPLE_TEAM_ID: YOUR_TEAM_ID
```

---

## Security Best Practices

### Certificate Storage

**DO:**
- Store private keys in hardware tokens (Windows EV certificates)
- Use GitHub Secrets for CI/CD (encrypted at rest)
- Enable MFA on certificate provider accounts
- Rotate certificates before expiration
- Audit certificate usage logs

**DON'T:**
- Commit certificates to version control
- Share certificates via email or Slack
- Store certificates in cloud storage (Dropbox, Google Drive)
- Use same certificate for multiple projects
- Export private keys unnecessarily

### Revocation Planning

**If certificate is compromised:**

1. **Immediately revoke certificate**:
   - Contact certificate provider
   - Request emergency revocation
   - Typically effective within 24 hours

2. **Notify users**:
   - Post security advisory on GitHub
   - Email notification list
   - Update website with alert

3. **Acquire new certificate**:
   - Different provider (if provider was compromised)
   - New keypair (don't reuse)

4. **Rebuild and re-sign all releases**:
   - Replace binaries in GitHub Releases
   - Update checksums and signatures

---

## Cost Analysis

### Phase 1 (No Code Signing)
- **Cost**: $0
- **User Experience**: Warnings on all platforms
- **Risk**: Users may distrust application
- **Recommendation**: Acceptable for alpha/beta

### Phase 5 (Full Code Signing)

**Windows:**
- EV Certificate: $474/year
- Hardware token: Included
- **Total**: ~$500/year

**macOS:**
- Apple Developer Program: $99/year
- **Total**: ~$100/year

**Linux:**
- GPG key: Free
- **Total**: $0

**Total Annual Cost**: ~$600/year

**Return on Investment:**
- Improved user trust
- Reduced support requests (fewer "how to bypass warnings" questions)
- Professional appearance
- Required for enterprise deployments

---

## Testing Code Signing

### Windows

```powershell
# Verify signature
signtool verify /pa /v "Tactical-RAG-Setup.exe"

# Check certificate details
Get-AuthenticodeSignature "Tactical-RAG-Setup.exe" | Format-List

# Test SmartScreen (requires uploading to web and downloading)
# SmartScreen only triggers on downloaded files, not local builds
```

### macOS

```bash
# Verify signature
codesign -vvv --deep --strict "Tactical RAG.app"

# Check notarization
spctl -a -vv "Tactical RAG.app"

# Verify Gatekeeper approval
spctl --assess --type execute "Tactical RAG.app"
```

---

## Troubleshooting

### Windows: "Certificate not found"

**Cause**: Certificate not imported or thumbprint incorrect

**Solution**:
```powershell
# List installed code signing certificates
Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert

# Update thumbprint in tauri.conf.json
```

### macOS: "No identity found"

**Cause**: Developer ID certificate not in keychain

**Solution**:
```bash
# List signing identities
security find-identity -v -p codesigning

# Import certificate
security import Developer_ID.p12 -k ~/Library/Keychains/login.keychain-db
```

### macOS: "Notarization failed"

**Cause**: App-specific password incorrect or expired

**Solution**:
```bash
# Create new app-specific password
# Visit appleid.apple.com > Security > App-Specific Passwords

# Update keychain profile
xcrun notarytool store-credentials "tactical-rag-notarization" \
  --apple-id "your-apple-id@example.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "NEW_APP_SPECIFIC_PASSWORD"
```

---

## Migration Path

**Phase 1 → Phase 5 Transition:**

1. **Acquire certificates** (start process 2-4 weeks before production release)
2. **Configure signing** (update tauri.conf.json, GitHub Actions)
3. **Test signed builds** (verify on clean VMs)
4. **Release signed version** (create new GitHub Release)
5. **Update documentation** (remove "unsigned" warnings)
6. **Monitor SmartScreen reputation** (Windows EV cert only)

**No action required from existing users:**
- Auto-update mechanism will deliver signed version
- Users on v4.0.0-unsigned will update to v4.0.1-signed seamlessly

---

## References

- [Windows Code Signing Best Practices](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Tauri Bundle Configuration](https://tauri.app/v1/api/config/#bundleconfig)
- [DigiCert EV Code Signing](https://www.digicert.com/signing/code-signing-certificates)

---

**Last Updated**: 2025-10-21
**Maintained By**: ZHADYZ DevOps Orchestrator
**Classification**: Production Security Infrastructure
