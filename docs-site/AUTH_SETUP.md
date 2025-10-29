# OAuth Authentication Setup Guide

This guide will help you set up OAuth authentication for the Apollo documentation site.

## Prerequisites

- Node.js 18.17.0 or higher
- npm 9.0.0 or higher
- GitHub account (for GitHub OAuth)
- Google Cloud account (for Google OAuth)

## 1. Environment Variables Setup

Copy the example environment file and fill in your OAuth credentials:

```bash
cp .env.local.example .env.local
```

## 2. Generate NextAuth Secret

Generate a secure secret for JWT encryption:

```bash
# On Linux/Mac
openssl rand -base64 32

# On Windows (PowerShell)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

Add the generated secret to your `.env.local` file:

```env
NEXTAUTH_SECRET=your-generated-secret-here
```

## 3. GitHub OAuth Setup

### Step 1: Create OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "OAuth Apps" → "New OAuth App"
3. Fill in the details:
   - **Application name**: Apollo Docs (or your preferred name)
   - **Homepage URL**: `http://localhost:3000` (development) or your production URL
   - **Authorization callback URL**: `http://localhost:3000/api/auth/callback/github`
4. Click "Register application"

### Step 2: Get Credentials

1. Note your **Client ID**
2. Click "Generate a new client secret"
3. Copy the **Client Secret** immediately (it won't be shown again)

### Step 3: Update .env.local

```env
GITHUB_ID=your-github-client-id
GITHUB_SECRET=your-github-client-secret
```

## 4. Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

### Step 2: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure consent screen if prompted:
   - User Type: External
   - Fill in required fields
   - Add authorized domains
4. Select "Web application"
5. Fill in the details:
   - **Name**: Apollo Docs OAuth
   - **Authorized JavaScript origins**: `http://localhost:3000`
   - **Authorized redirect URIs**: `http://localhost:3000/api/auth/callback/google`
6. Click "Create"

### Step 3: Get Credentials

1. Copy the **Client ID**
2. Copy the **Client Secret**

### Step 4: Update .env.local

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 5. Complete .env.local File

Your final `.env.local` file should look like this:

```env
# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-generated-secret

# GitHub OAuth
GITHUB_ID=your-github-client-id
GITHUB_SECRET=your-github-client-secret

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 6. Running the Application

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Visit `http://localhost:3000` and click the "Login" button in the navigation bar to test OAuth authentication.

## 7. Production Deployment

For production deployment:

1. Update the OAuth callback URLs in GitHub and Google:
   - GitHub: `https://apollo.onyxlab.ai/api/auth/callback/github`
   - Google: `https://apollo.onyxlab.ai/api/auth/callback/google`

2. Update `.env.local` or your hosting platform's environment variables:
   ```env
   NEXTAUTH_URL=https://apollo.onyxlab.ai
   ```

## Troubleshooting

### Common Issues

**1. "Configuration" Error**
- Check that all environment variables are set correctly
- Ensure NEXTAUTH_SECRET is generated and added

**2. "OAuthCallback" Error**
- Verify callback URLs match exactly in OAuth app settings
- Check that the OAuth app is not in development mode (for Google)

**3. "OAuthAccountNotLinked" Error**
- User's email is already registered with a different provider
- User needs to sign in with their original provider first

**4. Session Not Persisting**
- Clear browser cookies
- Check that NEXTAUTH_SECRET is consistent across deployments
- Verify SessionProvider is wrapping the app in `_app.tsx`

### Support

For additional help:
- Email: contact@onyxlab.ai
- GitHub Issues: [tactical-rag-system/issues](https://github.com/zhadyz/tactical-rag-system/issues)

## Security Notes

- **Never commit `.env.local`** to version control
- Keep OAuth secrets secure and rotate them periodically
- Use strong, randomly generated NEXTAUTH_SECRET
- Enable 2FA on your OAuth provider accounts
- Regularly review authorized OAuth applications
