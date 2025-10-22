# Tauri Auto-Update Infrastructure Setup

**CLASSIFICATION**: Production Infrastructure
**COMPONENT**: Auto-Update Mechanism
**SECURITY LEVEL**: Critical (Private Key Management)

---

## Overview

Tactical RAG Desktop uses Tauri's built-in auto-update mechanism with cryptographic signature verification. This ensures users automatically receive updates while preventing tampering or supply-chain attacks.

**Key Features:**
- Automatic update checks every 6 hours
- Signature verification (mandatory, cannot be disabled)
- Differential updates (only download changed files)
- Rollback capability (if update fails)
- User-controlled installation timing

---

## Architecture

```
┌─────────────────┐
│  Desktop App    │
│  (Tauri)        │
└────────┬────────┘
         │
         │ 1. Check for updates
         ▼
┌─────────────────────────────────┐
│  Update Server                  │
│  (GitHub Releases or Internal)  │
│                                 │
│  /latest.json                   │
│  /tactical-rag-4.0.1.exe.sig    │
│  /tactical-rag-4.0.1.exe        │
└─────────────────────────────────┘
         │
         │ 2. Download manifest + signature
         ▼
┌─────────────────┐
│  Verification   │
│  (Public Key)   │
└────────┬────────┘
         │
         │ 3. Verify signature
         ▼
┌─────────────────┐
│  Install Update │
│  (if valid)     │
└─────────────────┘
```

---

## Phase 1: Generate Signing Keypair

**CRITICAL**: This step is performed ONCE during initial infrastructure setup. The private key must be securely stored and NEVER committed to version control.

### Prerequisites

```bash
# Install Tauri CLI globally
npm install -g @tauri-apps/cli@next

# Verify installation
tauri --version
```

### Generate Keypair

```bash
# Generate signing keypair (interactive)
tauri signer generate -w ~/.tauri/tactical-rag.key

# Output example:
# Your keypair was generated successfully
# Private: C:\Users\{USER}\.tauri\tactical-rag.key (Keep this private!)
# Public: dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDJFNTU...
#
# Password: (randomly generated, save securely)
```

### Secure Private Key Storage

**Options:**

1. **Local Secure Storage** (Development):
   ```bash
   # Windows: Store in user profile (encrypted filesystem)
   C:\Users\{USER}\.tauri\tactical-rag.key

   # macOS: Store in keychain
   security add-generic-password \
     -a tactical-rag-updater \
     -s tauri-private-key \
     -w "$(cat ~/.tauri/tactical-rag.key)"

   # Linux: Store with restricted permissions
   chmod 600 ~/.tauri/tactical-rag.key
   ```

2. **GitHub Secrets** (CI/CD):
   ```bash
   # Read private key
   cat ~/.tauri/tactical-rag.key | base64

   # Add to GitHub repository secrets:
   # Settings > Secrets and variables > Actions > New repository secret
   # Name: TAURI_PRIVATE_KEY
   # Value: <base64-encoded private key>

   # Also add password:
   # Name: TAURI_KEY_PASSWORD
   # Value: <password from generation step>
   ```

3. **Production Secrets Vault** (Enterprise):
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault

**NEVER:**
- Commit private key to git
- Share private key via email/Slack
- Store private key in cloud storage (Dropbox, Google Drive, etc.)
- Use same keypair for multiple projects

---

## Phase 2: Configure Tauri Application

### Update `tauri.conf.json`

Add updater configuration to your Tauri config:

```json
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://github.com/zhadyz/tactical-rag-system/releases/latest/download/latest.json"
      ],
      "pubkey": "YOUR_PUBLIC_KEY_FROM_GENERATION_STEP",
      "windows": {
        "installMode": "passive"
      }
    },
    "bundle": {
      "windows": {
        "webviewInstallMode": {
          "type": "embedBootstrapper"
        }
      }
    }
  }
}
```

**Configuration Explained:**

