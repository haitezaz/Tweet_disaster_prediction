# Firebase Service Account Credentials

Place your Firebase service account JSON file here.

**IMPORTANT**: This directory is git-ignored. Never commit credentials to version control.

## Setup Instructions

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** → **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `firebase-key.json` in this directory

## File Location

```
./secrets/firebase-key.json
```

## Permissions

Ensure the file has restrictive permissions:

```bash
chmod 600 firebase-key.json
```

## Alternative: Environment Variable

You can also specify credentials via environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/secrets/firebase-key.json"
```

## Security Reminders

⚠️ **DO NOT**:
- Commit this file to Git
- Share this file with anyone
- Expose the credentials in logs or error messages
- Use a service account key in production without proper rotation

✅ **DO**:
- Keep credentials secure and private
- Rotate keys periodically (quarterly recommended)
- Use `.env` file to reference the path
- Set proper file permissions (chmod 600)
