# Environment Variables Management Proposal for Ekko

## Executive Summary

This proposal outlines a streamlined approach to managing environment variables across local development, GitHub Actions CI/CD, and Google Cloud Run deployment for the Ekko application, minimizing manual steps while maintaining security best practices.

## Current Challenges

1. Multiple credential files in the codebase (`ekko_prototype/creds/`)
2. Hardcoded values (e.g., ngrok URL, authentication tokens)
3. Manual environment variable management across different environments
4. Risk of exposing sensitive data in version control

## Proposed Solution Architecture

### 1. Three-Tier Environment Strategy

```
Local Development → GitHub Actions → Google Cloud Run
     (.env)       → (GitHub Secrets) → (Secret Manager)
```

### 2. Implementation Plan

#### Phase 1: Local Development Setup

**File Structure:**
```
ekko/
├── .env.example        # Template with all required variables (committed)
├── .env               # Actual values (gitignored)
├── .env.test          # Test environment values (gitignored)
└── config/
    └── settings.py    # Centralized configuration loader
```

**Configuration Loader (`config/settings.py`):**
```python
import os
from pathlib import Path
from typing import Optional
import json

# Only load dotenv in development
if os.getenv('ENVIRONMENT', 'development') == 'development':
    from dotenv import load_dotenv
    load_dotenv()

class Config:
    """Centralized configuration management"""

    # Environment detection
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    IS_CI = os.getenv('CI', 'false').lower() == 'true'

    # API Keys and Secrets
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    PODCASTINDEX_API_KEY = os.getenv('PODCASTINDEX_API_KEY')
    PODCASTINDEX_API_SECRET = os.getenv('PODCASTINDEX_API_SECRET')
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

    # Application Settings
    NGROK_URL = os.getenv('NGROK_URL', 'https://default.ngrok.io')
    AUTH_TOKEN = os.getenv('AUTH_TOKEN', 'default-dev-token')

    # Google Cloud Settings
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GCP_REGION = os.getenv('GCP_REGION', 'us-central1')

    @classmethod
    def validate(cls) -> bool:
        """Validate required environment variables"""
        required = ['OPENAI_API_KEY', 'PODCASTINDEX_API_KEY']
        missing = [var for var in required if not getattr(cls, var)]

        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True

config = Config()
```

**`.env.example`:**
```bash
# Environment
ENVIRONMENT=development

# API Keys (obtain from respective services)
OPENAI_API_KEY=sk-...
PODCASTINDEX_API_KEY=your-key-here
PODCASTINDEX_API_SECRET=your-secret-here
YOUTUBE_API_KEY=your-youtube-key

# Application Settings
NGROK_URL=https://your-ngrok-url.ngrok.io
AUTH_TOKEN=your-secure-token

# Google Cloud
GCP_PROJECT_ID=ekko-468919
GCP_REGION=europe-west1
```

#### Phase 2: GitHub Actions Setup

**Step 1: Create GitHub Secrets**
```bash
# Using GitHub CLI (one-time setup)
gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY"
gh secret set PODCASTINDEX_API_KEY --body "$PODCASTINDEX_API_KEY"
gh secret set PODCASTINDEX_API_SECRET --body "$PODCASTINDEX_API_SECRET"
gh secret set YOUTUBE_API_KEY --body "$YOUTUBE_API_KEY"
gh secret set GCP_SA_KEY --body "$(cat service-account-key.json)"
gh secret set GCP_PROJECT_ID --body "your-project-id"
```

**Step 2: Update CI/CD Workflow:**
```yaml
# .github/workflows/cicd.yml
env:
  ENVIRONMENT: ci
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}

jobs:
  test:
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      PODCASTINDEX_API_KEY: ${{ secrets.PODCASTINDEX_API_KEY }}
      PODCASTINDEX_API_SECRET: ${{ secrets.PODCASTINDEX_API_SECRET }}
    steps:
      - name: Run tests
        run: pytest tests/

  deploy:
    steps:
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ekko \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/ekko:latest \
            --region us-central1 \
            --set-secrets="OPENAI_API_KEY=openai-api-key:latest" \  # pragma: allowlist secret
            --set-secrets="PODCASTINDEX_API_KEY=podcastindex-api-key:latest" \  # pragma: allowlist secret
            --set-env-vars="ENVIRONMENT=production"
```

#### Phase 3: Google Cloud Setup