- `active: true` - Enable auto-update mechanism
- `endpoints` - URLs to check for updates (GitHub Releases or custom server)
- `pubkey` - Public key for signature verification (from keypair generation)
- `windows.installMode: "passive"` - Silent installation (no UAC prompt per update)

### Alternative: Internal Update Server

For field deployments without internet access:

```json
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://updates.tactical-rag.local/latest.json",
        "http://192.168.1.100:8080/updates/latest.json"
      ],
      "pubkey": "YOUR_PUBLIC_KEY_FROM_GENERATION_STEP"
    }
  }
}
```

**Multiple endpoints**: Tauri tries each in order until one succeeds.

---

## Phase 3: Implement Frontend Update Logic

### React Hook: `useAutoUpdate.ts`

Create a custom hook to manage update checks:

```typescript
// src/hooks/useAutoUpdate.ts
import { useState, useEffect } from 'react';
import { checkUpdate, installUpdate } from '@tauri-apps/api/updater';
import { relaunch } from '@tauri-apps/api/process';
import { ask } from '@tauri-apps/api/dialog';

interface UpdateManifest {
  version: string;
  date: string;
  body: string;
}

export function useAutoUpdate() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [manifest, setManifest] = useState<UpdateManifest | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  const checkForUpdates = async (silent: boolean = true) => {
    try {
      setIsChecking(true);
      const { shouldUpdate, manifest } = await checkUpdate();

      if (shouldUpdate) {
        setUpdateAvailable(true);
        setManifest(manifest);

        // Auto-prompt user (non-silent mode)
        if (!silent) {
          await promptInstall(manifest);
        }
      } else {
        if (!silent) {
          await ask('You are running the latest version.', {
            title: 'No Updates Available',
            type: 'info'
          });
        }
      }
    } catch (error) {
      console.error('Update check failed:', error);
      if (!silent) {
        await ask(`Failed to check for updates: ${error}`, {
          title: 'Update Error',
          type: 'error'
        });
      }
    } finally {
      setIsChecking(false);
    }
  };

  const promptInstall = async (manifest: UpdateManifest) => {
    const install = await ask(
      `Version ${manifest.version} is available.\n\n${manifest.body}\n\nInstall now? The application will restart.`,
      {
        title: 'Update Available',
        type: 'info'
      }
    );

    if (install) {
      await installUpdateNow();
    }
  };

  const installUpdateNow = async () => {
    try {
      setIsInstalling(true);
      await installUpdate();
      await relaunch();
    } catch (error) {
      console.error('Update installation failed:', error);
      await ask(`Failed to install update: ${error}`, {
        title: 'Installation Error',
        type: 'error'
      });
    } finally {
      setIsInstalling(false);
    }
  };

  useEffect(() => {
    // Check on startup (silent)
    checkForUpdates(true);

    // Check every 6 hours
    const interval = setInterval(() => {
      checkForUpdates(true);
    }, 6 * 60 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    updateAvailable,
    manifest,
    isChecking,
    isInstalling,
    checkForUpdates,
    installUpdateNow
  };
}
```

### Settings UI Component

```typescript
// src/components/UpdateSettings.tsx
import { useAutoUpdate } from '@/hooks/useAutoUpdate';

export function UpdateSettings() {
  const {
    updateAvailable,
    manifest,
    isChecking,
    isInstalling,
    checkForUpdates,
    installUpdateNow
  } = useAutoUpdate();

  return (
    <div className="update-settings">
      <h3>Software Updates</h3>

      <div className="update-status">
        <p>Current version: 4.0.0</p>
        {updateAvailable && (
          <p className="update-badge">
            Update available: {manifest?.version}
          </p>
        )}
      </div>

      <button
        onClick={() => checkForUpdates(false)}
        disabled={isChecking || isInstalling}
      >
        {isChecking ? 'Checking...' : 'Check for Updates'}
      </button>

      {updateAvailable && (
        <button
          onClick={installUpdateNow}
          disabled={isInstalling}
          className="install-button"
        >
          {isInstalling ? 'Installing...' : 'Install Update'}
        </button>
      )}
    </div>
  );
}
```