**Step 1: Create Secrets in Secret Manager (one-time setup)**
```bash
# Script: scripts/setup-gcp-secrets.sh
#!/bin/bash

# Load local .env file
source .env

# Create secrets in Google Secret Manager
echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key \
    --data-file=- --replication-policy="automatic"

echo -n "$PODCASTINDEX_API_KEY" | gcloud secrets create podcastindex-api-key \
    --data-file=- --replication-policy="automatic"

echo -n "$PODCASTINDEX_API_SECRET" | gcloud secrets create podcastindex-api-secret \
    --data-file=- --replication-policy="automatic"

echo -n "$YOUTUBE_API_KEY" | gcloud secrets create youtube-api-key \
    --data-file=- --replication-policy="automatic"

# Grant Cloud Run service account access to secrets
SERVICE_ACCOUNT="ekko@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

for secret in openai-api-key podcastindex-api-key podcastindex-api-secret youtube-api-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor"
done
```

**Step 2: Cloud Run Deployment Configuration:**
```yaml
# cloud-run-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ekko
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/ekko:latest
        env:
        - name: ENVIRONMENT
          value: production
        - name: GCP_PROJECT_ID
          value: PROJECT_ID
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-api-key
              key: latest
        - name: PODCASTINDEX_API_KEY
          valueFrom:
            secretKeyRef:
              name: podcastindex-api-key
              key: latest
```

### 3. Migration Steps

#### Step 1: Initial Setup (15 minutes)
```bash
# 1. Create .env file from template
cp .env.example .env
# Edit .env with your values

# 2. Test local configuration
python -c "from config.settings import config; config.validate()"

# 3. Run application locally
streamlit run ekko_prototype/landing.py
```

#### Step 2: GitHub Secrets Setup (10 minutes)
```bash
# 1. Set all secrets using GitHub CLI
./scripts/setup-github-secrets.sh

# 2. Verify secrets are set
gh secret list
```

#### Step 3: Google Cloud Setup (20 minutes)
```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# 2. Create secrets in Secret Manager
./scripts/setup-gcp-secrets.sh

# 3. Deploy to Cloud Run
gcloud run deploy ekko \
    --source . \
    --region us-central1 \
    --platform managed
```

### 4. Benefits of This Approach

1. **Security**:
   - No secrets in code repository
   - Secrets encrypted at rest in Secret Manager
   - Least privilege access with service accounts

2. **Simplicity**:
   - Single source of truth for each environment
   - Automated secret injection
   - No manual copying of credentials

3. **Consistency**:
   - Same configuration interface across all environments
   - Environment-specific overrides when needed
   - Clear separation of concerns

4. **Minimal Manual Steps**:
   - One-time setup scripts for each environment
   - Automated deployment with proper secret handling
   - No manual environment variable management after setup

### 5. Optional: Advanced Setup with dotenv-vault

For teams wanting additional security and versioning:

```bash
# Install dotenv-vault
npm install -g dotenv-vault

# Login and push .env
dotenv-vault login
dotenv-vault push

# Build encrypted vault
dotenv-vault build

# In production, only need DOTENV_KEY
DOTENV_KEY="vault_key_here" python app.py
```

### 6. Rollback Plan

If issues arise, we can quickly rollback:

1. **Local**: Restore previous .env file
2. **GitHub**: Update secrets through UI or CLI
3. **Cloud Run**: Deploy previous container version
   ```bash
   gcloud run services update-traffic ekko --to-revisions=ekko-00001-abc=100
   ```

### 7. Security Best Practices

1. **Never commit**:
   - .env files
   - Service account keys
   - Any file containing secrets

2. **Use least privilege**:
   - Create service accounts with minimal permissions
   - Rotate secrets regularly
   - Audit access logs

3. **Environment separation**:
   - Different secrets for dev/staging/production
   - Separate Google Cloud projects for each environment
   - Network isolation where possible

### 8. Monitoring and Alerts

Set up monitoring for secret access:

```bash
# Create alert for unusual secret access
gcloud logging metrics create secret_access_metric \
    --log-filter='resource.type="secretmanager.googleapis.com/Secret"' \
    --value-extractor='EXTRACT(jsonPayload.request.name)'
```

## Implementation Timeline

- **Week 1**: Local development setup and testing
- **Week 2**: GitHub Actions integration
- **Week 3**: Google Cloud Secret Manager setup
- **Week 4**: Full deployment and documentation

## Conclusion

This approach provides a secure, automated, and maintainable solution for environment variable management across all deployment environments with minimal manual intervention required after initial setup.