---

## Phase 4: Update Manifest Generation (CI/CD)

The GitHub Actions workflow automatically generates the update manifest. Here's what it looks like:

### `latest.json` Structure

```json
{
  "version": "4.0.1",
  "notes": "Critical security patch and performance improvements",
  "pub_date": "2025-10-21T16:30:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJpIHNlY3JldCBrZXkKUlVUNUJ...",
      "url": "https://github.com/zhadyz/tactical-rag-system/releases/download/v4.0.1/Tactical-RAG-Setup-4.0.1.exe"
    },
    "darwin-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJpIHNlY3JldCBrZXkKUlVUNUJ...",
      "url": "https://github.com/zhadyz/tactical-rag-system/releases/download/v4.0.1/Tactical-RAG-4.0.1.dmg"
    },
    "darwin-aarch64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJpIHNlY3JldCBrZXkKUlVUNUJ...",
      "url": "https://github.com/zhadyz/tactical-rag-system/releases/download/v4.0.1/Tactical-RAG-4.0.1-aarch64.dmg"
    },
    "linux-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJpIHNlY3JldCBrZXkKUlVUNUJ...",
      "url": "https://github.com/zhadyz/tactical-rag-system/releases/download/v4.0.1/tactical-rag_4.0.1_amd64.AppImage"
    }
  }
}
```

**Manifest is automatically generated by `tauri-action` GitHub Action.**

---

## Phase 5: Testing Update Flow

### Manual Test Procedure

1. **Build version 4.0.0**:
   ```bash
   cd tactical-rag-desktop
   npm run tauri build
   # Install resulting executable
   ```

2. **Increment version to 4.0.1**:
   ```json
   // tauri.conf.json
   {
     "package": {
       "version": "4.0.1"
     }
   }
   ```

3. **Create GitHub release**:
   ```bash
   git tag v4.0.1
   git push origin v4.0.1
   # GitHub Actions builds and creates release
   ```

4. **Test update in running app**:
   - Open v4.0.0 application
   - Navigate to Settings > Updates
   - Click "Check for Updates"
   - Verify update to v4.0.1 is detected
   - Click "Install Update"
   - Verify app restarts with v4.0.1

### Automated Test Script

```bash
#!/bin/bash
# scripts/test-auto-update.sh

echo "Testing auto-update flow..."

# 1. Verify current version
CURRENT_VERSION=$(grep '"version"' tactical-rag-desktop/src-tauri/tauri.conf.json | head -1 | sed 's/.*: "\(.*\)".*/\1/')
echo "Current version: $CURRENT_VERSION"

# 2. Check GitHub releases
LATEST_RELEASE=$(curl -s https://api.github.com/repos/zhadyz/tactical-rag-system/releases/latest | grep '"tag_name"' | sed 's/.*"v\(.*\)".*/\1/')
echo "Latest release: $LATEST_RELEASE"

# 3. Compare versions
if [ "$CURRENT_VERSION" == "$LATEST_RELEASE" ]; then
  echo "✅ App is up to date"
else
  echo "⚠️ Update available: $CURRENT_VERSION -> $LATEST_RELEASE"
fi

# 4. Verify update manifest
MANIFEST_URL="https://github.com/zhadyz/tactical-rag-system/releases/latest/download/latest.json"
curl -s "$MANIFEST_URL" | jq .

echo "Auto-update test complete."
```

---

## Security Considerations

### Signature Verification

- **Enforced by Tauri**: Cannot be disabled
- **Algorithm**: Ed25519 (modern, secure)
- **Process**:
  1. Download update manifest (`latest.json`)
  2. Download installer binary
  3. Verify signature using public key
  4. **Only** install if signature is valid

### Attack Scenarios (Mitigated)

1. **Man-in-the-Middle**:
   - Mitigated: HTTPS + signature verification
   - Attacker cannot forge signature without private key

2. **Compromised Update Server**:
   - Mitigated: Signature verification
   - Even if server is compromised, cannot serve unsigned updates

3. **Stolen Private Key**:
   - **Not mitigated**: Requires key rotation
   - Store private key with highest security level
   - Consider hardware security module (HSM) for production

### Best Practices

- **Rotate signing keys** annually (regenerate keypair)
- **Audit access** to GitHub Secrets
- **Monitor** update server logs for anomalies
- **Test** signature verification in CI/CD
- **Backup** private key in encrypted offline storage

---

## Troubleshooting

### Update Check Fails

**Symptoms**: App says "Failed to check for updates"

**Causes**:
1. No internet connection
2. GitHub Releases not accessible
3. Manifest URL incorrect
4. CORS issues (custom server)

**Solutions**:
```typescript
// Enable debug logging
import { checkUpdate } from '@tauri-apps/api/updater';

try {
  const result = await checkUpdate();
  console.log('Update check result:', result);
} catch (error) {
  console.error('Update check error:', error);
  // error.message will contain details
}
```

### Signature Verification Fails

**Symptoms**: Update downloads but fails to install

**Causes**:
1. Public key mismatch (wrong key in tauri.conf.json)
2. Private key changed (keypair regenerated)
3. Manual release (not signed by CI/CD)

**Solutions**:
```bash
# Verify public key matches
cat ~/.tauri/tactical-rag.key.pub

# Compare with tauri.conf.json
grep pubkey tactical-rag-desktop/src-tauri/tauri.conf.json

# Manually verify signature
tauri signer verify Tactical-RAG-Setup-4.0.1.exe \
  --public-key "YOUR_PUBLIC_KEY"
```

### Update Installs But Fails to Launch

**Causes**:
1. Corrupt download
2. Incompatible version (breaking changes)
3. Missing dependencies

**Solutions**:
- Implement rollback mechanism
- Test updates on clean VMs before release
- Include dependency checks in installer

---

## Rollback Procedure

If an update causes issues:

1. **Automatic Rollback** (Tauri built-in):
   - If app fails to launch after update, Tauri reverts to previous version
   - Triggered after 3 consecutive launch failures

2. **Manual Rollback**:
   ```bash
   # Windows: Reinstall previous version
   C:\ProgramData\Tactical RAG\backups\4.0.0\Tactical-RAG-Setup-4.0.0.exe

   # macOS: Time Machine restore
   # Linux: Reinstall previous .deb/.rpm
   ```

3. **Emergency Rollback (GitHub)**:
   ```bash
   # Delete problematic release
   gh release delete v4.0.1

   # Re-tag previous version as latest
   git tag -d v4.0.1
   git tag v4.0.1 v4.0.0
   git push --force origin v4.0.1
   ```

---

## Production Checklist

Before enabling auto-updates in production:

- [ ] Signing keypair generated and securely stored
- [ ] Public key added to `tauri.conf.json`
- [ ] Private key added to GitHub Secrets
- [ ] GitHub Actions workflow tested
- [ ] Update manifest validated (`latest.json` structure)
- [ ] Frontend update UI implemented
- [ ] Update flow tested (v4.0.0 → v4.0.1)
- [ ] Signature verification tested
- [ ] Rollback procedure documented
- [ ] Emergency contact list created (who to notify if update fails)

---

## References

- [Tauri Updater Guide](https://tauri.app/v1/guides/distribution/updater/)
- [tauri-action Documentation](https://github.com/tauri-apps/tauri-action)
- [Ed25519 Signature Scheme](https://ed25519.cr.yp.to/)

---

**Last Updated**: 2025-10-21
**Maintained By**: ZHADYZ DevOps Orchestrator
**Classification**: Production Infrastructure
